"""
Geo reference API — Italian regions / provinces / cities.

Public (no auth): this is static reference data used to populate the admin's
cascading location selectors and validate structure locations. Cascading:

  GET /api/geo/regions
  GET /api/geo/provinces?region=Lazio
  GET /api/geo/cities?province=Roma
"""

from fastapi import APIRouter

from app.services import geo

router = APIRouter(prefix="/api/geo", tags=["geo"])


@router.get("/regions", response_model=list[str])
def get_regions():
    return geo.list_regions()


@router.get("/provinces", response_model=list[str])
def get_provinces(region: str | None = None):
    return geo.list_provinces(region)


@router.get("/cities", response_model=list[str])
def get_cities(province: str | None = None):
    return geo.list_cities(province)
