from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from models.user_model import User
from database import init_db, get_session
from auth.auth_handler import create_access_token, hash_password, verify_password
from auth.auth_bearer import JWTBearer
from routers.agent_routes import router as agent_router
from crud.db_crud import (
    create_user_database,
    get_user_databases,
    update_user_database,
    delete_user_database,
    get_query_history_by_database,
    generate_mcp_api_key
)
from schemas.user_schemas import UserCreate, UserRead, UserLogin
from schemas.db_schemas import UserDatabaseCreate, UserDatabaseUpdate, UserDatabaseRead
from schemas.query_schemas import QueryHistoryRead
from typing import List
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB on startup
    await init_db()
    yield

app = FastAPI(lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Replace with your actual frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router, prefix="/agent", tags=["agent"])

# ----------- Auth Routes -----------

@app.post("/signup", response_model=UserRead)
async def signup(user: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == user.username))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_pw = hash_password(user.password)
    db_user = User(username=user.username, password_hash=hashed_pw)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


@app.post("/login")
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token}


@app.get("/me", dependencies=[Depends(JWTBearer())])
async def read_current_user(token_data: dict = Depends(JWTBearer()), session: AsyncSession = Depends(get_session)):
    user_id = int(token_data["sub"])
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"username": user.username, "user_id": user.id}



@app.post("/databases", dependencies=[Depends(JWTBearer())])
async def add_db(
    db_data: UserDatabaseCreate,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    try:
        db = await create_user_database(session, user_id, db_data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"msg": "Database added successfully", "db_id": db.id, "mcp_api_key": db.mcp_api_key}


@app.get("/get_databases", response_model=list[UserDatabaseRead], dependencies=[Depends(JWTBearer())])
async def get_dbs(
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    dbs = await get_user_databases(session, user_id)
    return [
        UserDatabaseRead.model_validate(db, update={"name": db.db_name}) 
        for db in dbs
    ]


@app.put("/databases/{db_id}", dependencies=[Depends(JWTBearer())])
async def update_db(
    db_id: int,
    updates: UserDatabaseUpdate,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    try:
        updated = await update_user_database(session, db_id, user_id, updates)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Database not found or unauthorized")
    return {"msg": "Database updated", "db_id": updated.id}


@app.delete("/databases/{db_id}", dependencies=[Depends(JWTBearer())])
async def delete_db(
    db_id: int,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    success = await delete_user_database(session, db_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Database not found or unauthorized")
    return {"msg": "Database deleted successfully"}

@app.post("/databases/{db_id}/rotate-mcp-key", dependencies=[Depends(JWTBearer())])
async def rotate_key(
    db_id: int,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])
    new_key = await generate_mcp_api_key(session, db_id, user_id)
    if not new_key:
        raise HTTPException(status_code=404, detail="Database not found or unauthorized")
    return {"mcp_api_key": new_key}

@app.get("/query-history/{db_id}", response_model=List[QueryHistoryRead], dependencies=[Depends(JWTBearer())])
async def get_query_history(
    db_id: int,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(JWTBearer())
):
    user_id = int(token_data["sub"])

    # Ensure user has access to the database
    user_dbs = await get_user_databases(session, user_id)
    if not any(db.id == db_id for db in user_dbs):
        raise HTTPException(status_code=403, detail="Forbidden: Database not accessible")

    query_history = await get_query_history_by_database(session, db_id)
    return [
        QueryHistoryRead.model_validate(qh, update={
            "db_id": qh.user_database_id,
            "prompt": qh.original_prompt,
            "raw_sql": qh.executed_sql or qh.generated_sql,
            "status": "success" if qh.success else "error",
            "error": qh.error_message,
            "timestamp": qh.executed_at
        }) 
        for qh in query_history
    ]


if __name__ == "__main__":
    import uvicorn
    # Use standard uvicorn for async
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
