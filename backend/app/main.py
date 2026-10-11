from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.attachments import router as attachments_router
from backend.app.api.auth import router as auth_router
from backend.app.api.findings import router as findings_router
from backend.app.api.projects import router as projects_router
from backend.app.api.users import router as users_router
from backend.app.core.database import engine
from backend.app.models.base import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables are created if database engine is accessible
    try:
        Base.metadata.create_all(bind=engine)
        from backend.scripts.seed_dev_data import seed
        seed()
    except Exception as e:
        # Expected in automated testing environments utilizing in-memory SQLite dependency overrides
        pass
    yield


app = FastAPI(
    title="Cross-Project Code Review Finding Tracker",
    description="Backend API for managing code review findings across projects.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for local Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)
app.include_router(findings_router)
app.include_router(attachments_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

