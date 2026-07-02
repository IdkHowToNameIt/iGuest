from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

# connect_timeout bounds how long a connection attempt can block, so an
# unreachable DB can never hang the app (e.g. the background retention job).
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
