from typing import Optional

from sqlalchemy import create_engine, text


def build_postgres_url(
    host: Optional[str],
    port: Optional[int],
    db_user: Optional[str],
    db_password: str,
    db_name: str,
) -> str:
    if not host or not port or not db_user or not db_password or not db_name:
        raise ValueError("host, port, db_user, db_password, and db_name are required")
    return f"postgresql://{db_user}:{db_password}@{host}:{port}/{db_name}"


def validate_database_connection(
    host: Optional[str],
    port: Optional[int],
    db_user: Optional[str],
    db_password: str,
    db_name: str,
) -> None:
    engine = create_engine(build_postgres_url(host, port, db_user, db_password, db_name), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise ValueError(f"Database connection failed: {exc}") from exc
    finally:
        engine.dispose()
