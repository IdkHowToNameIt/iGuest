# Architettura — iGuest

Documento di riferimento del progetto: obiettivi, modello dati, pipeline RAG,
superfici API e decisioni prese. Aggiornalo quando cambi un comportamento
strutturale (non per modifiche cosmetiche).

## Obiettivo

Chatbot RAG multilingua per ospiti di affitti brevi. L'ospite riceve dal gestore
un link univoco, apre la chat e fa domande sull'alloggio; il bot risponde **solo**
attingendo al manuale digitale della struttura/unità, nella lingua dell'ospite.
Un pannello admin gestisce strutture, unità, documenti, link, host e richieste;
un portale host dà al gestore una vista in sola lettura della documentazione.

Vincoli di progetto: budget 0 (solo strumenti gratuiti/open source), nessun dato
personale richiesto agli ospiti, risposte verificabili (niente invenzioni).

## Stack

| Livello | Tecnologia |
|---------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, pydantic-settings |
| Database | PostgreSQL 16 + `pgvector` (dati relazionali ed embedding nello stesso DB) |
| AI | Google Gemini via Google AI Studio: `gemini-embedding-001` (embedding) e `gemini-3.5-flash` (generazione) |
| Frontend | React 19 + Vite (SPA), React Router, CSS custom |
| Dev/ops | Docker Compose (db + backend + frontend dev/prod), nginx per la build statica |

## Flusso di una domanda

```mermaid
flowchart LR
  G[Ospite<br/>link /c/token] -->|POST /api/guest/{token}/chat| C[chat service]
  C -->|risolve il token| L[(guest_link)]
  C -->|salva subito il messaggio| M[(message)]
  C --> R[RAG engine]
  R -->|embed query 768d| E[Gemini embeddings]
  R -->|cosine distance su unit + structure| V[(document_chunk)]
  R -->|prompt: regole + contesto| A[Gemini generation]
  A --> C
  C -->|salva risposta + lingua| M
  C --> G
```

Il messaggio dell'ospite viene salvato **prima** della chiamata al modello: se la
generazione fallisce (rate limit, rete), la domanda resta registrata e viene
usata dal ricalcolo delle analytics/FAQ.

## Modello dati

