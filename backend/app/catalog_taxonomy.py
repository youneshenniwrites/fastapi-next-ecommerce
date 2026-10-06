"""Stable workspace categories. All is a storefront choice, not a stored row."""

CATEGORIES: tuple[tuple[str, str, int], ...] = (
    ("desk-organization", "Desk organization", 1),
    ("ergonomics-and-stands", "Ergonomics and stands", 2),
    ("lighting", "Lighting", 3),
    ("writing-and-planning", "Writing and planning", 4),
    ("tech-accessories", "Tech accessories", 5),
    ("workspace-comforts", "Workspace comforts", 6),
    ("uncategorized", "Uncategorized", 7),
)

UNCATEGORIZED_SLUG = "uncategorized"

# Exact current names only. A renamed product is left for the uncategorized fallback
# so this mapping cannot overwrite an edit to the name, price, stock or description.
PRODUCT_CATEGORIES: dict[str, str] = {
    "Oak Monitor Stand": "ergonomics-and-stands",
    "Felt Desk Mat": "desk-organization",
    "Task Light": "lighting",
    "Cable Tray": "desk-organization",
    "Notebook Set": "writing-and-planning",
    "Ceramic Pen Cup": "writing-and-planning",
    "Compact Keyboard": "tech-accessories",
    "Focus Headphones": "tech-accessories",
    "Insulated Bottle": "workspace-comforts",
    "Handled Planter": "workspace-comforts",
    "Analogue Desk Clock": "workspace-comforts",
    "Wireless Mouse": "tech-accessories",
}
