from minio import Minio
from minio.error import S3Error
from io import BytesIO
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self):
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.uploads_bucket = settings.MINIO_BUCKET_UPLOADS
        self.outputs_bucket = settings.MINIO_BUCKET_OUTPUTS
    
    def create_buckets_if_not_exist(self):
        try:
            if not self.client.bucket_exists(self.uploads_bucket):
                self.client.make_bucket(self.uploads_bucket)
                logger.info(f"Created bucket: {self.uploads_bucket}")
            
            if not self.client.bucket_exists(self.outputs_bucket):
                self.client.make_bucket(self.outputs_bucket)
                logger.info(f"Created bucket: {self.outputs_bucket}")
        except S3Error as e:
            logger.error(f"Error creating buckets: {e}")
            raise
    
    def upload_file(self, bucket: str, key: str, file_bytes: bytes, content_type: str = "application/octet-stream") -> str:
        try:
            file_stream = BytesIO(file_bytes)
            self.client.put_object(
                bucket,
                key,
                file_stream,
                length=len(file_bytes),
                content_type=content_type
            )
            return f"{bucket}/{key}"
        except S3Error as e:
            logger.error(f"Error uploading file to {bucket}/{key}: {e}")
            raise
    
    def download_file(self, bucket: str, key: str) -> bytes:
        try:
            response = self.client.get_object(bucket, key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            logger.error(f"Error downloading file from {bucket}/{key}: {e}")
            raise
    
    def get_presigned_url(self, bucket: str, key: str, expires: int = 3600) -> str:
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                bucket,
                key,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL for {bucket}/{key}: {e}")
            raise
    
    def delete_file(self, bucket: str, key: str):
        try:
            self.client.remove_object(bucket, key)
            logger.info(f"Deleted file: {bucket}/{key}")
        except S3Error as e:
            logger.error(f"Error deleting file {bucket}/{key}: {e}")
            raise
    
    def file_exists(self, bucket: str, key: str) -> bool:
        try:
            self.client.stat_object(bucket, key)
            return True
        except S3Error:
            return False


storage_service = StorageService()
