from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.api import api_router
from app.services.storage import storage_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting TexLayerAI backend...")
    
    try:
        storage_service.create_buckets_if_not_exist()
        logger.info("MinIO buckets initialized")
    except Exception as e:
        logger.error(f"Error initializing MinIO: {e}")
    
    yield
    
    logger.info("Shutting down TexLayerAI backend...")


app = FastAPI(
    title="TexLayerAI API",
    description="AI-powered textile design automation system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "TexLayerAI API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
