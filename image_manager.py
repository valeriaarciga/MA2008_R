"""
image_manager.py — Genera imágenes sintéticas de botella para el planograma.
"""

import os
import re
import hashlib
from PIL import Image, ImageDraw, ImageFont

IMAGES_DIR = os.path.join(os.path.dirname(__file__), "static", "images", "products")
os.makedirs(IMAGES_DIR, exist_ok=True)

BRAND_PALETTE = {
    "coca-cola":    {"bg": "#E3000F", "fg": "#FFFFFF", "label": "Coca-Cola",  "accent": "#000000"},
    "cocacola":     {"bg": "#E3000F", "fg": "#FFFFFF", "label": "Coca-Cola",  "accent": "#000000"},
    "pepsi":        {"bg": "#004B93", "fg": "#FFFFFF", "label": "Pepsi",      "accent": "#E31837"},
    "sprite":       {"bg": "#00A550", "fg": "#FFFFFF", "label": "Sprite",     "accent": "#FFD700"},
    "fanta":        {"bg": "#F7941D", "fg": "#FFFFFF", "label": "Fanta",      "accent": "#E3000F"},
    "manzanita":    {"bg": "#6B8E23", "fg": "#FFFFFF", "label": "Manzanita",  "accent": "#FFD700"},
    "squirt":       {"bg": "#FFD700", "fg": "#2D5016", "label": "Squirt",     "accent": "#2D5016"},
    "fresca":       {"bg": "#E8F5E9", "fg": "#2E7D32", "label": "Fresca",     "accent": "#A5D6A7"},
    "jarritos":     {"bg": "#FF6B35", "fg": "#FFFFFF", "label": "Jarritos",   "accent": "#FFD700"},
    "penafiel":     {"bg": "#1565C0", "fg": "#FFFFFF", "label": "Peñafiel",   "accent": "#E3F2FD"},
    "peñafiel":     {"bg": "#1565C0", "fg": "#FFFFFF", "label": "Peñafiel",   "accent": "#E3F2FD"},
    "topo chico":   {"bg": "#26C6DA", "fg": "#FFFFFF", "label": "Topo Chico", "accent": "#00838F"},
    "7up":          {"bg": "#00703C", "fg": "#FFFFFF", "label": "7UP",        "accent": "#D50000"},
    "lift":         {"bg": "#FFD600", "fg": "#1A1A1A", "label": "Lift",       "accent": "#E65100"},
    "sidral":       {"bg": "#558B2F", "fg": "#FFFFFF", "label": "Sidral",     "accent": "#F9A825"},
    "boing":        {"bg": "#F50057", "fg": "#FFFFFF", "label": "Boing",      "accent": "#FFD740"},
    "jumex":        {"bg": "#F57F17", "fg": "#FFFFFF", "label": "Jumex",      "accent": "#E65100"},
    "del valle":    {"bg": "#2E7D32", "fg": "#FFFFFF", "label": "Del Valle",  "accent": "#A5D6A7"},
    "powerade":     {"bg": "#0D47A1", "fg": "#FFFFFF", "label": "Powerade",   "accent": "#29B6F6"},
    "gatorade":     {"bg": "#FF6D00", "fg": "#FFFFFF", "label": "Gatorade",   "accent": "#212121"},
    "joya":         {"bg": "#6A1B9A", "fg": "#FFFFFF", "label": "Joya",       "accent": "#CE93D8"},
    "mirinda":      {"bg": "#E040FB", "fg": "#FFFFFF", "label": "Mirinda",    "accent": "#F3E5F5"},
    "monster":      {"bg": "#1B1B1B", "fg": "#69FF00", "label": "Monster",    "accent": "#FFFFFF"},
    "barrilitos":   {"bg": "#FF7043", "fg": "#FFFFFF", "label": "Barrilitos", "accent": "#FFF9C4"},
    "agua mineral": {"bg": "#E3F2FD", "fg": "#1565C0", "label": "Agua Min.",  "accent": "#BBDEFB"},
    "ciel":         {"bg": "#E3F2FD", "fg": "#1565C0", "label": "Ciel",       "accent": "#64B5F6"},
    "bonafont":     {"bg": "#E8F5E9", "fg": "#1B5E20", "label": "Bonafont",   "accent": "#81C784"},
    "default":      {"bg": "#455A64", "fg": "#FFFFFF", "label": "",           "accent": "#90A4AE"},
}


def _get_brand(desc: str) -> dict:
    desc_l = str(desc).lower()
    for key, palette in BRAND_PALETTE.items():
        if key != "default" and key in desc_l:
            return palette
    return BRAND_PALETTE["default"]


