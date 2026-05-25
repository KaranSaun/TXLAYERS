from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    UPSCALING = "upscaling"
    SEGMENTING = "segmenting"
    CLUSTERING = "clustering"
    BUILDING = "building"
    GENERATING = "generating"
    DONE = "done"
    FAILED = "failed"


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    design_id = Column(UUID(as_uuid=True), ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    status = Column(Enum(JobStatus, values_callable=lambda x: [e.value for e in x]), default=JobStatus.QUEUED, nullable=False, index=True)
    current_step = Column(Integer, default=0, nullable=False)
    total_steps = Column(Integer, default=6, nullable=False)
    
    error_message = Column(Text, nullable=True)
    
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    design = relationship("Design", back_populates="jobs")
