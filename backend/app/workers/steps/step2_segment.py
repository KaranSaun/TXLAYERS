import os
import cv2
import numpy as np
from PIL import Image
import logging
import urllib.request
import io

from app.config import settings
from app.services.storage import storage_service
from app.workers.steps.utils.image_utils import (
    calculate_edge_sharpness,
    calculate_background_uniformity,
    extract_alpha_channel,
    pil_to_cv2
)

logger = logging.getLogger(__name__)


def download_sam2_model():
    """SAM2 model download - not needed for OpenCV watershed"""
    logger.info("Using OpenCV watershed segmentation (no model download needed)")
    return None


def segment_with_rembg(image_rgb: np.ndarray) -> dict:
    """Segment image using rembg (fast method)"""
    try:
        from rembg import remove
        
        pil_img = Image.fromarray(image_rgb)
        
        output = remove(pil_img)
        
        alpha = extract_alpha_channel(output)
        
        if alpha is None:
            return None
        
        motif_mask = alpha
        background_mask = 255 - motif_mask
        
        edge_sharpness = calculate_edge_sharpness(motif_mask)
        bg_uniformity = calculate_background_uniformity(image_rgb, motif_mask)
        
        return {
            'background_mask': background_mask,
            'motif_masks': [motif_mask],
            'quality_score': (edge_sharpness + bg_uniformity) / 2,
            'edge_sharpness': edge_sharpness,
            'bg_uniformity': bg_uniformity,
            'method': 'rembg'
        }
        
    except Exception as e:
        logger.error(f"rembg segmentation failed: {str(e)}")
        return None


def segment_with_sam2(image_rgb: np.ndarray) -> dict:
    """Segment image using SAM2 (accurate method)"""
    try:
        from sam2.build_sam import build_sam2
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator
        
        model_path = download_sam2_model()
        
        sam2 = build_sam2(
            config_file="sam2_hiera_b+.yaml",
            ckpt_path=model_path,
            device="cpu"
        )
        
        mask_generator = SAM2AutomaticMaskGenerator(
            model=sam2,
            points_per_side=32,
            pred_iou_thresh=0.88,
            stability_score_thresh=0.95,
            min_mask_region_area=100
        )
        
        masks = mask_generator.generate(image_rgb)
        
        if not masks:
            return None
        
        masks = sorted(masks, key=lambda x: x['area'], reverse=True)
        
        h, w = image_rgb.shape[:2]
        background_mask = np.zeros((h, w), dtype=np.uint8)
        motif_masks = []
        
        for i, mask_data in enumerate(masks[:10]):
            mask = (mask_data['segmentation'] * 255).astype(np.uint8)
            
            edge_pixels = np.sum(mask[:5, :]) + np.sum(mask[-5:, :]) + \
                         np.sum(mask[:, :5]) + np.sum(mask[:, -5:])
            total_edge_pixels = (5 * w * 2) + (5 * h * 2)
            edge_ratio = edge_pixels / (total_edge_pixels * 255)
            
            if edge_ratio > 0.3 and i == 0:
                background_mask = mask
            else:
                motif_masks.append(mask)
        
        if len(motif_masks) == 0 and len(masks) > 0:
            motif_masks = [(masks[0]['segmentation'] * 255).astype(np.uint8)]
            background_mask = 255 - motif_masks[0]
        
        edge_sharpness = calculate_edge_sharpness(motif_masks[0] if motif_masks else background_mask)
        bg_uniformity = calculate_background_uniformity(image_rgb, motif_masks[0] if motif_masks else background_mask)
        
        return {
            'background_mask': background_mask,
            'motif_masks': motif_masks,
            'quality_score': (edge_sharpness + bg_uniformity) / 2,
            'edge_sharpness': edge_sharpness,
            'bg_uniformity': bg_uniformity,
            'method': 'sam2'
        }
        
    except Exception as e:
        logger.error(f"SAM2 segmentation failed: {str(e)}")
        return None


def segment_image(design, db) -> dict:
    """
    Segment image into background and motif masks
    
    Args:
        design: Design model instance
        db: Database session
    
    Returns:
        Dictionary containing background_mask and motif_masks
    """
    try:
        bucket, key = design.upscaled_storage_path.split("/", 1)
        image_bytes = storage_service.download_file(bucket, key)
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        image_rgb = np.array(pil_img.convert('RGB'))
        
        logger.info("Attempting segmentation with rembg (fast method)...")
        result = segment_with_rembg(image_rgb)
        
        if result and result['edge_sharpness'] >= 0.7 and result['bg_uniformity'] >= 0.6:
            logger.info(f"rembg segmentation successful (quality: {result['quality_score']:.2f})")
            return result
        
        logger.info("rembg quality insufficient, trying SAM2 (accurate method)...")
        sam2_result = segment_with_sam2(image_rgb)
        
        if sam2_result:
            logger.info(f"SAM2 segmentation successful (quality: {sam2_result['quality_score']:.2f})")
            return sam2_result
        
        if result:
            logger.warning("SAM2 failed, using rembg result despite lower quality")
            return result
        
        logger.warning("All segmentation methods failed, creating simple threshold mask")
        gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
        _, motif_mask = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        background_mask = 255 - motif_mask
        
        return {
            'background_mask': background_mask,
            'motif_masks': [motif_mask],
            'quality_score': 0.5,
            'edge_sharpness': 0.5,
            'bg_uniformity': 0.5,
            'method': 'threshold'
        }
        
    except Exception as e:
        logger.error(f"Error segmenting image: {str(e)}")
        raise
