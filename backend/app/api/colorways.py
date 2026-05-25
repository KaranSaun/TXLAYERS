from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.design import Design
from app.models.colorway import Colorway
from app.schemas.colorway import ColorwayResponse, ColorwayListResponse, ColorwayCreate
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/designs/{design_id}/colorways", response_model=List[ColorwayListResponse])
async def list_colorways(
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
    
    colorways_result = await db.execute(
        select(Colorway)
        .where(Colorway.design_id == design_id)
        .order_by(Colorway.variant_index)
    )
    colorways = colorways_result.scalars().all()
    
    return colorways


@router.get("/{colorway_id}", response_model=ColorwayResponse)
async def get_colorway(
    colorway_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Colorway).join(Design).where(
            Colorway.id == colorway_id,
            Design.user_id == current_user.id
        )
    )
    colorway = result.scalar_one_or_none()
    
    if not colorway:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Colorway not found"
        )
    
    return colorway


@router.post("/designs/{design_id}/colorways/generate")
async def generate_colorways(
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
    
    from app.workers.pipeline import generate_colorways_task
    task = generate_colorways_task.delay(str(design_id))
    
    return {
        "message": "Colorway generation started",
        "task_id": task.id
    }


@router.post("/designs/{design_id}/colorways/manual", response_model=ColorwayResponse)
async def create_manual_colorway(
    design_id: UUID,
    colorway_data: ColorwayCreate,
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
    
    from app.workers.pipeline import create_manual_colorway_task
    task = create_manual_colorway_task.delay(
        str(design_id),
        colorway_data.name,
        colorway_data.color_map
    )
    
    return {
        "message": "Manual colorway creation started",
        "task_id": task.id
    }
