from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class DesignStatus(str, enum.Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    REVIEW = "review"
    APPROVED = "approved"
    EXPORTED = "exported"


class Design(Base):
    __tablename__ = "designs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    original_filename = Column(String, nullable=False)
    original_dpi = Column(Float, nullable=True)
    width_px = Column(Integer, nullable=True)
    height_px = Column(Integer, nullable=True)
    
    upload_storage_path = Column(String, nullable=False)
    upscaled_storage_path = Column(String, nullable=True)
    
    status = Column(Enum(DesignStatus, values_callable=lambda x: [e.value for e in x]), default=DesignStatus.UPLOADED, nullable=False, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = relationship("User", back_populates="designs")
    jobs = relationship("Job", back_populates="design", cascade="all, delete-orphan")
    layers = relationship("Layer", back_populates="design", cascade="all, delete-orphan")
    colorways = relationship("Colorway", back_populates="design", cascade="all, delete-orphan")
