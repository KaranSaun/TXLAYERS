from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import io
import zipfile
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.design import Design
from app.models.colorway import Colorway
from app.services.auth_service import get_current_user, get_current_user_optional, AuthService
from app.services.storage import storage_service
import re

def safe_filename(name: str) -> str:
    """Strip non-ASCII characters so they're safe in HTTP Content-Disposition headers."""
    return re.sub(r'[^\x00-\x7F]+', '_', name)

router = APIRouter()


async def get_user_from_token(token: str, db: AsyncSession) -> User:
    """Resolve a user from a JWT token string (for query-param auth)"""
    user_id = AuthService.decode_jwt_token(token)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/preview/{storage_path:path}")
async def serve_design_preview(
    storage_path: str,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Serve original design image for preview in the viewer"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    await get_user_from_token(token, db)
    
    try:
        bucket, key = storage_path.split("/", 1)
        file_bytes = storage_service.download_file(bucket, key)
        ext = key.rsplit('.', 1)[-1].lower()
        media_type = 'image/png' if ext == 'png' else 'image/jpeg'
        return StreamingResponse(io.BytesIO(file_bytes), media_type=media_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/{storage_path:path}")
async def serve_layer_png(
    storage_path: str,
    token: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Serve individual layer PNG mask file for the viewer"""
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    await get_user_from_token(token, db)
    
    try:
        bucket, key = storage_path.split("/", 1)
        file_bytes = storage_service.download_file(bucket, key)
        return StreamingResponse(io.BytesIO(file_bytes), media_type='image/png')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/designs/{design_id}/tif")
async def download_master_tif(
    design_id: UUID,
    token: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    user = current_user
    if user is None and token:
        user = await get_user_from_token(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = await db.execute(
        select(Design).where(Design.id == design_id, Design.user_id == user.id)
    )
    design = result.scalar_one_or_none()
    
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    if not design.upscaled_storage_path:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Design processing not complete"
        )
    
    try:
        bucket, key = design.upscaled_storage_path.split("/", 1)
        master_tif_key = f"{design_id}/master_layers.tif"
        
        file_bytes = storage_service.download_file(
            storage_service.outputs_bucket,
            master_tif_key
        )
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="image/tiff",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename(design.original_filename)}_master.tif"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )


@router.get("/colorways/{colorway_id}/tif")
async def download_colorway_tif(
    colorway_id: UUID,
    token: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    user = current_user
    if user is None and token:
        user = await get_user_from_token(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = await db.execute(
        select(Colorway).join(Design).where(
            Colorway.id == colorway_id,
            Design.user_id == user.id
        )
    )
    colorway = result.scalar_one_or_none()
    
    if not colorway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Colorway not found"
        )
    
    try:
        bucket, key = colorway.tif_storage_path.split("/", 1)
        file_bytes = storage_service.download_file(bucket, key)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="image/tiff",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename(colorway.name)}.tif"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )


@router.get("/colorways/{colorway_id}/preview")
async def download_colorway_preview(
    colorway_id: UUID,
    token: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    user = current_user
    if user is None and token:
        user = await get_user_from_token(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = await db.execute(
        select(Colorway).join(Design).where(
            Colorway.id == colorway_id,
            Design.user_id == user.id
        )
    )
    colorway = result.scalar_one_or_none()
    
    if not colorway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Colorway not found"
        )
    
    try:
        bucket, key = colorway.preview_storage_path.split("/", 1)
        file_bytes = storage_service.download_file(bucket, key)
        
        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f'inline; filename="{safe_filename(colorway.name)}_preview.jpg"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error downloading file: {str(e)}"
        )


@router.get("/designs/{design_id}/bundle")
async def download_bundle(
    design_id: UUID,
    token: Optional[str] = Query(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db)
):
    user = current_user
    if user is None and token:
        user = await get_user_from_token(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    result = await db.execute(
        select(Design).where(Design.id == design_id, Design.user_id == user.id)
    )
    design = result.scalar_one_or_none()
    
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    colorways_result = await db.execute(
        select(Colorway).where(Colorway.design_id == design_id)
    )
    colorways = colorways_result.scalars().all()
    
    if not colorways:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No colorways available for download"
        )
    
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for colorway in colorways:
                bucket, key = colorway.tif_storage_path.split("/", 1)
                file_bytes = storage_service.download_file(bucket, key)
                zip_file.writestr(f"{colorway.name}.tif", file_bytes)
                
                preview_bucket, preview_key = colorway.preview_storage_path.split("/", 1)
                preview_bytes = storage_service.download_file(preview_bucket, preview_key)
                zip_file.writestr(f"{colorway.name}_preview.jpg", preview_bytes)
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="{safe_filename(design.original_filename)}_colorways.zip"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating bundle: {str(e)}"
        )
