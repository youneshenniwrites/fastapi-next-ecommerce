"""Reviewed workspace catalog for the explicit import command.

Copy is original and fictional. Photographs are the existing local WebP files
already credited for this shop; alternative text describes that photograph.
One item has no photograph. The release cap is 100 products. This reviewed
set contains 60. Nothing here is a supplier feed or a stock promise.
"""

from decimal import Decimal
from pathlib import Path

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.catalog_media import IMAGE_KEYS
from app.catalog_taxonomy import CATEGORIES
from app.schemas.product import (
    CategorySlug,
    Description,
    ImageKey,
    MaterialText,
    Millimetre,
    PlainText,
    Price,
    ProductName,
    Stock,
    _plain_text,
)

RELEASE_CAP = 100
REVIEWED_COUNT = 60
PHOTO_ROOT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "photos"

# Alternative text describes the licensed file, including when several
# fictional products share that file.
IMAGE_ALTS: dict[str, str] = {
    "stand": "Representative photograph of a wooden monitor stand",
    "mat": "Representative photograph of a felt desk mat",
    "lamp": "Representative photograph of a desk lamp",
    "tray": "Representative photograph of a wooden desk tray",
    "notebooks": "Representative photograph of two notebooks",
    "cup": "Representative photograph of a ceramic cup holding pencils",
    "keyboard": "Representative photograph of a computer keyboard",
    "headphones": "Representative photograph of over-ear headphones",
    "bottle": "Representative photograph of a steel bottle",
    "planter": "Representative photograph of a ceramic planter",
    "clock": "Representative photograph of a round analogue clock",
    "mouse": "Representative photograph of a wireless computer mouse",
}

LEGACY_NAMES: dict[str, str] = {
    "oak-monitor-stand": "Oak Monitor Stand",
    "felt-desk-mat": "Felt Desk Mat",
    "task-light": "Task Light",
    "cable-tray": "Cable Tray",
    "notebook-set": "Notebook Set",
    "ceramic-pen-cup": "Ceramic Pen Cup",
    "compact-keyboard": "Compact Keyboard",
    "focus-headphones": "Focus Headphones",
    "insulated-bottle": "Insulated Bottle",
    "handled-planter": "Handled Planter",
    "analogue-desk-clock": "Analogue Desk Clock",
    "wireless-mouse": "Wireless Mouse",
}

