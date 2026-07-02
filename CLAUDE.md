# Progetto: Assistente virtuale multilingua per ospiti OTA (MVP)

## Cosa stiamo costruendo
Un chatbot RAG multilingua per ospiti di affitti brevi (Airbnb, Booking, ecc.).
L'ospite accede tramite un link univoco ricevuto dal gestore e fa domande sulla
struttura/alloggio; il bot risponde solo con le informazioni del manuale digitale
di quella specifica unità. Esiste un'interfaccia admin per gestire strutture,
unità, documenti, link e conversazioni.

## Stack
- Backend: Python 3.11+, FastAPI, SQLAlchemy, Alembic.
- DB: PostgreSQL + estensione pgvector (relazionale + embeddings insieme). Docker in locale.
- AI: Google Gemini via Google AI Studio (chiave in .env) per generazione + embeddings.
- Frontend: React + Vite (JavaScript), processo separato, comunica col backend via REST.
- Budget 0: usare solo strumenti gratuiti/open source. Niente servizi a pagamento.

## Modello dati (concetti chiave)
- Structure (struttura) -> Unit (unità affittabile: stanza singola o appartamento intero).
- I documenti hanno uno scope: livello "structure" (condivisi tra tutte le unità) o
  livello "unit" (specifici). Il retrieval per un'unità usa i chunk di quell'unità
  PIÙ quelli della sua struttura.
- L'identità dell'ospite arriva dal token del link (capability URL), non dalla sessione.

## Regole di comportamento del bot
- Risponde nella lingua del messaggio dell'ospite (auto-detect).
- Risponde SOLO con informazioni presenti nei documenti dell'unità/struttura.
- Domanda inerente la struttura ma senza risposta nei documenti -> fornisce il
  recapito del titolare (campo owner_contact).
- Domanda non inerente la struttura -> risponde che può trattare solo domande
  relative alla struttura.
- Non chiede mai dati personali all'ospite.

## GDPR / privacy (vincolante)
- Dato minimo: l'ospite è identificato solo dal token, nessun nome/PII richiesto.
- Avviso privacy nella chat ospite (un provider AI elabora i messaggi, tempi di
  conservazione, recapito).
- Conversazioni conservate con cancellazione automatica configurabile (default 30 giorni).
- L'admin può cancellare i dati di una prenotazione/conversazione (diritto all'oblio).

## Convenzioni
- Repo con due cartelle: backend/ e frontend/.
- Tutta la configurazione sensibile in .env (mai hardcoded). Fornire .env.example.
- Codice commentato dove la logica non è ovvia. README con istruzioni di avvio locale.
- Non inventare contenuti dei manuali né recapiti: sono inseriti dall'utente.
