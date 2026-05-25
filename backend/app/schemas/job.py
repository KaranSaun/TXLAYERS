from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional


class JobResponse(BaseModel):
    id: UUID4
    design_id: UUID4
    status: str
    current_step: int
    total_steps: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobProgressResponse(BaseModel):
    id: UUID4
    design_id: UUID4
    status: str
    current_step: int
    total_steps: int
    progress_percent: float
    error_message: Optional[str]
    
    class Config:
        from_attributes = True