# key | name | description | price | stock | category | image | material | w | d | h | legacy
_ROWS = """
oak-monitor-stand | Oak Monitor Stand | Fictional solid-oak desk riser. | 79.00 | 12 | ergonomics-and-stands | stand | Solid oak | 540 | 220 | 80 | Oak Monitor Stand
felt-desk-mat | Felt Desk Mat | Fictional charcoal felt workspace mat. | 29.50 | 24 | desk-organization | mat | Felt | 800 | 400 |  | Felt Desk Mat
task-light | Task Light | Fictional adjustable warm-white desk lamp. | 65.00 | 8 | lighting | lamp | Aluminium | 150 | 150 | 420 | Task Light
cable-tray | Cable Tray | Fictional under-desk cable organiser. | 24.00 | 18 | desk-organization | tray | Wood | 300 | 200 | 40 | Cable Tray
notebook-set | Notebook Set | Fictional set of three dotted notebooks. | 12.90 | 30 | writing-and-planning | notebooks | Paper | 140 | 15 | 210 | Notebook Set
ceramic-pen-cup | Ceramic Pen Cup | Fictional hand-finished stationery holder. | 18.00 | 0 | writing-and-planning | cup | Ceramic | 90 | 90 | 100 | Ceramic Pen Cup
compact-keyboard | Compact Keyboard | Fictional low-profile keyboard for everyday desk work. | 49.00 | 16 | tech-accessories | keyboard | Plastic | 310 | 120 | 22 | Compact Keyboard
focus-headphones | Focus Headphones | Fictional padded over-ear headphones for a quiet workspace. | 89.00 | 7 | tech-accessories | headphones | Plastic |  |  |  | Focus Headphones
insulated-bottle | Insulated Bottle | Fictional green steel bottle for desk-side hydration. | 26.00 | 22 | workspace-comforts | bottle | Steel | 75 | 75 | 260 | Insulated Bottle
handled-planter | Handled Planter | Fictional rustic ceramic planter; plant not included. | 21.00 | 9 | workspace-comforts | planter | Ceramic | 140 | 140 | 130 | Handled Planter
analogue-desk-clock | Analogue Desk Clock | Fictional round bedside or desk clock with a warm metallic finish. | 32.00 | 11 | workspace-comforts | clock |  |  |  |  | Analogue Desk Clock
wireless-mouse | Wireless Mouse | Fictional compact red wireless mouse for everyday browsing. | 23.00 | 14 | tech-accessories | mouse | Plastic | 110 | 62 | 38 | Wireless Mouse
linen-drawer-liner | Linen Drawer Liner | Fictional washed-linen liner for a shallow desk drawer. | 16.00 | 14 | desk-organization | mat | Linen | 340 | 260 | 4 |
walnut-letter-tray | Walnut Letter Tray | Fictional two-tier tray for letters and loose paper. | 38.00 | 6 | desk-organization | tray | Walnut | 250 | 180 | 70 |
brass-clip-dish | Brass Clip Dish | Fictional small brass dish for clips and pins. | 14.50 | 20 | desk-organization | cup | Brass | 80 | 80 | 30 |
slim-document-sleeve | Slim Document Sleeve | Fictional flat sleeve for a few unmarked pages. | 11.00 | 25 | desk-organization | notebooks | Paper | 230 | 5 | 320 |
cork-pin-strip | Cork Pin Strip | Fictional narrow cork strip for notes above a desk. | 19.00 | 8 | desk-organization | mat | Cork | 600 | 80 | 12 |
smoked-glass-inbox | Smoked Glass Inbox | Fictional glass inbox for paper still in use. | 27.00 | 5 | desk-organization | tray | Glass | 220 | 160 | 50 |
woven-cable-sleeve | Woven Cable Sleeve | Fictional sleeve that gathers a short run of cables. | 9.50 | 28 | desk-organization | tray | Cotton | 400 | 30 | 30 |
bamboo-laptop-riser | Bamboo Laptop Riser | Fictional angled riser that lifts a laptop toward eye level. | 42.00 | 10 | ergonomics-and-stands | stand | Bamboo | 280 | 220 | 90 |
walnut-wrist-rest | Walnut Wrist Rest | Fictional low wooden rest for a compact keyboard. | 24.00 | 12 | ergonomics-and-stands | stand | Walnut | 300 | 70 | 18 |
steel-monitor-plinth | Steel Monitor Plinth | Fictional low steel plinth for a lighter display. | 54.00 | 4 | ergonomics-and-stands | stand | Steel | 480 | 180 | 60 |
angled-writing-board | Angled Writing Board | Fictional board that tilts paper toward the writer. | 33.00 | 7 | ergonomics-and-stands | stand | Wood | 360 | 240 | 40 |
cork-footrest | Cork Footrest | Fictional cork wedge for a seated desk position. | 29.00 | 6 | ergonomics-and-stands | mat | Cork | 420 | 280 | 90 |
balance-board | Balance Board | Fictional standing board for shifting weight at a desk. | 46.00 | 3 | ergonomics-and-stands | mat | Wood | 700 | 320 | 70 |
lumbar-cushion | Lumbar Cushion | Fictional small cushion for the lower back of a desk chair. | 22.00 | 15 | ergonomics-and-stands | mat | Linen | 320 | 80 | 120 |
brass-picture-light | Brass Picture Light | Fictional small brass light for a shelf or pinboard. | 48.00 | 5 | lighting | lamp | Brass | 180 | 80 | 90 |
linen-shade-lamp | Linen Shade Lamp | Fictional table lamp with a pale linen shade. | 72.00 | 4 | lighting | lamp | Linen | 200 | 200 | 380 |
puck-task-light | Puck Task Light | Fictional low puck light for a shelf underside. | 18.50 | 17 | lighting | lamp | Aluminium | 90 | 90 | 25 |
clip-reading-lamp | Clip Reading Lamp | Fictional clip lamp for a notebook or shelf edge. | 21.00 | 13 | lighting | lamp | Steel | 120 | 80 | 300 |
amber-night-light | Amber Night Light | Fictional dim amber light for late desk work. | 16.00 | 9 | lighting | lamp | Glass | 70 | 70 | 110 |
linear-shelf-light | Linear Shelf Light | Fictional thin light meant to wash a single shelf. | 36.00 | 8 | lighting | lamp | Aluminium | 400 | 20 | 15 |
paper-lantern | Paper Lantern | Fictional paper shade that softens a desk corner. | 27.50 | 6 | lighting | lamp | Paper | 180 | 180 | 200 |
dotted-pocket-notebook | Dotted Pocket Notebook | Fictional pocket notebook with a light dotted grid. | 8.50 | 40 | writing-and-planning | notebooks | Paper | 90 | 8 | 140 |
linen-weekly-planner | Linen Weekly Planner | Fictional undated planner with a linen cover. | 19.00 | 18 | writing-and-planning | notebooks | Linen | 150 | 12 | 210 |
graphite-pencil-pair | Graphite Pencil Pair | Fictional pair of graphite pencils for markup and notes. | 6.00 | 36 | writing-and-planning | cup | Wood | 7 | 7 | 180 |
ink-bottle | Ink Bottle | Fictional small bottle of black writing ink. | 13.00 | 11 | writing-and-planning | bottle | Glass | 45 | 45 | 80 |
kraft-index-cards | Kraft Index Cards | Fictional pack of plain kraft cards for sorting ideas. | 7.50 | 32 | writing-and-planning | notebooks | Paper | 127 | 10 | 76 |
cloth-book-weight | Cloth Book Weight | Fictional cloth-covered weight that holds a book open. | 15.00 | 10 | writing-and-planning | tray | Cloth | 160 | 40 | 20 |
ruled-legal-pad | Ruled Legal Pad | Fictional ruled pad for longer draft notes. | 5.50 | 27 | writing-and-planning | notebooks | Paper | 150 | 8 | 250 |
usb-c-hub | USB-C Hub | Fictional compact hub for a laptop's side ports. | 39.00 | 14 | tech-accessories | keyboard | Aluminium | 110 | 40 | 15 |
braided-charge-cable | Braided Charge Cable | Fictional one-metre braided cable for desk charging. | 12.00 | 30 | tech-accessories | mouse | Nylon | 1000 | 8 | 8 |
webcam-cover | Webcam Cover | Fictional sliding cover for a laptop camera. | 4.50 | 45 | tech-accessories | mouse | Plastic | 30 | 12 | 3 |
felt-laptop-sleeve | Felt Laptop Sleeve | Fictional felt sleeve for a 13-inch laptop. | 28.00 | 9 | tech-accessories | mat | Felt | 340 | 20 | 240 |
compact-speaker | Compact Speaker | Fictional small desk speaker for a single room. | 45.00 | 7 | tech-accessories | headphones | Plastic | 80 | 80 | 50 |
sd-card-reader | SD Card Reader | Fictional slim reader for transferring camera cards. | 11.50 | 16 | tech-accessories | keyboard | Aluminium | 60 | 20 | 10 |
cable-clip-set | Cable Clip Set | Fictional set of adhesive clips for a desk edge. | 8.00 | 22 | tech-accessories | tray | Plastic | 40 | 15 | 12 |
ceramic-tea-cup | Ceramic Tea Cup | Fictional cup for tea beside the keyboard. | 14.00 | 12 | workspace-comforts | cup | Ceramic | 85 | 85 | 70 |
wool-throw | Wool Throw | Fictional small wool throw for a chair back. | 58.00 | 4 | workspace-comforts | mat | Wool | 1200 | 20 | 700 |
beeswax-candle | Beeswax Candle | Fictional unscented beeswax candle for a desk shelf. | 9.00 | 19 | workspace-comforts | lamp | Beeswax | 60 | 60 | 90 |
linen-napkin-stack | Linen Napkin Stack | Fictional stack of linen napkins for a desk lunch. | 17.00 | 8 | workspace-comforts | mat | Linen | 200 | 10 | 200 |
stone-coaster-set | Stone Coaster Set | Fictional set of four stone coasters. | 18.00 | 11 | workspace-comforts | tray | Stone | 100 | 100 | 8 |
cedar-sachet | Cedar Sachet | Fictional cedar sachet for a closed drawer. | 6.50 | 24 | workspace-comforts | planter | Cedar | 80 | 20 | 80 |
glass-carafe | Glass Carafe | Fictional glass carafe for water at the desk. | 24.00 | 6 | workspace-comforts | bottle | Glass | 90 | 90 | 220 |
unmarked-sample-box | Unmarked Sample Box | Fictional closed sample box with no listed contents or photograph. | 10.00 | 0 | uncategorized |  |  |  |  |  |
workshop-offcut | Workshop Offcut | Fictional leftover wood block kept as a paperweight. | 3.00 | 2 | uncategorized | stand | Wood | 80 | 40 | 30 |
plain-cardboard-mailer | Plain Cardboard Mailer | Fictional plain mailer with no branding. | 2.50 | 20 | uncategorized | tray | Cardboard | 250 | 20 | 350 |
unlabeled-glass-jar | Unlabeled Glass Jar | Fictional empty jar with no product label. | 4.00 | 13 | uncategorized | bottle | Glass | 70 | 70 | 100 |
spare-linen-swatch | Spare Linen Swatch | Fictional loose swatch kept for colour comparison. | 3.50 | 8 | uncategorized | mat | Linen | 120 | 2 | 120 |
mixed-hardware-tin | Mixed Hardware Tin | Fictional tin of unsorted screws and clips. | 5.00 | 1 | uncategorized | cup | Steel | 90 | 90 | 40 |
"""


