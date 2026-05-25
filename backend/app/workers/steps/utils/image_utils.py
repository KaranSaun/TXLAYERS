import cv2
import numpy as np
from PIL import Image
import io


def refine_mask(mask: np.ndarray) -> np.ndarray:
    """Refine mask edges using morphological operations"""
    if mask.dtype != np.uint8:
        mask = (mask * 255).astype(np.uint8)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=1)
    
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    
    edges = cv2.Canny(mask, 50, 150)
    edge_dilated = cv2.dilate(edges, kernel, iterations=1)
    
    blurred = mask.copy()
    blurred[edge_dilated > 0] = cv2.GaussianBlur(mask, (5, 5), 0)[edge_dilated > 0]
    
    contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    refined = np.zeros_like(mask)
    cv2.drawContours(refined, contours, -1, 255, -1)
    
    return refined


def calculate_edge_sharpness(mask: np.ndarray) -> float:
    """Calculate edge sharpness score for mask quality evaluation"""
    if mask.dtype != np.uint8:
        mask = (mask * 255).astype(np.uint8)
    
    edges = cv2.Canny(mask, 50, 150)
    edge_pixels = np.sum(edges > 0)
    
    if edge_pixels == 0:
        return 0.0
    
    gradient_x = cv2.Sobel(mask, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(mask, cv2.CV_64F, 0, 1, ksize=3)
    gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
    
    edge_gradient = gradient_magnitude[edges > 0]
    sharpness = np.mean(edge_gradient) / 255.0
    
    return min(1.0, sharpness)


def calculate_background_uniformity(image: np.ndarray, mask: np.ndarray) -> float:
    """Calculate background uniformity score"""
    if mask.dtype != np.uint8:
        mask = (mask * 255).astype(np.uint8)
    
    background_mask = (mask == 0)
    
    if np.sum(background_mask) == 0:
        return 0.0
    
    background_pixels = image[background_mask]
    
    if len(background_pixels) == 0:
        return 0.0
    
    std_dev = np.std(background_pixels, axis=0)
    mean_std = np.mean(std_dev)
    
    uniformity = 1.0 - min(1.0, mean_std / 128.0)
    
    return uniformity


def resize_image_maintain_aspect(image: np.ndarray, target_size: tuple) -> np.ndarray:
    """Resize image while maintaining aspect ratio"""
    h, w = image.shape[:2]
    target_w, target_h = target_size
    
    aspect = w / h
    target_aspect = target_w / target_h
    
    if aspect > target_aspect:
        new_w = target_w
        new_h = int(target_w / aspect)
    else:
        new_h = target_h
        new_w = int(target_h * aspect)
    
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)
    
    canvas = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)
    
    y_offset = (target_h - new_h) // 2
    x_offset = (target_w - new_w) // 2
    
    canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
    
    return canvas


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert PIL Image to OpenCV format"""
    if pil_image.mode == 'RGBA':
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
    elif pil_image.mode == 'RGB':
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    else:
        return np.array(pil_image)


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """Convert OpenCV image to PIL Image"""
    if len(cv2_image.shape) == 2:
        return Image.fromarray(cv2_image)
    elif cv2_image.shape[2] == 3:
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))
    elif cv2_image.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGRA2RGBA))
    else:
        return Image.fromarray(cv2_image)


def extract_alpha_channel(image: Image.Image) -> np.ndarray:
    """Extract alpha channel from PIL image as binary mask"""
    if image.mode != 'RGBA':
        return None
    
    alpha = np.array(image.split()[-1])
    
    mask = (alpha > 128).astype(np.uint8) * 255
    
    return mask


def create_thumbnail(image: np.ndarray, size: tuple = (800, 800)) -> bytes:
    """Create JPEG thumbnail from image"""
    pil_img = cv2_to_pil(image)
    
    pil_img.thumbnail(size, Image.Resampling.LANCZOS)
    
    buffer = io.BytesIO()
    if pil_img.mode == 'RGBA':
        pil_img = pil_img.convert('RGB')
    pil_img.save(buffer, format='JPEG', quality=90)
    
    return buffer.getvalue()
