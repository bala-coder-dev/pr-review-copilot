"""
FastAPI entry point for PR Review Copilot.
Run locally:  uvicorn app.main:app --reload
"""

from dotenv import load_dotenv

# Load .env before other app modules read environment variables.
load_dotenv()

from fastapi import FastAPI

from app.webhook import router as webhook_router

app = FastAPI(
    title="PR Review Copilot",
    description="GitHub PR webhook receiver (Week 1)",
    version="0.1.0",
)

app.include_router(webhook_router)


@app.get("/health")
async def health_check():
    """Simple liveness check for local dev and future Render deploys."""
    return {"status": "ok"}