class CatalogItem(BaseModel):
    """One reviewed product. The key is the import identity, not the public id."""

    model_config = ConfigDict(extra="forbid")
    key: CategorySlug
    name: ProductName
    description: Description
    price: Price
    stock: Stock
    category: CategorySlug
    image_key: ImageKey | None = None
    image_alt: PlainText | None = None
    material: MaterialText | None = None
    width_mm: Millimetre | None = None
    depth_mm: Millimetre | None = None
    height_mm: Millimetre | None = None
    legacy_name: ProductName | None = None

    @field_validator("name", "description", "image_alt", "material", "legacy_name")
    @classmethod
    def text_is_plain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _plain_text(value)

    @model_validator(mode="after")
    def photo_and_alt_are_paired(self) -> "CatalogItem":
        if (self.image_key is None) != (self.image_alt is None):
            raise ValueError("photo and alt text are paired")
        return self


def _optional_int(value: str) -> int | None:
    return int(value) if value else None


def _parse_row(line: str) -> CatalogItem:
    parts = [part.strip() for part in line.split("|")]
    if len(parts) != 12:
        raise ValueError("Catalog row must have 12 fields.")
    (
        key,
        name,
        description,
        price,
        stock,
        category,
        image_key,
        material,
        width,
        depth,
        height,
        legacy,
    ) = parts
    return CatalogItem(
        key=key,
        name=name,
        description=description,
        price=Decimal(price),
        stock=int(stock),
        category=category,
        image_key=image_key or None,
        image_alt=IMAGE_ALTS[image_key] if image_key else None,
        material=material or None,
        width_mm=_optional_int(width),
        depth_mm=_optional_int(depth),
        height_mm=_optional_int(height),
        legacy_name=legacy or None,
    )


