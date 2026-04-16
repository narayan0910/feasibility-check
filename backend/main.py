import uvicorn
from contextlib import asynccontextmanager

from core.database import init_db
from app import app


@asynccontextmanager
async def lifespan(_app):
    # ── Startup ───────────────────────────────────────────────────────────────
    print("Starting up... initializing database")
    try:
        from core.database import engine
        with engine.connect() as connection:
            print("✅ Successfully connected to the PostgreSQL database!")
        init_db()
        print("✅ Database tables verified/initialized!")
    except Exception as e:
        print(f"❌ ERROR: Failed to connect to or initialize the database. Please check your POSTGRES_URL.")
        print(f"Details: {e}")
        
    yield
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
