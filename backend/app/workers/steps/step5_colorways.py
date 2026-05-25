import numpy as np
from PIL import Image
import logging
import io

from app.config import settings
from app.models.colorway import Colorway, ColorwayType
from app.models.layer import LayerRole
from app.services.storage import storage_service
from app.workers.steps.utils.color_math import apply_hsl_shift, hex_to_rgb
from app.workers.steps.utils.image_utils import create_thumbnail

logger = logging.getLogger(__name__)


SEASONAL_PRESETS = {
    'earth_tones': {'hue_shift': 30, 'saturation_scale': 0.8, 'lightness_shift': -10},
    'pastels': {'hue_shift': 0, 'saturation_scale': 0.4, 'lightness_shift': 20},
    'winter': {'hue_shift': 200, 'saturation_scale': 0.6, 'lightness_shift': 5},
    'neon': {'hue_shift': 0, 'saturation_scale': 1.5, 'lightness_shift': 0},
}

BACKGROUND_PRESETS = [
    {'name': 'Ivory', 'hex': '#FFFFF0'},
    {'name': 'Charcoal', 'hex': '#36454F'},
    {'name': 'Navy', 'hex': '#001F5B'},
    {'name': 'Sage', 'hex': '#B2AC88'},
    {'name': 'Dusty Rose', 'hex': '#DCAE96'},
]


def create_single_colorway(design, layers, name, color_map, variant_type, db, variant_index=0):
    """Create a single colorway variant"""
    try:
        bucket, key = design.upscaled_storage_path.split("/", 1)
        image_bytes = storage_service.download_file(bucket, key)
        
        pil_img = Image.open(io.BytesIO(image_bytes))
        # Use same capped size as the layer files (1000px max)
        MAX_DIM = 1000
        w_orig, h_orig = pil_img.size
        if max(w_orig, h_orig) > MAX_DIM:
            scale = MAX_DIM / max(w_orig, h_orig)
            pil_img = pil_img.resize((int(w_orig * scale), int(h_orig * scale)), Image.LANCZOS)
        image_size = pil_img.size
        
        composite = Image.new('RGB', image_size, (255, 255, 255))
        
        sorted_layers = sorted(layers, key=lambda l: (l.role == LayerRole.MOTIF, l.layer_index))
        
        for layer in sorted_layers:
            layer_id_str = str(layer.id)
            
            if layer_id_str in color_map:
                new_hex = color_map[layer_id_str]
            else:
                new_hex = layer.hex_color
            
            r, g, b = hex_to_rgb(new_hex)
            
            layer_bucket, layer_key = layer.mask_storage_path.split("/", 1)
            layer_bytes = storage_service.download_file(layer_bucket, layer_key)
            layer_img = Image.open(io.BytesIO(layer_bytes)).convert('RGBA')
            # Ensure mask matches composite size
            if layer_img.size != image_size:
                layer_img = layer_img.resize(image_size, Image.NEAREST)
            
            colored_layer = Image.new('RGBA', image_size, (r, g, b, 0))
            colored_layer.putalpha(layer_img.split()[-1])
            
            composite.paste(colored_layer, (0, 0), colored_layer)
        
        tif_buffer = io.BytesIO()
        composite.save(tif_buffer, format='TIFF', compression='tiff_deflate', dpi=(300, 300))
        tif_buffer.seek(0)
        
        tif_key = f"{design.id}/colorways/variant_{variant_index}.tif"
        tif_storage_path = storage_service.upload_file(
            storage_service.outputs_bucket,
            tif_key,
            tif_buffer.getvalue(),
            "image/tiff"
        )
        
        composite_array = np.array(composite)
        preview_bytes = create_thumbnail(composite_array, (800, 800))
        
        preview_key = f"{design.id}/colorways/variant_{variant_index}_preview.jpg"
        preview_storage_path = storage_service.upload_file(
            storage_service.outputs_bucket,
            preview_key,
            preview_bytes,
            "image/jpeg"
        )
        
        colorway = Colorway(
            design_id=design.id,
            variant_index=variant_index,
            name=name,
            variant_type=ColorwayType(variant_type),
            color_map=color_map,
            tif_storage_path=tif_storage_path,
            preview_storage_path=preview_storage_path
        )
        
        db.add(colorway)
        
        logger.info(f"Created colorway: {name}")
        
        return colorway
        
    except Exception as e:
        logger.error(f"Error creating colorway '{name}': {str(e)}")
        raise


