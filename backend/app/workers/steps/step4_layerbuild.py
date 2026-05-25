import numpy as np
from PIL import Image
import logging
import io

from app.models.layer import Layer, LayerRole
from app.services.storage import storage_service

logger = logging.getLogger(__name__)


def build_layer_file(design, clusters, db) -> list:
    """
    Build individual layer files from color clusters
    
    Args:
        design: Design model instance
        clusters: List of ColorCluster objects
        db: Database session
    
    Returns:
        List of Layer model instances
    """
    try:
        bucket, key = design.upscaled_storage_path.split("/", 1)
        image_bytes = storage_service.download_file(bucket, key)
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        # Cap to 1000px max to match clustering step
        MAX_DIM = 1000
        w_orig, h_orig = pil_img.size
        if max(w_orig, h_orig) > MAX_DIM:
            scale = MAX_DIM / max(w_orig, h_orig)
            new_w = int(w_orig * scale)
            new_h = int(h_orig * scale)
            pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
        image_size = pil_img.size
        
        layers = []
        
        for cluster in clusters:
            r, g, b = cluster.rgb_color
            # Vectorized numpy approach
            layer_array = np.zeros((image_size[1], image_size[0], 4), dtype=np.uint8)
            if cluster.pixel_positions:
                ys, xs = zip(*cluster.pixel_positions)
                ys = np.array(ys); xs = np.array(xs)
                valid = (xs < image_size[0]) & (ys < image_size[1])
                layer_array[ys[valid], xs[valid]] = [r, g, b, 255]
            layer_image = Image.fromarray(layer_array, 'RGBA')
            
            layer_buffer = io.BytesIO()
            layer_image.save(layer_buffer, format='PNG')
            layer_buffer.seek(0)
            
            mask_key = f"{design.id}/layers/layer_{cluster.layer_index}.png"
            mask_storage_path = storage_service.upload_file(
                storage_service.outputs_bucket,
                mask_key,
                layer_buffer.getvalue(),
                "image/png"
            )
            
            layer = Layer(
                design_id=design.id,
                layer_index=cluster.layer_index,
                name=cluster.layer_name,
                role=LayerRole.BACKGROUND if cluster.role == "background" else LayerRole.MOTIF,
                hex_color=cluster.hex_color,
                lab_l=cluster.lab_color[0],
                lab_a=cluster.lab_color[1],
                lab_b=cluster.lab_color[2],
                pixel_count=cluster.pixel_count,
                coverage_percent=cluster.coverage_percent,
                mask_storage_path=mask_storage_path
            )
            
            db.add(layer)
            layers.append(layer)
        
        db.commit()
        
        logger.info(f"Built {len(layers)} layer files")
        
        return layers
        
    except Exception as e:
        logger.error(f"Error building layer files: {str(e)}")
        raise
