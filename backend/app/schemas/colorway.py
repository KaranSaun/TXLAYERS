from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Dict


class ColorwayCreate(BaseModel):
    name: str
    color_map: Dict[str, str]


class ColorwayResponse(BaseModel):
    id: UUID4
    design_id: UUID4
    variant_index: int
    name: str
    variant_type: str
    color_map: Dict
    tif_storage_path: str
    preview_storage_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ColorwayListResponse(BaseModel):
    id: UUID4
    variant_index: int
    name: str
    variant_type: str
    preview_storage_path: str
    created_at: datetime
    
    class Config:
        from_attributes = True
