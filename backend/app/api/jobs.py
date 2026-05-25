from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
import asyncio
import json

from app.database import get_db
from app.models.user import User
from app.models.job import Job
from app.models.design import Design
from app.schemas.job import JobResponse, JobProgressResponse
from app.services.auth_service import get_current_user

router = APIRouter()


@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Job).join(Design).where(
            Job.id == job_id,
            Design.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return job


@router.get("/{job_id}/progress", response_model=JobProgressResponse)
async def get_job_progress(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Job).join(Design).where(
            Job.id == job_id,
            Design.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    progress_percent = (job.current_step / job.total_steps) * 100 if job.total_steps > 0 else 0
    
    return JobProgressResponse(
        id=job.id,
        design_id=job.design_id,
        status=job.status.value,
        current_step=job.current_step,
        total_steps=job.total_steps,
        progress_percent=round(progress_percent, 2),
        error_message=job.error_message
    )


@router.get("/{job_id}/stream")
async def stream_job_status(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Job).join(Design).where(
            Job.id == job_id,
            Design.user_id == current_user.id
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    async def event_generator():
        from app.database import AsyncSessionLocal
        
        while True:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Job).where(Job.id == job_id))
                current_job = result.scalar_one_or_none()
                
                if current_job:
                    progress_percent = (current_job.current_step / current_job.total_steps) * 100
                    
                    data = {
                        "status": current_job.status.value,
                        "current_step": current_job.current_step,
                        "total_steps": current_job.total_steps,
                        "progress_percent": round(progress_percent, 2),
                        "error_message": current_job.error_message
                    }
                    
                    yield f"data: {json.dumps(data)}\n\n"
                    
                    if current_job.status.value in ["done", "failed"]:
                        break
            
            await asyncio.sleep(2)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
