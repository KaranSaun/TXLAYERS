import numpy as np
from PIL import Image
import tifffile
import logging
import io

from app.models.layer import LayerRole
from app.services.storage import storage_service
from app.workers.steps.utils.color_math import hex_to_rgb

logger = logging.getLogger(__name__)


def export_master_tiff(design, layers, db):
    """
    Export master multi-layer TIFF file
    
    Args:
        design: Design model instance
        layers: List of Layer model instances
        db: Database session
    """
    try:
        bucket, key = design.upscaled_storage_path.split("/", 1)
        image_bytes = storage_service.download_file(bucket, key)
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        # Cap to 1000px to avoid OOM
        MAX_DIM = 1000
        w_orig, h_orig = pil_img.size
        if max(w_orig, h_orig) > MAX_DIM:
            scale = MAX_DIM / max(w_orig, h_orig)
            pil_img = pil_img.resize((int(w_orig * scale), int(h_orig * scale)), Image.LANCZOS)
        image_size = pil_img.size
        
        sorted_layers = sorted(layers, key=lambda l: (l.role == LayerRole.MOTIF, l.layer_index))
        # Cap to 16 layers max for TIFF export
        sorted_layers = sorted_layers[:16]
        
        layer_images = []
        layer_names = []
        
        for layer in sorted_layers:
            layer_bucket, layer_key = layer.mask_storage_path.split("/", 1)
            layer_bytes = storage_service.download_file(layer_bucket, layer_key)
            layer_img = Image.open(io.BytesIO(layer_bytes)).convert('RGBA')
            layer_img = layer_img.resize(image_size, Image.NEAREST)
            
            r, g, b = hex_to_rgb(layer.hex_color)
            alpha = np.array(layer_img.split()[-1])
            layer_array = np.zeros((image_size[1], image_size[0], 4), dtype=np.uint8)
            layer_array[:, :, 0] = r
            layer_array[:, :, 1] = g
            layer_array[:, :, 2] = b
            layer_array[:, :, 3] = alpha
            layer_images.append(layer_array)
            layer_names.append(layer.name)
            del layer_array, alpha  # free memory immediately
        
        layer_count = len(layer_images)
        tif_buffer = io.BytesIO()
        tifffile.imwrite(
            tif_buffer,
            np.array(layer_images),
            compression='zlib',
            resolution=(300, 300),
            metadata={'LayerNames': layer_names}
        )
        layer_images.clear()  # free memory
        
        tif_buffer.seek(0)
        
        master_key = f"{design.id}/master_layers.tif"
        storage_path = storage_service.upload_file(
            storage_service.outputs_bucket,
            master_key,
            tif_buffer.getvalue(),
            "image/tiff"
        )
        
        logger.info(f"Exported master TIFF with {layer_count} layers to {storage_path}")
        
        return storage_path
        
    except Exception as e:
        logger.error(f"Error exporting master TIFF: {str(e)}")
        raise
