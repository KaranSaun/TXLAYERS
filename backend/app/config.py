from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET_UPLOADS: str = "uploads"
    MINIO_BUCKET_OUTPUTS: str = "outputs"
    MINIO_SECURE: bool = False
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_HOURS: int = 24
    
    DELTA_E_MERGE_THRESHOLD: float = 0.4
    MAX_LAYERS: int = 50
    MAX_COLORWAYS: int = 10
    MODEL_PATH: str = "/app/models_cache"
    CELERY_CONCURRENCY: int = 2
    
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
