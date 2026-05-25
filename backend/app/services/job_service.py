from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from uuid import UUID

from app.models.job import Job, JobStatus
from app.models.design import Design, DesignStatus


class JobService:
    @staticmethod
    async def create_job(design_id: UUID, db: AsyncSession) -> Job:
        job = Job(
            design_id=design_id,
            status=JobStatus.QUEUED,
            current_step=0,
            total_steps=6,
            started_at=datetime.utcnow()
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job
    
    @staticmethod
    async def update_job_status(
        job_id: UUID,
        status: JobStatus,
        step: int,
        db: AsyncSession
    ):
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if job:
            job.status = status
            job.current_step = step
            await db.commit()
            await db.refresh(job)
        
        return job
    
    @staticmethod
    async def mark_job_failed(job_id: UUID, error_message: str, db: AsyncSession):
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if job:
            job.status = JobStatus.FAILED
            job.error_message = error_message
            job.completed_at = datetime.utcnow()
            
            design_result = await db.execute(select(Design).where(Design.id == job.design_id))
            design = design_result.scalar_one_or_none()
            if design:
                design.status = DesignStatus.UPLOADED
            
            await db.commit()
            await db.refresh(job)
        
        return job
    
    @staticmethod
    async def mark_job_done(job_id: UUID, db: AsyncSession):
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if job:
            job.status = JobStatus.DONE
            job.current_step = job.total_steps
            job.completed_at = datetime.utcnow()
            
            design_result = await db.execute(select(Design).where(Design.id == job.design_id))
            design = design_result.scalar_one_or_none()
            if design:
                design.status = DesignStatus.REVIEW
            
            await db.commit()
            await db.refresh(job)
        
        return job
    
    @staticmethod
    async def get_job(job_id: UUID, db: AsyncSession) -> Job:
        result = await db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()


job_service = JobService()