def _reviewed_rows() -> tuple[CatalogItem, ...]:
    return tuple(
        _parse_row(line) for line in _ROWS.strip().splitlines() if line.strip()
    )


WORKSPACE_CATALOG: tuple[CatalogItem, ...] = _reviewed_rows()


def validate_manifest(raw, *, photo_root: Path | None = None) -> list[CatalogItem]:
    """Check the whole manifest and its photo files before any database write."""
    if not isinstance(raw, (list, tuple)):
        raise ValueError("Catalog manifest must be a list.")
    if len(raw) > RELEASE_CAP:
        raise ValueError("Catalog import refuses more than 100 products.")
    if len(raw) != REVIEWED_COUNT:
        raise ValueError("The reviewed catalog contains 60 products.")
    items = [CatalogItem.model_validate(item) for item in raw]
    keys = [item.key for item in items]
    names = [item.name for item in items]
    legacy_names = [item.legacy_name for item in items if item.legacy_name is not None]
    if len(keys) != len(set(keys)):
        raise ValueError("Catalog keys must be unique.")
    if len(names) != len(set(names)):
        raise ValueError("Catalog names must be unique in the manifest.")
    if len(legacy_names) != len(set(legacy_names)):
        raise ValueError("Legacy names must be unique in the manifest.")
    if {item.key for item in items if item.legacy_name} != set(LEGACY_NAMES):
        raise ValueError(
            "The reviewed catalog must keep the twelve original demo identities."
        )
    for item in items:
        expected = LEGACY_NAMES.get(item.key)
        if item.legacy_name != expected:
            raise ValueError(
                "Legacy names must belong only to the twelve original demo products."
            )
    if not any(item.stock == 0 for item in items):
        raise ValueError("The reviewed catalog must include an out-of-stock product.")
    if not any(item.image_key is None for item in items):
        raise ValueError(
            "The reviewed catalog must include a product without a photograph."
        )
    present = {item.category for item in items}
    expected_categories = {slug for slug, _, _ in CATEGORIES}
    if present != expected_categories:
        raise ValueError("The reviewed catalog must include every workspace category.")
    root = photo_root or PHOTO_ROOT
    for item in items:
        if item.image_key is None:
            continue
        if item.image_key not in IMAGE_KEYS:
            raise ValueError(f"Catalog photo {item.image_key} is not allowlisted.")
        if not (root / f"{item.image_key}.webp").is_file():
            raise ValueError(
                f"Catalog photo {item.image_key} is not in the local photo set."
            )
    return items
