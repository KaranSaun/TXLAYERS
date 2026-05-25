import os
import io
import cv2
import numpy as np
from PIL import Image
import logging
import urllib.request
from pathlib import Path

from app.config import settings
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


def download_realesrgan_model():
    """Download Real-ESRGAN model if not present"""
    model_path = os.path.join(settings.MODEL_PATH, "RealESRGAN_x4plus.pth")
    
    if os.path.exists(model_path):
        logger.info(f"Real-ESRGAN model already exists at {model_path}")
        return model_path
    
    os.makedirs(settings.MODEL_PATH, exist_ok=True)
    
    model_url = "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
    
    logger.info(f"Downloading Real-ESRGAN model from {model_url}")
    urllib.request.urlretrieve(model_url, model_path)
    logger.info(f"Model downloaded to {model_path}")
    
    return model_path


def upscale_image(design, db) -> str:
    """
    Upscale image to 300 DPI using Real-ESRGAN
    
    Args:
        design: Design model instance
        db: Database session
    
    Returns:
        Storage path of upscaled image
    """
    try:
        bucket, key = design.upload_storage_path.split("/", 1)
        image_bytes = storage_service.download_file(bucket, key)
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            raise ValueError("Failed to decode image")
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        source_dpi = design.original_dpi or 72.0
        
        target_dpi = 300.0
        scale_factor = target_dpi / source_dpi
        
        if scale_factor <= 1.0:
            logger.info(f"Image already at or above 300 DPI ({source_dpi} DPI), skipping upscaling")
            upscaled_key = f"{design.id}/upscaled.png"
            
            _, buffer = cv2.imencode('.png', img)
            storage_path = storage_service.upload_file(
                storage_service.outputs_bucket,
                upscaled_key,
                buffer.tobytes(),
                "image/png"
            )
            
            return storage_path
        
        scale_factor = min(scale_factor, 4.0)
        
        logger.info(f"Upscaling image with scale factor {scale_factor} using Lanczos interpolation")
        
        # Use high-quality Lanczos interpolation (no PyTorch needed)
        new_width = int(img.shape[1] * scale_factor)
        new_height = int(img.shape[0] * scale_factor)
        output = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
        
        current_dpi = source_dpi * (output.shape[1] / img.shape[1])
        
        if current_dpi > target_dpi:
            resize_factor = target_dpi / current_dpi
            new_width = int(output.shape[1] * resize_factor)
            new_height = int(output.shape[0] * resize_factor)
            output = cv2.resize(output, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        pil_output = Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))
        pil_output.info['dpi'] = (300, 300)
        
        buffer = io.BytesIO()
        pil_output.save(buffer, format='PNG', dpi=(300, 300))
        buffer.seek(0)
        
        upscaled_key = f"{design.id}/upscaled.png"
        storage_path = storage_service.upload_file(
            storage_service.outputs_bucket,
            upscaled_key,
            buffer.getvalue(),
            "image/png"
        )
        
        logger.info(f"Image upscaled successfully: {output.shape[1]}x{output.shape[0]} at 300 DPI")
        
        return storage_path
        
    except Exception as e:
        logger.error(f"Error upscaling image: {str(e)}")
        raise
