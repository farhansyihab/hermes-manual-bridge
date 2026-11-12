"""
Main entry point untuk Hermes Manual Bridge.
Modul E: Approval Router ditambahkan untuk Sandbox Approval UI.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from .routers import chat, ui, history, approval

app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop middleware untuk Hermes Agent",
    version="1.3.0"
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(chat.router)
app.include_router(ui.router)
app.include_router(history.router)
app.include_router(approval.router)  # Modul E: Approval endpoints


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.3.0"}