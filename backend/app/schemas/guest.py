"""Request/response schemas for the guest-facing API."""

import uuid

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    # Only the message — never any personal data about the guest.
    message: str = Field(..., min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    answer: str
    detected_language: str | None = None


class OpeningResponse(BaseModel):
    primary_language: str
    primary_message: str
    english_message: str
    language_note: str
    privacy_notice: str
    stay_notice: str


class HistoryMessage(BaseModel):
    role: str  # "guest" | "assistant"
    content: str


class HistoryResponse(BaseModel):
    # The conversation so far for this link — temporary, deleted at end of stay.
    messages: list[HistoryMessage]


class FaqEntry(BaseModel):
    question: str
    answer: str
    answer_language: str | None = None


class FaqMenuResponse(BaseModel):
    # The menu is hidden until enough distinct FAQs have accumulated; `entries`
    # is empty in that case so the frontend can simply check `enabled`.
    enabled: bool
    entries: list[FaqEntry]
