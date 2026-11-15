---
name: phase3-host-portal
description: Status of the Phase 3 host-portal / FAQ-analytics feature and what remains
metadata:
  type: project
---

Phase 3 adds **host accounts**, **question analytics / FAQ**, and **document change requests**.

As of 2026-06-29 the **backend is complete**: models (`Host`, `QuestionCluster`,
`DocumentChangeRequest`), migration `0002_host_analytics_faq`, services
(`host_auth` using the `bcrypt` lib directly — *not* passlib, which is broken
against bcrypt 5.x — and `faq/` clustering + analytics), the host router
(`/api/host/*`), admin endpoints (hosts / change-requests / analytics), the guest
FAQ menu (`GET /api/guest/{token}/faqs`), and `scripts/recompute_faqs.py` (off
the request path). All backend tests pass.

**Frontend is now complete too** (built green with `npm run build`): admin
UnitDetailPage gained Hosts + Analytics sections; a global `/admin/change-requests`
inbox (top-nav link); a full host portal under `/host/*` (`src/host/` — own
`hostApi.js` + `hostAuth.jsx` with forced password change on first login,
dashboard with read-only docs / FAQ / analytics / change-request submission); and
the guest chat shows FAQ suggestion chips. Host portal reuses `admin/admin.css`.

Phase 3 is feature-complete end to end.

**Phase 4 (2026-06-30)** extended it:
- **Bug fixed:** migration `0002` had never been applied (DB was at `0001`), so
  `/units/{id}/hosts` and `/units/{id}/analytics` returned 500 — which the browser
  surfaced as "could not reach the server" because unhandled 500s lack CORS headers.
  Fix = `alembic upgrade head`. Lesson: a 500 masquerading as a network error usually
  means a missing migration.
- **Hosts are now structure-scoped** (migration `0003`: `Host.unit_id`→`structure_id`,
  `DocumentChangeRequest.unit_id`→`structure_id`). Host portal shows the whole
  structure's docs/FAQ/analytics. Admin host management moved to the structure page.
- **Structure** gained `region/province/city` + admin-only `contact_name/phone/email`.
- **Admin gestionale**: structures card grid with search (name/city/province/region) +
  cascading region/province/city filters (combinable). See [[geo-dataset]].
- **Document text viewing**: `Document.extracted_text` (already stored at ingestion) is
  exposed via `/api/admin/documents/{id}/content` and `/api/host/documents/{id}/content`;
  shared `DocumentText` component on admin + host.
- Backend: 97 tests pass + 3 DB-flow skipped; frontend builds clean.
