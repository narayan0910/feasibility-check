import uvicorn
from contextlib import asynccontextmanager

from core.database import init_db
from app import app


@asynccontextmanager
async def lifespan(_app):
    # ── Startup ───────────────────────────────────────────────────────────────
    print("Starting up... initializing database")
    init_db()
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("Shutting down...")

app.router.lifespan_context = lifespan

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