| Tabella | Ruolo |
|---------|-------|
| `structure` | Struttura (B&B, appartamento): lingua, recapito titolare, posizione, contatti admin-only, messaggio di benvenuto |
| `unit` | Unità affittabile di una struttura (stanza o appartamento intero) |
| `document` | Manuale caricato, con scope `structure` o `unit`; conserva `extracted_text` e lo stato di ingestion |
| `document_chunk` | Finestra di testo del documento + embedding `vector(768)`, con `structure_id` e `unit_id` denormalizzati |
| `guest_link` | Capability URL: token casuale (256 bit), validità opzionale, un link per prenotazione |
| `conversation` / `message` | Chat legata al link (non all'ospite): `delete_after` per la retention |
| `host` | Account host scoped alla struttura (bcrypt, cambio password obbligatorio al primo accesso) |
| `admin_user` / `admin_profile` | Account admin aggiuntivi (DB) + nome/avatar del profilo |
| `question_cluster` | Domande raggruppate semanticamente, da cui nascono le FAQ |
| `document_change_request` | Richieste di modifica host → admin |
| `visit_request` | Lead dal form "Prenota una visita" della landing |

## Ingestion (documento → chunk → embedding)

`app/services/ingestion/`

1. **conversion.py** — estrae testo da `txt/md/csv/html/pdf/docx`. Immagini e PDF
   senza text layer sollevano `OCRRequiredError` (OCR fuori scope). Il testo
   estratto viene salvato *prima* dell'embedding, così il manuale resta leggibile
   anche se l'indicizzazione fallisce.
2. **chunking.py** — finestre di `CHUNK_SIZE` caratteri con `CHUNK_OVERLAP` di
   sovrapposizione; il taglio preferisce i confini di paragrafo/frase, poi lo
   spazio bianco, per non spezzare concetti a metà.
3. **embedding.py** — `gemini-embedding-001` con `output_dimensionality=768` e
   `task_type=RETRIEVAL_DOCUMENT`, in batch (`EMBEDDING_BATCH_SIZE`).
4. **pipeline.py** — orchestra i passi e aggiorna lo stato del documento
   (`pending` → `processed` / `error` con motivazione).

## Retrieval e prompt

`app/services/rag/`

- **retrieval.py** — dual-scope: per un'unità si cercano i suoi chunk **più**
  quelli della struttura (`unit_id IS NULL`), ordinati per distanza coseno. I
  chunk oltre `RAG_MAX_DISTANCE` vengono scartati: sotto una certa soglia il
  contesto è rumore e il modello rischia risposte fuori tema.
- **prompt.py** — regole di comportamento in italiano, contesto numerato,
  richiesta di output JSON (`answer`, `detected_language`). Regole chiave:
  lingua dell'ospite, solo contesto, contesto in lingua diversa va tradotto,
  informazione mancante → recapito del titolare, domande fuori tema → rifiuto
  cortese, mai chiedere dati personali.
- **engine.py** — orchestrazione (unità → embedding query → retrieval → prompt →
  generazione); embedding e generazione sono iniettabili per i test.
- **generation.py** — chiamata a `gemini-3.5-flash`, timeout per richiesta e parsing
  tollerante del JSON
  (accetta anche output racchiuso in un fence markdown).

## API

| Prefisso | Auth | Contenuto |
|----------|------|-----------|
| `/api/guest/{token}/*` | capability token | opening, history, faqs, chat |
| `/api/admin/*` | JWT admin | login, strutture, unità, documenti, link, conversazioni, host, account admin, richieste, analytics, profilo, statistiche |
| `/api/host/*` | JWT host | login, documenti della struttura, FAQ/analytics, richieste di modifica, profilo |
| `/api/public/*` | nessuna | form "prenota una visita" |
| `/api/geo/*` | nessuna | regioni/province/città italiane per i filtri admin |

La documentazione interattiva è su `/docs`.

## Privacy e GDPR

- L'ospite non fornisce dati personali: è identificato dal token del link.
- Avviso privacy nella schermata iniziale della chat (provider AI, retention,
  recapito del titolare).
- `CONVERSATION_RETENTION_DAYS` (default 30) imposta `delete_after` alla nascita
  della conversazione; una purga in background gira all'avvio e ogni
  `RETENTION_PURGE_INTERVAL_SECONDS`.
- Revocare un link lo elimina (insieme alla chat); l'admin può cancellare una
  conversazione via API e dalla UI.
- Nessun training sui dati: usare le impostazioni Gemini no-training/DPA in
  produzione e ospitare in UE.

## Analytics e FAQ

- Le domande degli ospiti sono raggruppate per similarità in cluster
  (`FAQ_QUESTION_DISTANCE`, `FAQ_CATEGORY_DISTANCE`); i cluster principali
  diventano FAQ con una risposta generata.
- Il ricalcolo gira nel backend ogni `FAQ_RECOMPUTE_INTERVAL_SECONDS` (default 5
  minuti), fuori dal percorso della richiesta; eseguibile a mano con
  `scripts/recompute_faqs.py`.

## Sicurezza

- Link ospite: token casuale da `secrets.token_urlsafe(32)`, nessun ID
  sequenziale esposto.
- Admin: singolo account da `.env` più account DB opzionali, JWT firmato con
  `ADMIN_JWT_SECRET`, scadenza configurabile.
- Host: password bcrypt, verifica a tempo costante anche su email inesistente,
  cambio password obbligatorio al primo accesso.
- Upload: limite di dimensione (`MAX_DOCUMENT_UPLOAD_BYTES`) e validazione del
  tipo per gli avatar.
- I file `.env` non sono mai committati; `.env.example` documenta tutte le chiavi.

## Decisioni e compromessi

- **pgvector nello stesso Postgres** invece di un vector DB dedicato: una sola
  dipendenza, join relazionali semplici, nessun costo aggiuntivo.
- **Nessun OCR**: i PDF scansionati vengono rifiutati con un errore esplicito
  invece di produrre testo vuoto.
- **Snapshot del testo estratto** nel DB: la UI legge il manuale senza riaprire
  il file e senza dipendere dallo storage degli upload.
- **Un solo admin "storico" da `.env`** più account DB: semplicità per la demo,
  senza introdurre un sistema di ruoli completo.
- **Chunking a finestre con confini semantici leggeri**: buon compromesso per un
  MVP; un splitter per paragrafi/token con valutazione quantitativa è il passo
  successivo.
- **Frontend SPA senza libreria di stato**: dati caricati per pagina via REST;
  sufficiente per la dimensione dell'app.