def generate_colorways(design, layers, db):
    """
    Generate 10 colorway variants
    
    Args:
        design: Design model instance
        layers: List of Layer model instances
        db: Database session
    """
    try:
        colorways = []
        variant_index = 0
        
        motif_layers = [l for l in layers if l.role == LayerRole.MOTIF]
        bg_layers = [l for l in layers if l.role == LayerRole.BACKGROUND]
        
        for hue_shift in [30, 60, 90]:
            color_map = {}
            for layer in motif_layers:
                new_hex = apply_hsl_shift(layer.hex_color, hue_delta=hue_shift)
                color_map[str(layer.id)] = new_hex
            
            name = f"Hue Shift +{hue_shift}°"
            colorway = create_single_colorway(
                design, layers, name, color_map, "motif_only", db, variant_index
            )
            colorways.append(colorway)
            variant_index += 1
        
        for i, bg_preset in enumerate(BACKGROUND_PRESETS[:2]):
            color_map = {}
            for layer in bg_layers:
                color_map[str(layer.id)] = bg_preset['hex']
            
            name = f"{bg_preset['name']} Background"
            colorway = create_single_colorway(
                design, layers, name, color_map, "bg_only", db, variant_index
            )
            colorways.append(colorway)
            variant_index += 1
        
        for preset_name, preset_values in list(SEASONAL_PRESETS.items())[:2]:
            color_map = {}
            for layer in layers:
                new_hex = apply_hsl_shift(
                    layer.hex_color,
                    hue_delta=preset_values['hue_shift'],
                    sat_scale=preset_values['saturation_scale'],
                    light_delta=preset_values['lightness_shift']
                )
                color_map[str(layer.id)] = new_hex
            
            name = preset_name.replace('_', ' ').title()
            colorway = create_single_colorway(
                design, layers, name, color_map, "full", db, variant_index
            )
            colorways.append(colorway)
            variant_index += 1
        
        color_map = {}
        for layer in motif_layers:
            new_hex = apply_hsl_shift(layer.hex_color, hue_delta=180)
            color_map[str(layer.id)] = new_hex
        
        name = "Complementary Colors"
        colorway = create_single_colorway(
            design, layers, name, color_map, "motif_only", db, variant_index
        )
        colorways.append(colorway)
        variant_index += 1
        
        color_map = {}
        for i, layer in enumerate(motif_layers):
            lightness_shift = -20 + (i * 10)
            new_hex = apply_hsl_shift(
                motif_layers[0].hex_color if motif_layers else layer.hex_color,
                light_delta=lightness_shift
            )
            color_map[str(layer.id)] = new_hex
        
        name = "Monochromatic"
        colorway = create_single_colorway(
            design, layers, name, color_map, "motif_only", db, variant_index
        )
        colorways.append(colorway)
        variant_index += 1
        
        color_map = {}
        for layer in bg_layers:
            color_map[str(layer.id)] = BACKGROUND_PRESETS[2]['hex']
        for layer in motif_layers:
            new_hex = apply_hsl_shift(layer.hex_color, hue_delta=45)
            color_map[str(layer.id)] = new_hex
        
        name = "Navy + Warm Shift"
        colorway = create_single_colorway(
            design, layers, name, color_map, "full", db, variant_index
        )
        colorways.append(colorway)
        variant_index += 1
        
        db.commit()
        
        logger.info(f"Generated {len(colorways)} colorway variants")
        
        return colorways
        
    except Exception as e:
        logger.error(f"Error generating colorways: {str(e)}")
        raise
