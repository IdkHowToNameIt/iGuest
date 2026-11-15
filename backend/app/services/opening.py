"""
Opening message + privacy notice for the guest chat.

The opening screen shows, per the project rules (docs/ARCHITECTURE.md):
  - a greeting in the structure's country_language,
  - the same greeting in English (shown separately),
  - a note that the bot auto-detects the guest's preferred language,
  - a short privacy notice (an AI provider processes messages; retention; contact).

We keep a small localized catalog for common OTA languages and fall back to
English text when the country language isn't covered — this avoids an extra
LLM call just to render the welcome screen (budget 0, instant load).
"""

from dataclasses import dataclass

# Greeting per language code
_GREETINGS: dict[str, str] = {
    "en": "Hello! I'm the virtual assistant for your accommodation. Ask me anything about your stay.",
    "it": "Ciao! Sono l'assistente virtuale del tuo alloggio. Chiedimi qualsiasi cosa sul tuo soggiorno.",
    "es": "¡Hola! Soy el asistente virtual de tu alojamiento. Pregúntame lo que quieras sobre tu estancia.",
    "fr": "Bonjour ! Je suis l'assistant virtuel de votre logement. Posez-moi toutes vos questions sur votre séjour.",
    "de": "Hallo! Ich bin der virtuelle Assistent für Ihre Unterkunft. Fragen Sie mich alles zu Ihrem Aufenthalt.",
    "pt": "Olá! Sou o assistente virtual do seu alojamento. Pergunte-me qualquer coisa sobre a sua estadia.",
}

# "We auto-detect your language" note per language code
_LANGUAGE_NOTES: dict[str, str] = {
    "en": "You can write in any language — I'll automatically reply in the language you use.",
    "it": "Puoi scrivere in qualsiasi lingua: rileverò automaticamente la tua lingua e risponderò in quella.",
    "es": "Puedes escribir en cualquier idioma: detectaré tu idioma automáticamente y responderé en él.",
    "fr": "Vous pouvez écrire dans n'importe quelle langue : je la détecte automatiquement et je réponds dans cette langue.",
    "de": "Sie können in jeder Sprache schreiben — ich erkenne sie automatisch und antworte in derselben Sprache.",
    "pt": "Pode escrever em qualquer idioma: deteto automaticamente o seu idioma e respondo no mesmo.",
}

# Privacy notice template per language code; {retention} and {contact} are filled in
_PRIVACY_NOTICES: dict[str, str] = {
    "en": ("Privacy: your messages are processed by an AI provider (Google Gemini) to generate "
           "answers. Conversations are kept for {retention} days and then deleted automatically. "
           "We never ask for personal data. For anything else, contact: {contact}"),
    "it": ("Privacy: i tuoi messaggi sono elaborati da un provider AI (Google Gemini) per generare "
           "le risposte. Le conversazioni sono conservate per {retention} giorni e poi cancellate "
           "automaticamente. Non ti chiediamo mai dati personali. Per altro, contatta: {contact}"),
    "es": ("Privacidad: tus mensajes son procesados por un proveedor de IA (Google Gemini) para "
           "generar respuestas. Las conversaciones se conservan {retention} días y luego se eliminan "
           "automáticamente. Nunca pedimos datos personales. Para lo demás, contacta: {contact}"),
    "fr": ("Confidentialité : vos messages sont traités par un fournisseur d'IA (Google Gemini) pour "
           "générer les réponses. Les conversations sont conservées {retention} jours puis supprimées "
           "automatiquement. Nous ne demandons jamais de données personnelles. Sinon, contactez : {contact}"),
    "de": ("Datenschutz: Ihre Nachrichten werden von einem KI-Anbieter (Google Gemini) verarbeitet, um "
           "Antworten zu erzeugen. Unterhaltungen werden {retention} Tage gespeichert und dann "
           "automatisch gelöscht. Wir fragen nie nach persönlichen Daten. Sonst kontaktieren Sie: {contact}"),
    "pt": ("Privacidade: as suas mensagens são processadas por um fornecedor de IA (Google Gemini) para "
           "gerar respostas. As conversas são mantidas {retention} dias e depois eliminadas "
           "automaticamente. Nunca pedimos dados pessoais. Para o resto, contacte: {contact}"),
}

# Notice that access is temporary: the link is revoked and the chat (with its
# history) is deleted at the end of the stay.
_STAY_NOTICES: dict[str, str] = {
    "en": ("Note: this chat is temporary. Your access will be revoked and the whole "
           "conversation, including its history, will be deleted at the end of your stay."),
    "it": ("Nota: questa chat è temporanea. L'accesso verrà revocato e l'intera "
           "conversazione, cronologia inclusa, sarà eliminata al termine del soggiorno."),
    "es": ("Nota: este chat es temporal. Tu acceso será revocado y toda la conversación, "
           "incluido su historial, se eliminará al final de tu estancia."),
    "fr": ("Remarque : ce chat est temporaire. Votre accès sera révoqué et toute la "
           "conversation, y compris son historique, sera supprimée à la fin de votre séjour."),
    "de": ("Hinweis: Dieser Chat ist temporär. Ihr Zugang wird widerrufen und die gesamte "
           "Unterhaltung samt Verlauf wird am Ende Ihres Aufenthalts gelöscht."),
    "pt": ("Nota: este chat é temporário. O seu acesso será revogado e toda a conversa, "
           "incluindo o histórico, será eliminada no final da sua estadia."),
}

_FALLBACK = "en"


@dataclass
class Opening:
    primary_language: str
    primary_message: str
    english_message: str
    language_note: str
    privacy_notice: str
    stay_notice: str


def _normalize_lang(code: str) -> str:
    """Reduce 'it-IT' / 'IT' to a catalog key like 'it'; fall back to English."""
    base = (code or "").strip().lower().split("-")[0].split("_")[0]
    return base if base in _GREETINGS else _FALLBACK


def build_opening(
    country_language: str,
    owner_contact: str,
    retention_days: int,
    custom_message: str | None = None,
) -> Opening:
    """Build the bilingual opening payload for a structure's country language.

    ``custom_message``, when set, is the structure's own welcome message
    (configured by the admin) and replaces the default catalog greeting.
    """
    lang = _normalize_lang(country_language)

    primary_message = custom_message.strip() if custom_message and custom_message.strip() else _GREETINGS[lang]
    english_message = _GREETINGS[_FALLBACK]
    language_note = _LANGUAGE_NOTES[lang]
    privacy_notice = _PRIVACY_NOTICES[lang].format(
        retention=retention_days, contact=owner_contact
    )

    return Opening(
        primary_language=lang,
        primary_message=primary_message,
        english_message=english_message,
        language_note=language_note,
        privacy_notice=privacy_notice,
        stay_notice=_STAY_NOTICES[lang],
    )
