# iGuest

Chatbot RAG multilingua per ospiti di affitti brevi (Airbnb, Booking, â€¦).
L'ospite apre un link univoco, fa domande sull'alloggio e il bot risponde **solo**
attingendo al manuale digitale di quella struttura, nella lingua dell'ospite.
Un pannello admin gestisce strutture, unitÃ , documenti, link e conversazioni.

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Database**: PostgreSQL + `pgvector` (dati relazionali + embeddings insieme)
- **AI**: Google Gemini (embeddings + generazione) via Google AI Studio
- **Frontend**: React + Vite (chat ospite + pannello admin)

---

## 1. Prerequisiti

| Strumento | Versione | Note |
|-----------|----------|------|
| Docker Desktop | ultima | esegue PostgreSQL + pgvector (e, in modalitÃ  consigliata, anche backend e frontend) |
| Python | 3.11+ | testato su 3.14 (serve solo per la modalitÃ  locale) |
| Node.js | 18+ | per il frontend (serve solo per la modalitÃ  locale) |
| Chiave API Gemini | â€” | gratuita su <https://aistudio.google.com/> |

> Tutte le dipendenze sono gratuite / open-source. L'unico servizio esterno Ã¨
> Google Gemini (il piano gratuito Ã¨ sufficiente per una demo).

---

## 2. Configura l'ambiente (serve per entrambe le modalitÃ )

```bash
# config backend â€” imposta la chiave Gemini e le credenziali admin
cp backend/.env.example backend/.env

# config frontend â€” lascia il default se il backend Ã¨ sulla :8000
cp frontend/.env.example frontend/.env
```

Modifica `backend/.env` e imposta almeno:

- `GEMINI_API_KEY` â€” la tua chiave di Google AI Studio (**obbligatoria** per embeddings/risposte)
- `ADMIN_USERNAME` / `ADMIN_PASSWORD` â€” le credenziali admin (cambia i default!)
- `ADMIN_JWT_SECRET` â€” una stringa lunga e casuale, es.
  `python -c "import secrets; print(secrets.token_urlsafe(48))"`

> Lascia `POSTGRES_HOST=localhost` in `backend/.env`. In modalitÃ  Docker Compose
> lo sovrascrive automaticamente a `db` â€” non serve modificarlo.

---

## 3. Avvia tutto con Docker (consigliato â€” un solo comando)

Dalla radice del repository:

```bash
docker compose up --build
```

Tutto qui. Compose costruisce e avvia **tre servizi**:

| Servizio | Immagine | Porta | Note |
|----------|----------|-------|------|
| `db` | `pgvector/pgvector:pg16` (scaricata) | 5432 | PostgreSQL + pgvector |
| `backend` | costruita da `backend/Dockerfile` | 8000 | esegue `alembic upgrade head`, poi uvicorn |
| `frontend` | costruita da `frontend/Dockerfile` | 5173 | dev server Vite |

Backend e frontend montano il tuo codice sorgente come volume, quindi **le modifiche
si ricaricano a caldo** senza rebuild: **non devi nÃ© stoppare nÃ© riavviare**, basta
salvare il file. Il rebuild (`--build`) serve **solo** quando cambiano le dipendenze
(`requirements.txt` o `package.json`). Ferma con `Ctrl+C`; `docker compose down`
rimuove i container (aggiungi `-v` per eliminare anche il volume del database).

Una volta avviato:
- Chat ospite: `http://localhost:5173/c/<token>`
- Pannello admin: <http://localhost:5173/admin>
- Portale host: <http://localhost:5173/host>
- Docs API: <http://localhost:8000/docs> Â· health: `GET http://localhost:8000/health`

---

## 4. Alternativa: backend/frontend in locale (DB su Docker)

Preferisci eseguire i processi dell'app sulla tua macchina (es. per un debugger
nativo)? Avvia solo il database su Docker, poi le due app in locale:

