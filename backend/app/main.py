from fastapi import FastAPI
from backend.app.api.auth import router as auth_router
from backend.app.api.users import router as users_router
from backend.app.api.projects import router as projects_router

app = FastAPI(
    title="Cross-Project Code Review Finding Tracker",
    description="Backend API for managing code review findings across projects.",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(projects_router)



@app.get("/health")
def health_check():
    return {"status": "ok"}
