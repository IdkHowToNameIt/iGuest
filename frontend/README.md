# Frontend — iGuest SPA

React 19 + Vite single-page app with three surfaces:

| Route | Surface | Notes |
|-------|---------|-------|
| `/` | Public landing | Bilingual IT/EN marketing page + "book a visit" form |
| `/c/:token` | Guest chat | Opened via the capability link, no login |
| `/admin/*` | Admin panel | Login required, reachable by URL only |
| `/host/*` | Host portal | Login required, structure-scoped, read-only docs |

```bash
npm install
npm run dev     # dev server on http://localhost:5173
npm run build   # production bundle in dist/
npm run lint    # oxlint
```

`VITE_BACKEND_URL` (in `.env`) sets the API base URL; it defaults to
`http://localhost:8000` when unset. See the root [`README.md`](../README.md) for
the full setup, the Docker workflow and the API overview.