```bash
# 4.1 â€” solo database
docker compose up -d db

# 4.2 â€” backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 4.3 â€” frontend (in un secondo terminale)
cd frontend
npm install
npm run dev
```

Stessi URL di sopra (frontend su :5173, backend su :8000).

---

## 5. Primo utilizzo (pannello admin)

1. Apri <http://localhost:5173/admin> â†’ accedi con `ADMIN_USERNAME` / `ADMIN_PASSWORD`.
2. **Crea una struttura**: nome, lingua ospite (BCP-47, es. `it`), recapito del titolare,
   piÃ¹ **posizione** opzionale (regione â†’ provincia â†’ cittÃ , da menu a cascata) e
   **recapiti host** solo-admin (nome / telefono / email â€” per raggiungere il gestore).
3. La pagina strutture Ã¨ una griglia di gestione: **cerca** per nome/cittÃ /provincia/regione
   e **filtra** per regione/provincia/cittÃ  (combinabili). Apri una struttura per modificarne
   dettagli, posizione, recapiti e il **messaggio di benvenuto del bot** (testo libero mostrato
   all'ospite in apertura chat al posto del saluto automatico per lingua; lascialo vuoto per
   usare quello di default).
4. Apri la struttura â†’ **crea un'unitÃ ** (es. "Stanza 1").
5. Carica un documento (il tuo manuale: PDF, DOCX, TXT, MD, HTMLâ€¦) sulla struttura
   (*condiviso*) o su un'unitÃ . Lo stato passa a `processed` una volta suddiviso in chunk
   ed embeddato. Usa **View text** per leggere in-app il testo estratto del documento,
   reso come blocchi formattati e leggibili (paragrafi + titoli in stile Markdown). Il testo
   estratto viene salvato *prima* dell'embedding, cosÃ¬ il manuale resta visualizzabile anche
   se l'indicizzazione fallisce (il documento mostra allora `error` con il motivo, ma resta
   leggibile).
