"""Public catalog queries against disposable SQLite and CI PostgreSQL databases."""

import pytest
from sqlalchemy import select

from app.models.category import Category
from app.models.product import Product

SEARCH = "/api/v1/products/search"


def test_search_reaches_later_products_without_changing_the_legacy_list(client, db):
    db.add_all(
        Product(name=f"Desk item {number:02}", price=number, stock=1)
        for number in range(31)
    )
    db.commit()

    first = client.get(SEARCH)
    second = client.get(SEARCH, params={"skip": 24})
    assert first.status_code == second.status_code == 200
    assert (first.json()["total"], first.json()["limit"], first.json()["skip"]) == (
        31,
        24,
        0,
    )
    assert len(first.json()["items"]) == 24
    assert len(second.json()["items"]) == 7
    assert second.json()["items"][-1]["name"] == "Desk item 30"
    later_match = client.get(SEARCH, params={"q": "item 30"}).json()
    assert later_match["total"] == 1
    assert later_match["items"][0]["name"] == "Desk item 30"
    assert {p["id"] for p in first.json()["items"]}.isdisjoint(
        {p["id"] for p in second.json()["items"]}
    )
    assert isinstance(client.get("/api/v1/products/?limit=100").json(), list)
    assert (
        client.get("/api/v1/products/", params={"skip": 24}).json()[0]["name"]
        == "Desk item 24"
    )


