import secrets
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.db_model import UserDatabase
from models.query_model import QueryHistory
from utils.db_connection import validate_database_connection
from utils.encryption import encrypt_password, decrypt_password
from typing import List, Optional
from schemas.db_schemas import UserDatabaseCreate, UserDatabaseUpdate


async def create_user_database(session: AsyncSession, user_id: int, data: UserDatabaseCreate):
    # Keep validation sync for now or refactor to async if needed
    validate_database_connection(
        host=data.host,
        port=data.port,
        db_user=data.db_user,
        db_password=data.db_password,
        db_name=data.db_name,
    )
    encrypted_pass = encrypt_password(data.db_password)
    user_db = UserDatabase(
        user_id=user_id,
        host=data.host,
        port=data.port,
        db_user=data.db_user,
        db_password_encrypted=encrypted_pass,
        db_name=data.db_name,
        mcp_api_key=secrets.token_urlsafe(32)
    )
    session.add(user_db)
    await session.commit()
    await session.refresh(user_db)
    return user_db


async def get_user_databases(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(UserDatabase).where(UserDatabase.user_id == user_id)
    )
    return result.scalars().all()


async def update_user_database(session: AsyncSession, db_id: int, user_id: int, updates: UserDatabaseUpdate):
    db = await session.get(UserDatabase, db_id)
    if not db or db.user_id != user_id:
        return None

    update_data = updates.dict(exclude_unset=True)
    
    # Only validate if connection params are changing
    conn_params = ["host", "port", "db_user", "db_password", "db_name"]
    if any(p in update_data for p in conn_params):
        merged_config = {
            "host": update_data.get("host", db.host),
            "port": update_data.get("port", db.port),
            "db_user": update_data.get("db_user", db.db_user),
            "db_password": update_data.get("db_password", decrypt_password(db.db_password_encrypted)),
            "db_name": update_data.get("db_name", db.db_name),
        }
        validate_database_connection(**merged_config)

    for key, value in update_data.items():
        if key == "db_password":
            value = encrypt_password(value)
            setattr(db, "db_password_encrypted", value)
        elif hasattr(db, key):
            setattr(db, key, value)

    session.add(db)
    await session.commit()
    await session.refresh(db)
    return db


async def delete_user_database(session: AsyncSession, db_id: int, user_id: int):
    db = await session.get(UserDatabase, db_id)
    if not db or db.user_id != user_id:
        return False
    await session.delete(db)
    await session.commit()
    return True


async def generate_mcp_api_key(session: AsyncSession, db_id: int, user_id: int):
    db = await session.get(UserDatabase, db_id)
    if not db or db.user_id != user_id:
        return None
    db.mcp_api_key = secrets.token_urlsafe(32)
    session.add(db)
    await session.commit()
    await session.refresh(db)
    return db.mcp_api_key


async def add_query_history(
    session: AsyncSession,
    db_id: int,
    event_type: str,
    prompt: Optional[str] = None,
    generated_sql: Optional[str] = None,
    executed_sql: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None,
):
    history = QueryHistory(
        user_database_id=db_id,
        event_type=event_type,
        original_prompt=prompt,
        generated_sql=generated_sql,
        executed_sql=executed_sql,
        success=success,
        error_message=error
    )
    session.add(history)
    await session.commit()
    await session.refresh(history)
    return history


async def get_query_history_by_database(session: AsyncSession, db_id: int) -> List[QueryHistory]:
    result = await session.execute(
        select(QueryHistory)
        .where(QueryHistory.user_database_id == db_id)
        .order_by(QueryHistory.executed_at.desc())
    )
    return result.scalars().all()

async def get_user_database_by_mcp_key(session: AsyncSession, mcp_key: str) -> Optional[UserDatabase]:
    result = await session.execute(
        select(UserDatabase).where(UserDatabase.mcp_api_key == mcp_key)
    )
    return result.scalar_one_or_none()
