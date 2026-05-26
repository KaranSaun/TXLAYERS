from typing import List


class Settings:
    # Database Configuration - hardcoded RDS
    DATABASE_URL: str = "postgresql+asyncpg://admin:Donear%232026%24@donear-auromation26.cn6qkoe6i58s.ap-south-1.rds.amazonaws.com:5432/texlayer_db"
    
    # Redis Configuration - hardcoded
    REDIS_URL: str = "redis://redis:6379/0"
    
    # MinIO Configuration - hardcoded
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_UPLOADS: str = "uploads"
    MINIO_BUCKET_OUTPUTS: str = "outputs"
    MINIO_SECURE: bool = False
    
    # JWT Authentication - hardcoded
    JWT_SECRET_KEY: str = "8f9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    # AI Processing Configuration - hardcoded
    DELTA_E_MERGE_THRESHOLD: float = 0.4
    MAX_LAYERS: int = 50
    MAX_COLORWAYS: int = 10
    MODEL_PATH: str = "/app/models_cache"
    CELERY_CONCURRENCY: int = 2
    
    # CORS Configuration - hardcoded (change this for production)
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost,http://localhost:80"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]


settings = Settings()