def _short_name(desc: str, max_chars: int = 18) -> str:
    desc = re.sub(r'\b(No Retornable|Retornable|NR|RET|botella|Botella|ml|ML|lt|LT|lata)\b', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    if len(desc) > max_chars:
        words, result = desc.split(), ""
        for w in words:
            if len(result) + len(w) + 1 <= max_chars:
                result = (result + " " + w).strip()
            else:
                break
        return result
    return desc


def _hex_to_rgb(h: str):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


_cache: dict[str, str] = {}


def get_product_image_path(upc: str, desc: str, w_cm: float = 8.0, h_cm: float = 25.0) -> str:
    upc = str(upc).strip()
    if upc in _cache:
        return _cache[upc]

    path = os.path.join(IMAGES_DIR, f"{hashlib.md5(upc.encode()).hexdigest()[:12]}.png")
    if os.path.exists(path):
        _cache[upc] = path
        return path

    palette    = _get_brand(desc)
    bg_rgb     = _hex_to_rgb(palette["bg"])
    fg_rgb     = _hex_to_rgb(palette["fg"])
    accent_rgb = _hex_to_rgb(palette["accent"])

    PX_PER_CM = 12
    img_w = max(48, int(w_cm * PX_PER_CM))
    img_h = max(80, int(h_cm * PX_PER_CM))

    img  = Image.new("RGBA", (img_w, img_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    body_x0 = int(img_w * 0.12);  body_x1 = int(img_w * 0.88)
    neck_x0  = int(img_w * 0.28); neck_x1  = int(img_w * 0.72)
    neck_h   = int(img_h * 0.12); cap_h    = int(img_h * 0.06)
    r        = int((body_x1 - body_x0) * 0.18)

    draw.rounded_rectangle([body_x0, neck_h, body_x1, img_h - 2], radius=r, fill=bg_rgb)
    draw.rectangle([neck_x0, cap_h + 2, neck_x1, neck_h + r], fill=bg_rgb)
    draw.rounded_rectangle([neck_x0 - 2, 0, neck_x1 + 2, cap_h + 4], radius=4, fill=accent_rgb)

    hi_x = body_x0 + int((body_x1 - body_x0) * 0.08)
    hi_w = int((body_x1 - body_x0) * 0.12)
    for i in range(hi_w):
        alpha = int(120 * (1 - i / hi_w))
        draw.line([(hi_x + i, neck_h + r + 4), (hi_x + i, img_h - 8)],
                  fill=(255, 255, 255, alpha), width=1)

    label_top    = int(img_h * 0.30)
    label_bottom = int(img_h * 0.72)
    draw.rectangle([body_x0 + 2, label_top, body_x1 - 2, label_bottom], fill=(*accent_rgb, 200))

    brand_name = palette["label"] or _short_name(desc, 12)
    short_desc = _short_name(desc, 16)

    fnt_sz_big   = max(10, min(18, img_w // 4))
    fnt_sz_small = max(8,  min(13, img_w // 6))
    try:
        font_big   = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", fnt_sz_big)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", fnt_sz_small)
    except Exception:
        font_big = font_small = ImageFont.load_default()

    # Fondo sólido detrás del texto para máxima legibilidad
    def _draw_text_with_bg(draw, text, font, cx, cy, fg, bg=(0, 0, 0)):
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = cx - tw // 2, cy - th // 2
        pad = 3
        draw.rounded_rectangle([x - pad, y - pad, x + tw + pad, y + th + pad],
                                radius=3, fill=(*bg, 180))
        draw.text((x, y), text, font=font, fill=(*fg, 255))

    label_zone_mid = (label_top + label_bottom) // 2
    _draw_text_with_bg(draw, brand_name, font_big,
                       img_w // 2, label_zone_mid - fnt_sz_big // 2 - 2,
                       fg_rgb, bg=(0, 0, 0) if fg_rgb[0] > 128 else (255, 255, 255))
    _draw_text_with_bg(draw, short_desc, font_small,
                       img_w // 2, label_zone_mid + fnt_sz_small,
                       fg_rgb, bg=(0, 0, 0) if fg_rgb[0] > 128 else (255, 255, 255))

    img.save(path, "PNG")
    _cache[upc] = path
    return path


def get_product_image_pil(upc: str, desc: str, w_cm: float = 8.0, h_cm: float = 25.0) -> Image.Image:
    return Image.open(get_product_image_path(upc, desc, w_cm, h_cm)).convert("RGBA")