def test_filters_apply_before_total_and_page(client, db):
    db.add_all(
        [
            Product(name="Desk Lamp", price="12.30", stock=0),
            Product(name="desk mat", price="12.30", stock=2),
            Product(name="DESK tray", price="9.00", stock=3),
            Product(name="Plant", price="8.00", stock=4),
        ]
    )
    db.commit()

    response = client.get(
        SEARCH,
        params={
            "q": "  dEsK  ",
            "in_stock": "true",
            "sort": "price-desc",
            "limit": 1,
            "skip": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["items"][0]["name"] == "DESK tray"
    assert response.json()["items"][0]["price"] == "9.00"
    assert client.get(
        SEARCH, params={"q": "desk", "in_stock": "true", "skip": 2}
    ).json() == {"items": [], "total": 2, "limit": 24, "skip": 2}


@pytest.mark.parametrize(
    "term,expected", [("%", "100% Cotton"), ("_", "Desk_Tray"), ("\\", "C\\ Organizer")]
)
def test_search_treats_like_metacharacters_as_literal(client, db, term, expected):
    db.add_all(
        [
            Product(name="100% Cotton", price=1, stock=1),
            Product(name="Desk_Tray", price=1, stock=1),
            Product(name="C\\ Organizer", price=1, stock=1),
            Product(name="Plain", price=1, stock=1),
        ]
    )
    db.commit()

    result = client.get(SEARCH, params={"q": term}).json()
    assert result["total"] == 1
    assert [product["name"] for product in result["items"]] == [expected]


@pytest.mark.parametrize(
    "sort,expected",
    [
        ("featured", ["Zulu", "alpha", "Alpha"]),
        ("name", ["alpha", "Alpha", "Zulu"]),
        ("price-asc", ["Zulu", "alpha", "Alpha"]),
        ("price-desc", ["alpha", "Alpha", "Zulu"]),
    ],
)
def test_sort_ties_break_by_product_id(client, db, sort, expected):
    db.add_all(
        [
            Product(name="Zulu", price="1.00", stock=1),
            Product(name="alpha", price="2.00", stock=1),
            Product(name="Alpha", price="2.00", stock=1),
        ]
    )
    db.commit()
    assert [
        item["name"]
        for item in client.get(SEARCH, params={"sort": sort}).json()["items"]
    ] == expected


@pytest.mark.parametrize(
    "params",
    [
        {"limit": 0},
        {"limit": 101},
        {"skip": -1},
        {"skip": 100001},
        {"sort": "recent"},
        {"q": "x" * 101},
        {"q": "desk\x00"},
        {"in_stock": "perhaps"},
    ],
)
def test_invalid_catalog_query_is_rejected(client, params):
    assert client.get(SEARCH, params=params).status_code == 422


def test_empty_and_out_of_range_catalog_pages(client, db):
    assert client.get(SEARCH).json() == {
        "items": [],
        "total": 0,
        "limit": 24,
        "skip": 0,
    }
    db.add(Product(name="Pen", price="0.00", stock=0))
    db.commit()
    assert client.get(SEARCH, params={"q": "absent"}).json() == {
        "items": [],
        "total": 0,
        "limit": 24,
        "skip": 0,
    }
    assert client.get(SEARCH, params={"skip": 100}).json() == {
        "items": [],
        "total": 1,
        "limit": 24,
        "skip": 100,
    }


def _categorized(db, name, *, category, price="1.00", stock=1):
    category_id = db.scalar(select(Category.id).where(Category.slug == category))
    return Product(name=name, price=price, stock=stock, category_id=category_id)


def test_category_filter_combines_with_search_stock_and_sort(client, db):
    db.add_all(
        [
            _categorized(db, "Task Light", category="lighting", price="30.00", stock=2),
            _categorized(db, "Desk Lamp", category="lighting", price="10.00", stock=0),
            _categorized(
                db,
                "Felt Desk Mat",
                category="desk-organization",
                price="20.00",
                stock=4,
            ),
        ]
    )
    db.commit()

    lighting = client.get(
        SEARCH,
        params={"category": "lighting", "sort": "price-asc", "in_stock": "true"},
    )
    assert lighting.status_code == 200
    assert [item["name"] for item in lighting.json()["items"]] == ["Task Light"]
    assert lighting.json()["total"] == 1
    assert lighting.json()["items"][0]["category"]["slug"] == "lighting"

    combined = client.get(
        SEARCH,
        params={"category": "lighting", "q": "mat", "sort": "name"},
    )
    assert combined.json() == {"items": [], "total": 0, "limit": 24, "skip": 0}

    everything = client.get(SEARCH)
    assert everything.json()["total"] == 3
    assert client.get(SEARCH, params={"category": "all"}).status_code == 404
    assert client.get(SEARCH, params={"category": "not-a-category"}).status_code == 404
    assert client.get(SEARCH, params={"category": "Lighting"}).status_code == 422
    assert client.get(SEARCH, params={"category": ""}).status_code == 422

    counts = client.get("/api/v1/categories/").json()
    assert [row["slug"] for row in counts] == [
        "desk-organization",
        "ergonomics-and-stands",
        "lighting",
        "writing-and-planning",
        "tech-accessories",
        "workspace-comforts",
        "uncategorized",
    ]
    assert "all" not in {row["slug"] for row in counts}
    by_slug = {row["slug"]: row["count"] for row in counts}
    assert by_slug["lighting"] == 2
    assert by_slug["desk-organization"] == 1
    assert by_slug["uncategorized"] == 0
    filtered = {
        row["slug"]: row["count"]
        for row in client.get(
            "/api/v1/categories/", params={"q": "mat", "in_stock": "true"}
        ).json()
    }
    assert filtered["desk-organization"] == 1
    assert filtered["lighting"] == 0


def test_category_page_is_independent_of_other_categories(client, db):
    db.add_all(
        _categorized(db, f"Lamp {number}", category="lighting") for number in range(3)
    )
    db.add(_categorized(db, "Mat", category="desk-organization"))
    db.commit()
    page = client.get(SEARCH, params={"category": "lighting", "limit": 2, "skip": 2})
    assert page.status_code == 200
    assert page.json()["total"] == 3
    assert [item["name"] for item in page.json()["items"]] == ["Lamp 2"]


def test_maximum_page_and_blank_search(client, db):
    db.add_all(Product(name=f"Item {n}", price="1.20", stock=1) for n in range(101))
    db.commit()
    result = client.get(SEARCH, params={"q": "   ", "limit": 100}).json()
    assert result["total"] == 101
    assert result["limit"] == len(result["items"]) == 100
    assert all(item["price"] == "1.20" for item in result["items"])
    assert all("reserved_stock" not in item for item in result["items"])
    assert client.get(SEARCH, params={"skip": 100000}).json() == {
        "items": [],
        "total": 101,
        "limit": 24,
        "skip": 100000,
    }
