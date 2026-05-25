from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ColorwayType(str, enum.Enum):
    MOTIF_ONLY = "motif_only"
    BG_ONLY = "bg_only"
    FULL = "full"
    MANUAL = "manual"


class Colorway(Base):
    __tablename__ = "colorways"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    design_id = Column(UUID(as_uuid=True), ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    variant_index = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    variant_type = Column(Enum(ColorwayType, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    color_map = Column(JSON, nullable=False)
    
    tif_storage_path = Column(String, nullable=False)
    preview_storage_path = Column(String, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    design = relationship("Design", back_populates="colorways")
