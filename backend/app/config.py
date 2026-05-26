import os
from typing import List


class Settings:
    # Database - reads from env var set by docker-compose (local postgres or RDS)
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "postgresql+asyncpg://texlayer:texlayer_pass@postgres:5432/texlayer_db")
    
    # Redis
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    
    # MinIO
    MINIO_ENDPOINT: str = os.environ.get("MINIO_ENDPOINT", "minio:9000")
    MINIO_ACCESS_KEY: str = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
    MINIO_BUCKET_UPLOADS: str = os.environ.get("MINIO_BUCKET_UPLOADS", "uploads")
    MINIO_BUCKET_OUTPUTS: str = os.environ.get("MINIO_BUCKET_OUTPUTS", "outputs")
    MINIO_SECURE: bool = False
    
    # JWT Authentication
    JWT_SECRET_KEY: str = os.environ.get("JWT_SECRET_KEY", "8f9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a")
    JWT_ALGORITHM: str = os.environ.get("JWT_ALGORITHM", "HS256")
    JWT_EXPIRY_HOURS: int = int(os.environ.get("JWT_EXPIRY_HOURS", "24"))
    
    # AI Processing Configuration
    DELTA_E_MERGE_THRESHOLD: float = 0.4
    MAX_LAYERS: int = 50
    MAX_COLORWAYS: int = 10
    MODEL_PATH: str = "/app/models_cache"
    CELERY_CONCURRENCY: int = 2
    
    # CORS
    ALLOWED_ORIGINS: str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost")
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
