"""FastAPI application for the FDA Packaging Recalls dashboard."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes import health, recalls

app = FastAPI(
    title="FDA Packaging Recalls API",
    version="0.1.0",
    description="Read-only API serving FDA drug recall analytics.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(recalls.router)

# In production, serve the frontend SPA with catch-all
_frontend_dist = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount(
        "/assets", StaticFiles(directory=_frontend_dist / "assets"), name="static"
    )

    @app.get("/{path:path}")
    async def serve_spa(path: str) -> FileResponse:
        file = _frontend_dist / path
        if file.exists() and file.is_file():
            return FileResponse(file)
        return FileResponse(_frontend_dist / "index.html")
