# Sample manuals (demo data)

These files are the fictional manuals of **Casa Sole**, a small B&B in Florence
used as the demo property. They exist so you can try the RAG pipeline — and the
admin/host/guest UI — without inventing content first.

```
samples/manuals/casa-sole/
├── house-rules.it.md       # structure scope  → shared by every unit
├── local-guide.it.md       # structure scope  → restaurants, transport, emergencies
├── suite-giardino.it.md    # unit scope       → "Suite Giardino" (Italian)
└── olive-room.en.md        # unit scope       → "Camera Oliva" (English)
```

The manuals are deliberately written in two languages: it lets you check that a
question in Italian about the English manual (or vice versa) is still answered
correctly, because the prompt tells the model to read a foreign-language context
and reply in the guest's language.

The documents are Markdown on purpose: they are easy to read and edit, and the
ingestion pipeline treats `.md` as plain text (no PDF parsing needed to try the
demo). You can upload PDF/DOCX versions later from the admin panel — same
result, just a different converter.

## Load them

From the repository root, with the database running:

```bash
docker compose exec backend python scripts/seed_demo.py --reset
```

or, running the backend locally:

```bash
cd backend
python scripts/seed_demo.py --reset
```

The script creates the structure, both units, ingests these four files and prints
a guest chat link. Add `--host-email you@example.com` to also create a host
account for the structure (the temporary password is printed once).

Everything here is fictional — names, phone numbers, Wi-Fi passwords and prices
are demo values, safe to publish.
