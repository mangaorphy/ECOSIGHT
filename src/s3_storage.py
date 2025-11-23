"""
S3 Storage Utilities for EcoSight
Handles uploading/downloading training data from AWS S3
"""

import os
import logging
from pathlib import Path
from typing import List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class S3Storage:
    """Handles S3 operations for training data"""
    
    def __init__(self, bucket_name: Optional[str] = None):
        """
        Initialize S3 storage client
        
        Args:
            bucket_name: S3 bucket name (defaults to env var S3_BUCKET)
        """
        self.bucket_name = bucket_name or os.getenv("S3_BUCKET", "ecosight-training-data")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        
        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                region_name=self.region,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            logger.info(f"S3 client initialized for bucket: {self.bucket_name}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    def download_model(self, local_dir: str = "/app/models") -> bool:
        """
        Download trained model files from S3
        
        Args:
            local_dir: Local directory to download model files to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            # Create local directory
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            
            # Model files to download
            model_files = [
                "yamnet_classifier_v2.keras",
                "class_names.json",
                "model_metadata.json",
                "performance_metrics.json",
                "training_history.pkl",  
            ]
    
            logger.info(f"Downloading model files from S3 to {local_dir}")
            
            for file_name in model_files:
                s3_key = f"models/{file_name}"
                local_path = Path(local_dir) / file_name
                
                try:
                    logger.info(f"Downloading {s3_key}")
                    self.s3_client.download_file(
                        self.bucket_name,
                        s3_key,
                        str(local_path)
                    )
                    logger.info(f"✓ Downloaded {file_name}")
                except ClientError as e:
                    if e.response['Error']['Code'] == '404':
                        logger.warning(f"File not found in S3: {s3_key}")
                        # Only model file is required
                        if file_name == "yamnet_classifier_v2.keras":
                            return False
                    else:
                        logger.error(f"Error downloading {s3_key}: {e}")
                        if file_name == "yamnet_classifier_v2.keras":
                            return False
            
            logger.info("Model download complete")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading model from S3: {e}")
            return False
    
    def download_extracted_audio(self, local_dir: str = "/app/extracted_audio") -> bool:
        """
        Download original/raw audio files from S3 (extracted_audio folder)
        
        Args:
            local_dir: Local directory to download files to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            # Create local directory
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            
            # List all objects in bucket
            logger.info(f"Downloading extracted audio from s3://{self.bucket_name}/extracted_audio/")
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='extracted_audio/')
            
            file_count = 0
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    
                    # Skip directories
                    if s3_key.endswith('/'):
                        continue
                    
                    # Process both .wav and .mp3 files
                    if not (s3_key.endswith('.wav') or s3_key.endswith('.mp3')):
                        continue
                    
                    # Calculate local path
                    # s3_key format: extracted_audio/dog_bark/file.mp3
                    relative_path = s3_key.replace('extracted_audio/', '')
                    local_path = Path(local_dir) / relative_path
                    
                    # Create subdirectory if needed
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Download file
                    logger.debug(f"Downloading: {s3_key} -> {local_path}")
                    self.s3_client.download_file(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Filename=str(local_path)
                    )
                    file_count += 1
            
            logger.info(f"✓ Downloaded {file_count} extracted audio files from S3")
            return True
            
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
            return False
    
    def download_training_data(self, local_dir: str = "/app/augmented_audio") -> bool:
        """
        Download all training audio files from S3 to local directory
        (DEPRECATED: Use download_extracted_audio + augmentation instead)
        
        Args:
            local_dir: Local directory to download files to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            # Create local directory
            Path(local_dir).mkdir(parents=True, exist_ok=True)
            
            # List all objects in bucket
            logger.info(f"Downloading training data from s3://{self.bucket_name}/augmented_audio/")
            
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='augmented_audio/')
            
            file_count = 0
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    
                    # Skip directories
                    if s3_key.endswith('/'):
                        continue
                    
                    # Only process .wav files
                    if not s3_key.endswith('.wav'):
                        continue
                    
                    # Calculate local path
                    # s3_key format: augmented_audio/dog_bark/file.wav
                    relative_path = s3_key.replace('augmented_audio/', '')
                    local_path = Path(local_dir) / relative_path
                    
                    # Create subdirectory if needed
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Download file
                    logger.debug(f"Downloading: {s3_key} -> {local_path}")
                    self.s3_client.download_file(
                        Bucket=self.bucket_name,
                        Key=s3_key,
                        Filename=str(local_path)
                    )
                    file_count += 1
            
            logger.info(f"✓ Downloaded {file_count} training audio files from S3")
            return True
            
        except ClientError as e:
            logger.error(f"S3 download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading from S3: {e}")
            return False
    
    def upload_file(self, local_file: str, s3_key: str) -> bool:
        """
        Upload a single file to S3
        
        Args:
            local_file: Path to local file
            s3_key: S3 object key (path in bucket)
            
        Returns:
            bool: True if successful
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            self.s3_client.upload_file(
                Filename=local_file,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"✓ Uploaded {local_file} to s3://{self.bucket_name}/{s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            return False
    
    def upload_training_data(self, local_dir: str = "./augmented_audio") -> bool:
        """
        Upload all training audio files from local directory to S3
        
        Args:
            local_dir: Local directory containing audio files
            
        Returns:
            bool: True if successful
        """
        if not self.s3_client:
            logger.error("S3 client not initialized")
            return False
        
        try:
            local_path = Path(local_dir)
            if not local_path.exists():
                logger.error(f"Directory not found: {local_dir}")
                return False
            
            # Find all .wav files
            wav_files = list(local_path.rglob("*.wav"))
            logger.info(f"Found {len(wav_files)} audio files to upload")
            
            for wav_file in wav_files:
                # Calculate relative path
                relative_path = wav_file.relative_to(local_path)
                s3_key = f"augmented_audio/{relative_path}"
                
                # Upload file
                self.upload_file(str(wav_file), s3_key)
            
            logger.info(f"✓ Uploaded {len(wav_files)} files to S3")
            return True
            
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return False
    
    def list_training_files(self) -> List[str]:
        """
        List all training audio files in S3
        
        Returns:
            List of S3 keys
        """
        if not self.s3_client:
            return []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix='augmented_audio/')
            
            files = []
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    if obj['Key'].endswith('.wav'):
                        files.append(obj['Key'])
            
            return files
            
        except ClientError as e:
            logger.error(f"Failed to list S3 files: {e}")
            return []


# Singleton instance
_s3_storage = None

def get_s3_storage() -> S3Storage:
    """Get or create S3Storage singleton instance"""
    global _s3_storage
    if _s3_storage is None:
        _s3_storage = S3Storage()
    return _s3_storage
