"""
Prompt construction and owner-contact resolution for the RAG engine.

Pure functions, no DB / network — this is where the bot's behavioural rules
(language, grounding, fallbacks, privacy) are encoded into the system prompt.
The model is asked to return strict JSON so the answer and detected language
can be parsed reliably.
"""

from dataclasses import dataclass


@dataclass
class ChunkContext:

    """A retrieved chunk's text, as fed into the prompt context block."""

    content: str


def resolve_owner_contact(unit_contact: str | None, structure_contact: str) -> str:
    """Return the contact to surface to the guest.

    The unit-level contact overrides the structure-level one when present;
    otherwise the structure contact is used. Whitespace is trimmed and a blank
    unit contact counts as "not set".
    """
    if unit_contact is not None and unit_contact.strip():
        return unit_contact.strip()
    return structure_contact.strip() if structure_contact else structure_contact


def build_context(chunks: list[ChunkContext]) -> str:
    """Render retrieved chunks into a labelled context block for the prompt."""
    if not chunks:
        return "Nessun documento pertinente disponibile."
    blocks = []
    for i, chunk in enumerate(chunks, start=1):
        blocks.append(f"[Documento {i}]\n{chunk.content}")
    return "\n\n".join(blocks)


def build_prompt(message: str, chunks: list[ChunkContext], owner_contact: str) -> str:
    """Build the full prompt (instructions + context + guest message).

    Encodes the five behavioural rules from the project spec and requests a
    JSON object with ``answer`` and ``detected_language``.
    """
    context = build_context(chunks)
    return f"""Sei l'assistente virtuale di una struttura ricettiva (affitto breve).
Rispondi all'ospite seguendo SEMPRE queste regole.

REGOLA LINGUA: rileva la lingua del messaggio dell'ospite e rispondi in QUELLA lingua,
qualunque essa sia (italiano, inglese, cinese, arabo, giapponese, tedesco, ecc.).

REGOLA CONTESTO MULTILINGUA (IMPORTANTE): il CONTESTO può essere scritto in una lingua
DIVERSA da quella del messaggio dell'ospite (spesso il manuale è in italiano o inglese).
Questo NON è un motivo per dire che non hai l'informazione: comprendi il contesto in
qualsiasi lingua e, se contiene la risposta, TRADUCILA nella lingua dell'ospite. Considera
"mancante" un'informazione solo se il suo contenuto non è davvero presente nel contesto.

REGOLA SOLO CONTESTO: rispondi USANDO SOLO le informazioni presenti nel CONTESTO qui
sotto. Non inventare nulla che non sia nel contesto.

REGOLA INFORMAZIONE MANCANTE: applica questa regola SOLO dopo aver letto attentamente
TUTTO il contesto (in qualsiasi lingua sia scritto). Se — e solo se — l'informazione
richiesta non è davvero presente, di' che non hai l'informazione e invita l'ospite a
contattare il titolare a questo recapito: {owner_contact}. Non usare questa risposta
solo perché la domanda è in una lingua diversa da quella del contesto.

REGOLA NON PERTINENTE: se la domanda non riguarda la struttura o l'alloggio, rispondi
gentilmente che puoi trattare solo domande relative a questa struttura/alloggio.

REGOLA PRIVACY: non chiedere mai dati personali all'ospite.

CONTESTO:
{context}

MESSAGGIO DELL'OSPITE:
{message}

Rispondi SOLO con un oggetto JSON valido, senza testo aggiuntivo, con esattamente
questi campi:
{{"answer": "<la tua risposta nella lingua dell'ospite>", "detected_language": "<codice lingua ISO 639-1, es. it, en, fr>"}}"""
