from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID
from PIL import Image
import io
import os

from app.database import get_db
from app.models.user import User
from app.models.design import Design, DesignStatus
from app.schemas.design import DesignResponse, DesignListResponse
from app.services.auth_service import get_current_user
from app.services.storage import storage_service
from app.services.job_service import job_service

router = APIRouter()

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".pdf", ".psd"}
MAX_FILE_SIZE = 200 * 1024 * 1024


@router.post("/upload", response_model=dict)
async def upload_design(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    file_bytes = await file.read()
    
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 200MB limit"
        )
    
    design = Design(
        user_id=current_user.id,
        original_filename=file.filename,
        upload_storage_path="",
        status=DesignStatus.UPLOADED
    )
    
    db.add(design)
    await db.flush()
    
    storage_key = f"{design.id}/original{file_ext}"
    storage_path = storage_service.upload_file(
        storage_service.uploads_bucket,
        storage_key,
        file_bytes,
        file.content_type or "application/octet-stream"
    )
    
    design.upload_storage_path = storage_path
    
    try:
        img = Image.open(io.BytesIO(file_bytes))
        design.width_px = img.width
        design.height_px = img.height
        
        if hasattr(img, 'info') and 'dpi' in img.info:
            design.original_dpi = img.info['dpi'][0]
        else:
            design.original_dpi = 72.0
    except Exception:
        design.original_dpi = 72.0
    
    await db.commit()
    await db.refresh(design)
    
    job = await job_service.create_job(design.id, db)
    
    design.status = DesignStatus.PROCESSING
    await db.commit()
    
    from app.workers.pipeline import process_design
    process_design.delay(str(job.id))
    
    return {
        "design_id": str(design.id),
        "job_id": str(job.id),
        "message": "Design uploaded successfully. Processing started."
    }


@router.get("", response_model=List[DesignListResponse])
async def list_designs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Design)
        .where(Design.user_id == current_user.id)
        .order_by(Design.created_at.desc())
    )
    designs = result.scalars().all()
    return designs


@router.get("/{design_id}", response_model=DesignResponse)
async def get_design(
    design_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Design)
        .where(Design.id == design_id, Design.user_id == current_user.id)
        .options(selectinload(Design.layers))
    )
    design = result.scalar_one_or_none()
    
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    return design


@router.delete("/{design_id}")
async def delete_design(
    design_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Design).where(Design.id == design_id, Design.user_id == current_user.id)
    )
    design = result.scalar_one_or_none()
    
    if not design:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Design not found"
        )
    
    try:
        bucket, key = design.upload_storage_path.split("/", 1)
        storage_service.delete_file(bucket, key)
    except Exception:
        pass
    
    await db.delete(design)
    await db.commit()
    
    return {"message": "Design deleted successfully"}
