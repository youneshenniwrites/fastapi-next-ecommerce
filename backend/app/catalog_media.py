"""Allowlisted local product photos and a few stated demo facts.

The image key is the photograph's identity. A product rename must not change it.
Keys match files in frontend/public/photos, excluding the storefront hero.
"""

IMAGE_KEYS: tuple[str, ...] = (
    "stand",
    "mat",
    "lamp",
    "tray",
    "notebooks",
    "cup",
    "keyboard",
    "headphones",
    "bottle",
    "planter",
    "clock",
    "mouse",
)

# Exact current demo names only. A renamed product keeps whatever was already
# stored; this mapping cannot overwrite an edit.
PRODUCT_MEDIA: dict[str, dict[str, str | int]] = {
    "Oak Monitor Stand": {
        "image_key": "stand",
        "image_alt": "Representative photograph of a wooden monitor stand",
        "material": "Solid oak",
        "width_mm": 540,
        "depth_mm": 220,
        "height_mm": 80,
    },
    "Felt Desk Mat": {
        "image_key": "mat",
        "image_alt": "Representative photograph of a felt desk mat",
        "material": "Felt",
        "width_mm": 800,
        "depth_mm": 400,
    },
    "Task Light": {
        "image_key": "lamp",
        "image_alt": "Representative photograph of a desk lamp",
        "material": "Aluminium",
        "width_mm": 150,
        "depth_mm": 150,
        "height_mm": 420,
    },
    "Cable Tray": {
        "image_key": "tray",
        "image_alt": "Representative photograph of a wooden desk tray",
        "material": "Wood",
        "width_mm": 300,
        "depth_mm": 200,
        "height_mm": 40,
    },
    "Notebook Set": {
        "image_key": "notebooks",
        "image_alt": "Representative photograph of two notebooks",
        "material": "Paper",
        "width_mm": 140,
        "depth_mm": 15,
        "height_mm": 210,
    },
    "Ceramic Pen Cup": {
        "image_key": "cup",
        "image_alt": "Representative photograph of a ceramic cup holding pencils",
        "material": "Ceramic",
        "width_mm": 90,
        "depth_mm": 90,
        "height_mm": 100,
    },
    "Compact Keyboard": {
        "image_key": "keyboard",
        "image_alt": "Representative photograph of a computer keyboard",
        "material": "Plastic",
        "width_mm": 310,
        "depth_mm": 120,
        "height_mm": 22,
    },
    "Focus Headphones": {
        "image_key": "headphones",
        "image_alt": "Representative photograph of over-ear headphones",
        "material": "Plastic",
    },
    "Insulated Bottle": {
        "image_key": "bottle",
        "image_alt": "Representative photograph of a steel bottle",
        "material": "Steel",
        "width_mm": 75,
        "depth_mm": 75,
        "height_mm": 260,
    },
    "Handled Planter": {
        "image_key": "planter",
        "image_alt": "Representative photograph of a ceramic planter",
        "material": "Ceramic",
        "width_mm": 140,
        "depth_mm": 140,
        "height_mm": 130,
    },
    "Analogue Desk Clock": {
        "image_key": "clock",
        "image_alt": "Representative photograph of a round analogue clock",
    },
    "Wireless Mouse": {
        "image_key": "mouse",
        "image_alt": "Representative photograph of a wireless computer mouse",
        "material": "Plastic",
        "width_mm": 110,
        "depth_mm": 62,
        "height_mm": 38,
    },
}


def image_key_sql() -> str:
    """Return a portable check that accepts only the allowlisted file keys."""
    quoted = ", ".join(f"'{key}'" for key in IMAGE_KEYS)
    return f"image_key IS NULL OR image_key IN ({quoted})"
