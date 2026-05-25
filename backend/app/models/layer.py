from sqlalchemy import Column, String, Integer, Float, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class LayerRole(str, enum.Enum):
    BACKGROUND = "background"
    MOTIF = "motif"


class Layer(Base):
    __tablename__ = "layers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    design_id = Column(UUID(as_uuid=True), ForeignKey("designs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    layer_index = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(LayerRole, values_callable=lambda x: [e.value for e in x]), nullable=False)
    
    hex_color = Column(String(7), nullable=False)
    lab_l = Column(Float, nullable=False)
    lab_a = Column(Float, nullable=False)
    lab_b = Column(Float, nullable=False)
    
    pixel_count = Column(Integer, nullable=False)
    coverage_percent = Column(Float, nullable=False)
    
    mask_storage_path = Column(String, nullable=False)
    
    design = relationship("Design", back_populates="layers")
