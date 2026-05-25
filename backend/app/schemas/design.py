from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List


class DesignCreate(BaseModel):
    original_filename: str


class LayerInfo(BaseModel):
    id: UUID4
    layer_index: int
    name: str
    role: str
    hex_color: str
    coverage_percent: float
    mask_storage_path: str
    
    class Config:
        from_attributes = True


class DesignResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    original_filename: str
    original_dpi: Optional[float]
    width_px: Optional[int]
    height_px: Optional[int]
    upload_storage_path: str
    upscaled_storage_path: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    layers: List[LayerInfo] = []
    
    class Config:
        from_attributes = True


class DesignListResponse(BaseModel):
    id: UUID4
    original_filename: str
    status: str
    created_at: datetime
    upload_storage_path: str
    
    class Config:
        from_attributes = True
