from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from core.logging import setup_logging
from routers.agent_routes import router as agent_router
from routers.auth_routes import router as auth_router
from routers.database_routes import router as database_router
from routers.tenant_routes import router as tenant_router
from routers.governance_routes import router as governance_router
from routers.workflow_routes import router as workflow_router
from routers.catalog_routes import router as catalog_router
from routers.report_routes import router as report_router
from core.config import settings
import contextlib

# Setup context-aware logging
setup_logging()

import asyncio

async def report_scheduler_task():
    """Background task to run reports periodically."""
    from database import get_session
    from repositories.report_repository import ReportRepository, ReportRunRepository
    from repositories.workflow_repository import SavedQueryRepository, QueryCommentRepository
    from repositories.database_repository import DatabaseRepository
    from repositories.audit_repository import AuditRepository
    from repositories.policy_repository import PolicyRepository
    from repositories.approval_repository import ApprovalRepository
    from repositories.sensitivity_repository import SensitivityRepository
    from services.report_service import ReportService
    from services.workflow_service import WorkflowService
    from services.governance_service import GovernanceService
    from services.database_service import DatabaseService
    from services.audit_service import AuditService
    from services.policy_service import PolicyService
    from services.risk_service import RiskScoringService
    from services.approval_service import ApprovalService
    from services.sensitivity_service import SensitivityService
    from services.masking_service import MaskingService
    from services.confidence_service import ConfidenceService
    
    print("Starting background report scheduler...")
    while True:
        try:
            async for session in get_session():
                # Setup services
                db_repo = DatabaseRepository(session)
                audit_repo = AuditRepository(session)
                audit_service = AuditService(audit_repo)
                db_service = DatabaseService(db_repo, audit_service)
                
                policy_repo = PolicyRepository(session)
                policy_service = PolicyService(policy_repo)
                
                risk_service = RiskScoringService()
                conf_service = ConfidenceService()
                
                app_repo = ApprovalRepository(session)
                app_service = ApprovalService(app_repo)
                
                sens_repo = SensitivityRepository(session)
                sens_service = SensitivityService(sens_repo)
                mask_service = MaskingService(sens_service)
                
                gov_service = GovernanceService(db_service, policy_service, risk_service, app_service, mask_service, conf_service)
                
                q_repo = SavedQueryRepository(session)
                c_repo = QueryCommentRepository(session)
                wf_service = WorkflowService(q_repo, c_repo, gov_service)
                
                r_repo = ReportRepository(session)
                rr_repo = ReportRunRepository(session)
                report_service = ReportService(r_repo, rr_repo, wf_service, audit_service)
                
                # Check for enabled reports
                await report_service.run_pending_reports(db_repo)
                    
                break # Only one pass per session cycle
                
            await asyncio.sleep(600) # Check every 10 minutes
        except Exception as e:
            print(f"Error in report scheduler: {e}")
            await asyncio.sleep(60)

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Init DB on startup
    await init_db()
    # Start background scheduler
    scheduler_task = asyncio.create_task(report_scheduler_task())
    yield
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass

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
app.include_router(governance_router, prefix="/governance", tags=["Governance"])
app.include_router(agent_router, prefix="/agent", tags=["AI Agent"])
app.include_router(workflow_router, prefix="/workflow", tags=["Workflow"])
app.include_router(catalog_router, prefix="/catalog", tags=["Catalog"])
app.include_router(report_router, prefix="/reports", tags=["Reports"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.DEBUG)
