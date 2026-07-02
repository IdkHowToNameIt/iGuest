"""
Italian administrative geography (regions → provinces → cities).

Backed by a static dataset (``app/data/geo_it.json``, derived from the public
ISTAT comuni list) so there is no external dependency and no cost. The full
dataset (~7.9k cities) is loaded once and cached; the API exposes it as cascading
slices so the frontend only ever fetches the level it needs — keeping the SPA
bundle free of the bulky city list.
"""

import json
from functools import lru_cache
from pathlib import Path

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "geo_it.json"


@lru_cache(maxsize=1)
def _data() -> dict[str, dict[str, list[str]]]:
    """The nested region → province → [city] mapping (loaded once)."""
    with _DATA_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def list_regions() -> list[str]:
    return sorted(_data().keys())


def list_provinces(region: str | None = None) -> list[str]:
    """Provinces in ``region``; all provinces (deduplicated) when region is None."""
    data = _data()
    if region:
        return sorted(data.get(region, {}).keys())
    return sorted({prov for provs in data.values() for prov in provs})


def list_cities(province: str | None = None) -> list[str]:
    """Cities in ``province``; all cities when province is None (rarely needed)."""
    data = _data()
    if province:
        for provs in data.values():
            if province in provs:
                return list(provs[province])  # already sorted at build time
        return []
    return sorted({city for provs in data.values() for cities in provs.values() for city in cities})