6. **Genera un link ospite** (opzionalmente con una finestra di validitÃ ) â†’ **Copia** il link.
7. Apri il link copiato in un browser per chattare come ospite.
8. Le conversazioni compaiono sotto l'unitÃ ; puoi aprirle ed **eliminare i dati** (GDPR).
   **Revocare un link lo elimina definitivamente** (insieme alla sua chat): sparisce dalla
   lista e il token smette di funzionare (l'ospite vede "link non trovato").
   La pagina dell'unitÃ  mostra le **analytics delle domande**; le **richieste di modifica**
   degli host arrivano nella casella *Change requests* dell'admin (menu in alto), filtrabili
   per stato e per tipo (legate a un documento oppure "other").
9. *(opzionale)* Nella pagina della struttura, **aggiungi un host** (la sua email): una
   password temporanea viene mostrata una sola volta â€” condividila in modo sicuro.

> Il bot risponde esclusivamente in base ai documenti caricati. Se una domanda Ã¨ in tema
> ma non coperta, fornisce il recapito del titolare; le domande fuori tema vengono declinate
> cortesemente.

La schermata di apertura per l'ospite avvisa inoltre che la chat Ã¨ **temporanea**: l'accesso
viene revocato e l'intera conversazione eliminata al termine del soggiorno. Gli ospiti che
tornano rivedono i messaggi precedenti, caricati da `GET /api/guest/{token}/history` â€” questa
cronologia Ã¨ transitoria e sparisce all'eliminazione del link / con la purga di retention.

### Portale host

Un host (creato dall'admin e associato a una **struttura**) accede su `/host` con email +
password temporanea, Ã¨ obbligato a impostare una nuova password al primo accesso, e puÃ² poi
leggere tutta la documentazione della struttura (sola lettura, su tutte le sue unitÃ  â€” con
**View text**, che apre il testo estratto in un pop-up a schermo pieno), vedere FAQ/analytics
e inviare all'admin **richieste di modifica** dei documenti.

Il widget **"What guests ask"** ha una tab **General** (tutta la struttura) piÃ¹ una tab per
ogni unitÃ /stanza, ciascuna con le categorie di domande e il relativo drill-down per singola
domanda. Analytics e FAQ sono ricalcolate automaticamente ogni pochi minuti da uno scheduler
interno al backend (vedi GDPR/operativitÃ  sotto) â€” non serve lanciare nulla a mano.

Le richieste di modifica possono riferirsi a un documento specifico oppure a **"Other"** (un
problema diverso, per cui l'host scrive un titolo). Sono mostrate in due sezioni a scomparsa,
**In progress** e **Resolved**; una volta risolte mostrano la nota lasciata dall'admin,
firmata con il suo nome visualizzato (o "Admin" se non l'ha impostato). Dal tasto
**âš™ Settings** l'host puÃ² **riordinare le sezioni** della dashboard (salvato nel browser),
cambiare la **foto profilo** (cliccaci sopra per vederla ingrandita) e attivare le
**notifiche** quando l'admin risolve una sua richiesta.

### Dati di localizzazione

Regione/provincia/cittÃ  provengono da un dataset geografico italiano statico incluso lato
server (`backend/app/data/geo_it.json`, ~7,9k comuni) ed esposto tramite gli endpoint
pubblici a cascata `GET /api/geo/regions|provinces?region=|cities?province=`. Il frontend
scarica solo la fetta che serve, cosÃ¬ il bundle della SPA resta leggero e non c'Ã¨ inserimento
dati a mano.

---

## 6. Script demo di avvio rapido

Crea una struttura + unitÃ  + link ospite attivo in un colpo solo e stampa l'URL ospite.
**Non** inventa alcun contenuto â€” passi tu i tuoi valori:

```bash
cd backend
python scripts/demo_seed.py \
  --name "My B&B" \
  --country-language it \
  --owner-contact "info@mybnb.example" \
  --unit-name "Room 1" \
  --document /path/to/your/manual.pdf      # opzionale; richiede GEMINI_API_KEY
```

Stampa un link pronto da aprire tipo `http://localhost:5173/c/<token>`.

---

## 7. GDPR / privacy

iGuest Ã¨ progettato attorno alla minimizzazione dei dati:

- **Nessun dato personale Ã¨ richiesto o necessario dagli ospiti.** Sono identificati
  solo dal token anonimo del link â€” niente nome, email o telefono.
- **Avviso privacy nella chat**: la schermata di apertura per l'ospite indica che un
  provider AI (Google Gemini) elabora i messaggi, il periodo di conservazione e il
  recapito del titolare.
- **Retention configurabile**: le conversazioni ricevono un timestamp `delete_after` alla
  creazione (`CONVERSATION_RETENTION_DAYS`, default 30).
- **Cancellazione automatica pianificata**: il backend esegue una purga in background
  all'avvio e ogni `RETENTION_PURGE_INTERVAL_SECONDS` (default: giornaliera). Disattivabile
  con `RETENTION_PURGE_ENABLED=false`. Puoi anche eseguirla manualmente:
  ```bash
  python scripts/purge_conversations.py
  ```
  (o pianificarla via cron / UtilitÃ  di pianificazione).
- **Analytics domande & FAQ**: le domande degli ospiti vengono raggruppate nei temi piÃ¹
  richiesti e alle principali viene generata una risposta, mostrata sia nella chat ospite
  (`GET /api/guest/{token}/faqs`) sia nelle viste analytics admin/host (per struttura e per
  singola unitÃ ). Il ricalcolo gira fuori dal percorso della richiesta, in un loop interno
  al backend avviato all'avvio e ripetuto ogni `FAQ_RECOMPUTE_INTERVAL_SECONDS` (default: 5
  minuti; disattivabile con `FAQ_RECOMPUTE_ENABLED=false`). Puoi anche lanciarlo a mano, ad
  es. subito dopo un giro di test:
  ```bash
  python scripts/recompute_faqs.py            # tutte le unitÃ 
  python scripts/recompute_faqs.py --unit-id <uuid>
  ```
  Il messaggio di ogni ospite viene salvato **prima** di chiamare il modello di generazione,
  cosÃ¬ una domanda non va persa anche se la risposta fallisce (es. rate limit di Gemini) â€”
  resta comunque disponibile per il ricalcolo successivo.
- **Cronologia ospite temporanea**: un ospite che torna puÃ² rileggere i propri messaggi
  (`GET /api/guest/{token}/history`), ma la conversazione Ã¨ transitoria â€” cancellata alla
  revoca del link e dalla purga di retention.
- **Diritto all'oblio**: un admin puÃ² eliminare qualsiasi conversazione e tutti i suoi
  messaggi via `DELETE /api/admin/conversations/{id}` (pulsante nel pannello admin).
  **Revocare un link ospite** (`POST /api/admin/links/{id}/revoke`) elimina definitivamente
  il link e la chat di quella prenotazione: il token smette immediatamente di funzionare.
- Per la produzione, ospita in una regione UE e verifica l'impostazione no-training di
  Gemini / firma il DPA (vedi `CLAUDE.md`).

---

## 8. Eseguire i test

```bash
cd backend
python -m pytest -q
```

I test unit/HTTP girano senza database nÃ© chiave API (i test dipendenti da DB e Gemini
vengono skippati). Per eseguire il flusso completo di integrazione con il Postgres in
esecuzione:

```bash
# Windows PowerShell
$env:RUN_DB_TESTS=1; python -m pytest tests/test_guest_flow_db.py tests/test_admin_flow_db.py -v
# macOS / Linux
RUN_DB_TESTS=1 python -m pytest tests/test_guest_flow_db.py tests/test_admin_flow_db.py -v
```

Frontend:

```bash
cd frontend
npm run build   # validazione type/JSX + bundle
npm run lint
```

---

## 9. Struttura del progetto

```
iGuest/
â”œâ”€â”€ docker-compose.yml          # db + backend + frontend (un solo comando)
â”œâ”€â”€ CLAUDE.md                   # decisioni di progetto (fonte di veritÃ )
â”œâ”€â”€ README.md
â”œâ”€â”€ backend/
â”‚   â”œâ”€â”€ Dockerfile              # immagine backend (uvicorn)
â”‚   â”œâ”€â”€ .env.example
â”‚   â”œâ”€â”€ requirements.txt
â”‚   â”œâ”€â”€ alembic/                # migrazioni
â”‚   â”œâ”€â”€ scripts/
â”‚   â”‚   â”œâ”€â”€ demo_seed.py        # seed di avvio rapido
â”‚   â”‚   â”œâ”€â”€ demo_ingestion.py   # ingestione di un singolo file (demo)
â”‚   â”‚   â”œâ”€â”€ purge_conversations.py  # purga GDPR manuale
â”‚   â”‚   â””â”€â”€ recompute_faqs.py   # ricostruisce analytics domande + risposte FAQ
â”‚   â””â”€â”€ app/
â”‚       â”œâ”€â”€ main.py             # app FastAPI + scheduler di retention e ricalcolo FAQ
â”‚       â”œâ”€â”€ config.py           # impostazioni da env
â”‚       â”œâ”€â”€ models/             # modelli SQLAlchemy
â”‚       â”œâ”€â”€ routers/            # API ospite + admin
â”‚       â””â”€â”€ services/           # ingestion, RAG, links, chat, retention, auth
â””â”€â”€ frontend/
    â”œâ”€â”€ Dockerfile              # immagine frontend dev (dev server Vite)
    â”œâ”€â”€ Dockerfile.prod         # immagine frontend prod (build statica + nginx)
    â”œâ”€â”€ nginx.conf              # config nginx con fallback SPA (profilo "prod")
    â””â”€â”€ src/
        â”œâ”€â”€ pages/ChatPage.jsx  # chat ospite
        â””â”€â”€ admin/              # pannello admin (login + gestione)
```

---

## 10. Note & limitazioni

- **Docker Ã¨ obbligatorio.** Nella modalitÃ  consigliata esegue tutti e tre i servizi; in
  modalitÃ  locale esegue comunque il database (pgvector). Senza un daemon Docker attivo,
  gli endpoint che usano il DB daranno errore.
- I pin delle dipendenze usano `>=` perchÃ© alcuni pacchetti non avevano wheel per Python 3.14.
- Il `package-lock.json` Ã¨ cross-platform (include i binari opzionali di tutte le
  piattaforme), quindi l'immagine Docker del frontend usa `npm ci` per install
  riproducibili. Se aggiungi/aggiorni dipendenze, rigenera il lock con `npm install`
  (npm â‰¥ 10) cosÃ¬ resta completo per Windows e Linux.
- Il frontend Ã¨ una SPA. In sviluppo lo serve Vite; per la **produzione** c'Ã¨ un profilo
  Compose dedicato che builda il bundle statico e lo serve con **nginx** (con il rewrite
  che fa risolvere i deep link `/c/...`, `/admin/...`, `/host/...` su `index.html`):
  ```bash
  docker compose --profile prod up --build frontend-prod
  ```
  Serve il frontend di produzione su <http://localhost:8080> (immagine
  `frontend/Dockerfile.prod`, config `frontend/nginx.conf`). L'URL del backend Ã¨ iniettato
  a build-time tramite l'arg `VITE_BACKEND_URL` (default `http://localhost:8000`).
- L'auth admin Ã¨ un singolo account da `.env` con un JWT â€” pensato per un solo
  amministratore, senza registrazione pubblica.
- **Piano gratuito Gemini**: il tier free ha un limite giornaliero basso di chiamate a
  `generate_content` (es. 20/giorno su `gemini-2.5-flash` al momento della stesura). Superato
  il limite, la chat ospite risponde con "assistente momentaneamente occupato" (HTTP 503) e le
  risposte FAQ del ricalcolo automatico falliscono (loggato, non blocca il resto): i conteggi
  di analytics/cluster restano comunque corretti perchÃ© il messaggio dell'ospite Ã¨ salvato
  prima della chiamata al modello. Il limite si resetta ogni 24h o passando a un piano a
  pagamento.

---

## âš ï¸ TODO / REMINDER â€” moduli `ingestion` e `rag` da rivedere

I moduli **`backend/app/services/ingestion/`** (conversione â†’ chunking â†’ embedding â†’
pipeline) e **`backend/app/services/rag/`** (prompt, retrieval, embedding query,
generation, engine) sono stati creati come **prima versione di prova** per sbloccare
l'avvio dell'app e far passare i test. **Vanno adattati alle nostre esigenze** prima
di considerarli definitivi. Punti aperti da rivedere insieme:

- **Prompt RAG** (`rag/prompt.py`): tono, formato della risposta e regole di
  comportamento sono una bozza â€” affinarli sui casi reali.
- **Chunking** (`ingestion/chunking.py`): strategia a finestra su caratteri; valutare
  uno split semantico/per paragrafi e i valori di `CHUNK_SIZE` / `CHUNK_OVERLAP`.
- **Formati supportati** (`ingestion/conversion.py`): txt/md/csv/html/pdf/docx; OCR
  non gestito (le immagini sollevano `OCRRequiredError`) â€” decidere se serve.
- **Embedding / Generation Gemini** (`ingestion/embedding.py`, `rag/generation.py`):
  modelli, `task_type`, batch size, temperatura e parsing JSON della risposta da
  validare sul campo (richiedono `GEMINI_API_KEY`).
- **Retrieval** (`rag/retrieval.py`): scope unitÃ  + struttura via cosine distance;
  valutare una soglia di similaritÃ  minima e un indice pgvector per le performance.

> Nota: i test che esercitano embedding/generazione "live" restano skippati finchÃ©
> `GEMINI_API_KEY` non Ã¨ configurata in `backend/.env`.
