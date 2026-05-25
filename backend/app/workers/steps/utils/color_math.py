import numpy as np
from skimage.color import rgb2lab, lab2rgb
import colorsys


def lab_to_rgb(l: float, a: float, b: float) -> tuple:
    """Convert LAB color to RGB (0-255 range)"""
    lab = np.array([[[l, a, b]]])
    rgb = lab2rgb(lab)
    r = max(0, min(255, int(rgb[0, 0, 0] * 255)))
    g = max(0, min(255, int(rgb[0, 0, 1] * 255)))
    b_val = max(0, min(255, int(rgb[0, 0, 2] * 255)))
    return (r, g, b_val)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color string"""
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_lab(r: int, g: int, b: int) -> tuple:
    """Convert RGB (0-255) to LAB"""
    rgb_normalized = np.array([[[r/255.0, g/255.0, b/255.0]]])
    lab = rgb2lab(rgb_normalized)
    return (lab[0, 0, 0], lab[0, 0, 1], lab[0, 0, 2])


def calculate_delta_e(lab1: tuple, lab2: tuple) -> float:
    """Calculate Delta-E (Euclidean in LAB space - fast approximation)"""
    return float(np.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2))))


CSS_COLORS = {
    "#000000": "Black", "#FFFFFF": "White", "#FF0000": "Red", "#00FF00": "Lime",
    "#0000FF": "Blue", "#FFFF00": "Yellow", "#00FFFF": "Cyan", "#FF00FF": "Magenta",
    "#C0C0C0": "Silver", "#808080": "Gray", "#800000": "Maroon", "#808000": "Olive",
    "#008000": "Green", "#800080": "Purple", "#008080": "Teal", "#000080": "Navy",
    "#FFA500": "Orange", "#FFC0CB": "Pink", "#A52A2A": "Brown", "#F5F5DC": "Beige",
    "#FFD700": "Gold", "#4B0082": "Indigo", "#EE82EE": "Violet", "#F0E68C": "Khaki",
    "#E6E6FA": "Lavender", "#FA8072": "Salmon", "#98FB98": "Pale Green", "#DDA0DD": "Plum",
    "#B0C4DE": "Light Steel Blue", "#F0FFF0": "Honeydew", "#F5FFFA": "Mint Cream",
    "#FFE4E1": "Misty Rose", "#FAEBD7": "Antique White", "#D2691E": "Chocolate",
    "#FF7F50": "Coral", "#6495ED": "Cornflower Blue", "#DC143C": "Crimson",
    "#00CED1": "Dark Turquoise", "#9400D3": "Dark Violet", "#FF1493": "Deep Pink",
    "#1E90FF": "Dodger Blue", "#228B22": "Forest Green", "#FF69B4": "Hot Pink",
    "#CD5C5C": "Indian Red", "#4169E1": "Royal Blue", "#FA8072": "Salmon",
    "#2E8B57": "Sea Green", "#87CEEB": "Sky Blue", "#D2B48C": "Tan",
    "#40E0D0": "Turquoise", "#EE82EE": "Violet", "#F5DEB3": "Wheat"
}


def get_color_name(hex_color: str) -> str:
    """Get descriptive color name from hex value"""
    hex_color = hex_color.upper()
    
    if hex_color in CSS_COLORS:
        return CSS_COLORS[hex_color]
    
    r, g, b = hex_to_rgb(hex_color)
    target_lab = rgb_to_lab(r, g, b)
    
    min_distance = float('inf')
    closest_name = "Custom"
    
    for css_hex, name in CSS_COLORS.items():
        css_r, css_g, css_b = hex_to_rgb(css_hex)
        css_lab = rgb_to_lab(css_r, css_g, css_b)
        distance = calculate_delta_e(target_lab, css_lab)
        
        if distance < min_distance:
            min_distance = distance
            closest_name = name
    
    return closest_name


def apply_hsl_shift(hex_color: str, hue_delta: float = 0, sat_scale: float = 1.0, light_delta: float = 0) -> str:
    """Apply HSL transformations to a hex color"""
    r, g, b = hex_to_rgb(hex_color)
    
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    
    h = (h + hue_delta / 360.0) % 1.0
    s = max(0, min(1, s * sat_scale))
    l = max(0, min(1, l + light_delta / 100.0))
    
    r_new, g_new, b_new = colorsys.hls_to_rgb(h, l, s)
    
    r_int = int(r_new * 255)
    g_int = int(g_new * 255)
    b_int = int(b_new * 255)
    
    return rgb_to_hex(r_int, g_int, b_int)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple:
    """Convert RGB to HSL"""
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    return (h * 360, s * 100, l * 100)


def hsl_to_rgb(h: float, s: float, l: float) -> tuple:
    """Convert HSL to RGB"""
    r, g, b = colorsys.hls_to_rgb(h/360.0, l/100.0, s/100.0)
    return (int(r * 255), int(g * 255), int(b * 255))
