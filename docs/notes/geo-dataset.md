---
name: geo-dataset
description: How Italian region/province/city data is sourced and served (budget-0, bundle-light)
metadata:
  type: reference
---

Italian administrative geography for the admin structures filters/search.

- **Source:** the public ISTAT-derived comuni list (`matteocontrini/comuni-json`),
  fetched once and transformed into a compact nested JSON
  `backend/app/data/geo_it.json` (region → province → [cities]): 20 regions /
  107 provinces / ~7.9k comuni, ~110 KB.
- **Served** by `app/services/geo.py` (loaded once via `lru_cache`) through the
  public cascading endpoints in `app/routers/geo.py`:
  `GET /api/geo/regions`, `/provinces?region=`, `/cities?province=`.
- **Why this shape:** keeps the heavy city list server-side so the SPA bundle is
  unaffected; the frontend (`frontend/src/geoApi.js` + `components/GeoSelect.jsx`)
  fetches only the slice it needs. Picking region resets province+city, etc.
- To refresh the data, re-fetch the source and re-run the same transform (group by
  `regione.nome` → `provincia.nome` → sorted unique `nome`).

Related: [[phase3-host-portal]].
