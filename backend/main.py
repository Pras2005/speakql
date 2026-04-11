from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from core.logging import setup_logging
from routers.agent_routes import router as agent_router
from routers.auth_routes import router as auth_router
from routers.database_routes import router as database_router
from routers.tenant_routes import router as tenant_router
from core.config import settings
import contextlib

# Setup context-aware logging
setup_logging()

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB on startup
    await init_db()
    yield

from middleware.request_context_middleware import RequestIDMiddleware

app = FastAPI(lifespan=lifespan, title="SpeakQL Enterprise API")

# Middlewares
app.add_middleware(RequestIDMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router, tags=["Authentication"])
app.include_router(tenant_router, prefix="/tenancy", tags=["Tenancy"])
app.include_router(database_router, prefix="/databases", tags=["Databases"])
app.include_router(agent_router, prefix="/agent", tags=["AI Agent"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
