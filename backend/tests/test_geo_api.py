"""
Tests for the geo reference API (static dataset, no DB, no auth).
"""

import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

client = TestClient(app)


def test_regions():
    r = client.get("/api/geo/regions")
    assert r.status_code == 200
    regions = r.json()
    assert len(regions) == 20  # Italian regions
    assert "Lazio" in regions
    assert regions == sorted(regions)


def test_provinces_of_region():
    r = client.get("/api/geo/provinces", params={"region": "Lazio"})
    assert r.status_code == 200
    assert "Roma" in r.json()


def test_provinces_all_when_no_region():
    r = client.get("/api/geo/provinces")
    assert r.status_code == 200
    assert len(r.json()) == 107  # Italian provinces


def test_cities_of_province():
    r = client.get("/api/geo/cities", params={"province": "Roma"})
    assert r.status_code == 200
    cities = r.json()
    assert "Roma" in cities
    assert len(cities) > 1


def test_cities_unknown_province_empty():
    r = client.get("/api/geo/cities", params={"province": "Nowhere"})
    assert r.status_code == 200
    assert r.json() == []
