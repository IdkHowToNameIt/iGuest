from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    postgres_user: str = "iguest"
    postgres_password: str = "iguest"
    postgres_db: str = "iguest"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # AI
    gemini_api_key: str = ""
    embedding_model: str = "models/gemini-embedding-001"
    embedding_batch_size: int = 100  # texts per Gemini embed_content call
    generation_model: str = "models/gemini-3.5-flash"  # free-tier friendly
    generation_temperature: float = 0.2  # low â†’ faithful to context, less invention

    # Per-request cap: a slow/overloaded model returns 503/504 instead of stalling
    generation_timeout_seconds: int = 60

    # Chunking
    chunk_size: int = 800       # target characters per chunk
    chunk_overlap: int = 100    # overlap characters between consecutive chunks

    # RAG retrieval
    rag_top_k: int = 10         # chunks fed into the generation prompt (higher = better
                                # recall, incl. cross-lingual queries on large manuals)
    rag_max_distance: float = 0.65  # cosine-distance cutoff: farther chunks are noise for
                                    # the model; 0 disables the filter and keeps the top-k

    # FAQ / question analytics (recompute script)
    # Cosine-distance thresholds for the two clustering levels: tighter groups
    # near-duplicate questions; the coarser one groups those into categories.
    faq_question_distance: float = 0.18
    faq_category_distance: float = 0.40
    faq_top_n: int = 5          # number of FAQ entries surfaced in the guest chat
    faq_min_to_show: int = 3    # hide the FAQ menu below this many entries
    # In-app scheduled recompute (otherwise clusters/analytics/FAQs never
    # update unless someone runs scripts/recompute_faqs.py by hand)
    faq_recompute_enabled: bool = True
    faq_recompute_interval_seconds: int = 300  # every 5 minutes

    # Guest conversations / GDPR retention
    conversation_retention_days: int = 30  # auto-delete conversations after N days
    # In-app scheduled purge of expired conversations
    retention_purge_enabled: bool = True
    retention_purge_interval_seconds: int = 86400  # run the purge once per day

    # Admin authentication (single administrator; no public registration)
    admin_username: str = "admin"
    admin_password: str = "changeme"
    admin_jwt_secret: str = "dev-insecure-secret-change-me"
    admin_token_expire_minutes: int = 720  # 12 hours

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    max_document_upload_bytes: int = 20 * 1024 * 1024  # 20 MB

    # CORS
    cors_origins: str = "http://localhost:5173"

    # Visit-request notifications (leads from the public landing page). Optional:
    # when an SMTP host is configured, each new lead is emailed to
    # ``visit_request_notify_email``; otherwise it is just stored + logged. Demo
    # deployments can leave these blank and read the leads in the admin inbox.
    visit_request_notify_email: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True

    @property
    def database_url(self) -> str:
        # postgresql+psycopg:// uses psycopg v3, which supports Python 3.11+
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


settings = Settings()
