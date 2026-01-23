"""
Cloud storage service for resume PDFs.
Supports S3, GCS, and Cloudflare R2.
"""
import logging
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for cloud storage operations."""
    
    def __init__(self):
        """Initialize storage service."""
        self.provider = settings.cloud_storage_provider
        self._s3_client = None
    
    async def upload(
        self,
        file_path: Path,
        remote_path: str,
        content_type: str = "application/pdf"
    ) -> str:
        """
        Upload file to cloud storage.
        
        Args:
            file_path: Local file path
            remote_path: Remote path/key
            content_type: MIME type
            
        Returns:
            Public URL of uploaded file
        """
        if self.provider == "local":
            # Return local file path for serving
            return f"/api/resumes/download/{file_path.name}"
        
        elif self.provider == "s3":
            return await self._upload_s3(file_path, remote_path, content_type)
        
        elif self.provider == "gcs":
            return await self._upload_gcs(file_path, remote_path, content_type)
        
        elif self.provider == "r2":
            return await self._upload_r2(file_path, remote_path, content_type)
        
        else:
            raise ValueError(f"Unsupported storage provider: {self.provider}")
    
    async def _upload_s3(
        self,
        file_path: Path,
        remote_path: str,
        content_type: str
    ) -> str:
        """Upload to AWS S3."""
        if not self._s3_client:
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.s3_region
            )
        
        try:
            self._s3_client.upload_file(
                str(file_path),
                settings.s3_bucket,
                remote_path,
                ExtraArgs={'ContentType': content_type}
            )
            
            # Return public URL
            return f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{remote_path}"
        
        except ClientError as e:
            logger.error(f"S3 upload error: {e}")
            raise
    
    async def _upload_gcs(
        self,
        file_path: Path,
        remote_path: str,
        content_type: str
    ) -> str:
        """Upload to Google Cloud Storage."""
        from google.cloud import storage
        
        client = storage.Client()
        bucket = client.bucket(settings.s3_bucket)  # Reuse s3_bucket setting for GCS
        
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(str(file_path), content_type=content_type)
        
        return blob.public_url
    
    async def _upload_r2(
        self,
        file_path: Path,
        remote_path: str,
        content_type: str
    ) -> str:
        """Upload to Cloudflare R2 (S3-compatible)."""
        # R2 uses S3-compatible API
        if not self._s3_client:
            self._s3_client = boto3.client(
                's3',
                endpoint_url=f"https://{settings.s3_region}.r2.cloudflarestorage.com",
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name='auto'
            )
        
        try:
            self._s3_client.upload_file(
                str(file_path),
                settings.s3_bucket,
                remote_path,
                ExtraArgs={'ContentType': content_type}
            )
            
            # R2 public URL format
            return f"https://{settings.s3_bucket}.{settings.s3_region}.r2.cloudflarestorage.com/{remote_path}"
        
        except ClientError as e:
            logger.error(f"R2 upload error: {e}")
            raise
