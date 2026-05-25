import cv2
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
from skimage.color import rgb2lab
import logging
import io
from collections import defaultdict

from app.config import settings
from app.services.storage import storage_service
from app.workers.steps.utils.color_math import (
    lab_to_rgb,
    rgb_to_hex,
    rgb_to_lab,
    get_color_name,
    calculate_delta_e
)
from app.workers.steps.utils.image_utils import refine_mask

logger = logging.getLogger(__name__)


class ColorCluster:
    def __init__(self, cluster_id, lab_color, rgb_color, hex_color, pixel_mask, 
                 role, coverage_percent, layer_name, pixel_positions):
        self.cluster_id = cluster_id
        self.lab_color = lab_color
        self.rgb_color = rgb_color
        self.hex_color = hex_color
        self.pixel_mask = pixel_mask
        self.role = role
        self.coverage_percent = coverage_percent
        self.layer_name = layer_name
        self.pixel_positions = pixel_positions
        self.pixel_count = len(pixel_positions)


def cluster_colors(design, masks, db) -> list:
    """
    Cluster colors in the image using KMeans and Delta-E merging
    
    Args:
        design: Design model instance
        masks: Dictionary containing segmentation masks
        db: Database session
    
    Returns:
        List of ColorCluster objects
    """
    try:
        bucket, key = design.upscaled_storage_path.split("/", 1)
        image_bytes = storage_service.download_file(bucket, key)
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        image_rgb = np.array(pil_img.convert('RGB'))
        
        # Cap size to avoid OOM - resize for processing only
        MAX_DIM = 1000
        h_orig, w_orig = image_rgb.shape[:2]
        if max(h_orig, w_orig) > MAX_DIM:
            scale = MAX_DIM / max(h_orig, w_orig)
            new_w = int(w_orig * scale)
            new_h = int(h_orig * scale)
            image_rgb = cv2.resize(image_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized from {w_orig}x{h_orig} to {new_w}x{new_h} for processing")
        
        h, w = image_rgb.shape[:2]
        
        background_mask = masks['background_mask']
        motif_masks = masks['motif_masks']
        
        # Resize masks to match capped image size
        background_mask = cv2.resize(background_mask, (w, h), interpolation=cv2.INTER_NEAREST)
        motif_masks = [cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST) for m in motif_masks]
        
        background_mask = refine_mask(background_mask)
        motif_masks = [refine_mask(m) for m in motif_masks]
        
        combined_motif_mask = np.zeros((h, w), dtype=np.uint8)
        for motif_mask in motif_masks:
            combined_motif_mask = cv2.bitwise_or(combined_motif_mask, motif_mask)
        
        lab_image = rgb2lab(image_rgb)
        
        # Vectorized - no Python loops
        all_pixels = lab_image.reshape(-1, 3)
        ys, xs = np.mgrid[0:h, 0:w]
        pixel_coords = list(zip(ys.ravel().tolist(), xs.ravel().tolist()))
        
        max_clusters = min(16, settings.MAX_LAYERS)
        max_clusters = max(8, max_clusters)
        
        # Sample pixels for faster KMeans (max 50k pixels)
        if len(all_pixels) > 50000:
            sample_idx = np.random.choice(len(all_pixels), 50000, replace=False)
            sample_pixels = all_pixels[sample_idx]
        else:
            sample_idx = np.arange(len(all_pixels))
            sample_pixels = all_pixels
        
        logger.info(f"Running KMeans with {max_clusters} clusters on {len(sample_pixels)} pixels...")
        kmeans = KMeans(n_clusters=max_clusters, random_state=42, n_init=5, max_iter=200)
        kmeans.fit(sample_pixels)
        labels = kmeans.predict(all_pixels)
        centers = kmeans.cluster_centers_
        
        logger.info("Merging similar colors using Delta-E...")
        merge_map = {}
        delta_e_threshold = settings.DELTA_E_MERGE_THRESHOLD
        
        for i in range(len(centers)):
            if i in merge_map:
                continue
            for j in range(i + 1, len(centers)):
                if j in merge_map:
                    continue
                
                de = calculate_delta_e(
                    tuple(centers[i]),
                    tuple(centers[j])
                )
                
                if de < delta_e_threshold:
                    merge_map[j] = i
        
        for old_label, new_label in merge_map.items():
            labels[labels == old_label] = new_label
        
        unique_labels = np.unique(labels)
        
        logger.info(f"Merged to {len(unique_labels)} unique color clusters")
        
        clusters = []
        
        for idx, label in enumerate(unique_labels):
            mask_indices = labels == label
            cluster_pixels = all_pixels[mask_indices]
            cluster_coords = [pixel_coords[i] for i in range(len(pixel_coords)) if mask_indices[i]]
            
            avg_lab = np.mean(cluster_pixels, axis=0)
            l, a, b = avg_lab
            
            r, g, b_rgb = lab_to_rgb(l, a, b)
            hex_color = rgb_to_hex(r, g, b_rgb)
            color_name = get_color_name(hex_color)
            
            pixel_mask = np.zeros((h, w), dtype=np.uint8)
            if cluster_coords:
                cy, cx = zip(*cluster_coords)
                pixel_mask[list(cy), list(cx)] = 255
            
            total_pixels = h * w
            coverage = (len(cluster_coords) / total_pixels) * 100
            
            edge_pixels = 0
            for y, x in cluster_coords[:min(100, len(cluster_coords))]:
                if y < 5 or y >= h - 5 or x < 5 or x >= w - 5:
                    edge_pixels += 1
            
            edge_ratio = edge_pixels / min(100, len(cluster_coords)) if len(cluster_coords) > 0 else 0
            
            overlap_with_bg = np.sum((background_mask > 0) & (pixel_mask > 0))
            overlap_with_motif = np.sum((combined_motif_mask > 0) & (pixel_mask > 0))
            
            if overlap_with_bg > overlap_with_motif or edge_ratio > 0.3:
                role = "background"
            else:
                role = "motif"
            
            layer_name = f"{role.capitalize()} - {hex_color} {color_name}"
            
            cluster = ColorCluster(
                cluster_id=idx,
                lab_color=(l, a, b),
                rgb_color=(r, g, b_rgb),
                hex_color=hex_color,
                pixel_mask=pixel_mask,
                role=role,
                coverage_percent=coverage,
                layer_name=layer_name,
                pixel_positions=cluster_coords
            )
            
            clusters.append(cluster)
        
        clusters.sort(key=lambda c: (c.role == 'motif', -c.coverage_percent))
        
        if len(clusters) > settings.MAX_LAYERS:
            logger.warning(f"Limiting clusters from {len(clusters)} to {settings.MAX_LAYERS}")
            clusters = clusters[:settings.MAX_LAYERS]
        
        for i, cluster in enumerate(clusters):
            cluster.layer_index = i
        
        logger.info(f"Created {len(clusters)} color clusters")
        
        return clusters
        
    except Exception as e:
        logger.error(f"Error clustering colors: {str(e)}")
        raise
