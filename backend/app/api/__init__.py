from fastapi import APIRouter
from app.api import auth, designs, jobs, colorways, download

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(designs.router, prefix="/designs", tags=["designs"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(colorways.router, prefix="/colorways", tags=["colorways"])
api_router.include_router(download.router, prefix="/download", tags=["download"])
