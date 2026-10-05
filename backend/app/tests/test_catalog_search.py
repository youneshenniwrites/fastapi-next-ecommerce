"""Public catalog queries against disposable SQLite and CI PostgreSQL databases."""

import pytest

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
