"""
RAG package — retrieval-augmented answering for guest questions.

Public surface used by the chat service.
"""

from app.services.rag.engine import RagResult, UnitNotFoundError, answer_question

__all__ = ["RagResult", "UnitNotFoundError", "answer_question"]
