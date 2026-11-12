"""
Main entry point untuk Hermes Manual Bridge.

KEAMANAN & FALLBACK (Fase 3):
- Load konfigurasi keamanan saat startup
- Tampilkan info whitelist di log startup

Modul E: Approval Router ditambahkan untuk Sandbox Approval UI.

Version: 1.1.0 (Keamanan & Fallback)
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from .routers import chat, ui, history, approval
from .config import security_config


app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop middleware untuk Hermes Agent",
    version="1.1.0"
)


# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Include routers
app.include_router(chat.router)
app.include_router(ui.router)
app.include_router(history.router)
app.include_router(approval.router)  # Modul E: Approval endpoints


@app.on_event("startup")
async def startup_event():
    """
    Event handler saat aplikasi startup.
    Load konfigurasi dan tampilkan info keamanan.
    """
    print("=" * 70)
    print("🚀 Hermes Manual Bridge - Startup")
    print("=" * 70)
    print("\n📋 Konfigurasi Keamanan:")
    print(f"   Whitelist Direktori: {security_config.WHITELISTED_DIRECTORIES}")
    print(f"   Ekstensi Diizinkan: {len(security_config.ALLOWED_EXTENSIONS)} ekstensi")
    print(f"   Maks Ukuran File: {security_config.MAX_FILE_SIZE_BYTES / 1024 / 1024:.1f} MB")
    print(f"   Fallback ke Teks Biasa: {'✅ Aktif' if security_config.ENABLE_FALLBACK_TO_TEXT else '❌ Nonaktif'}")
    print("\n✅ Aplikasi siap menerima request dari Hermes Agent")
    print("=" * 70)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.1.0",
        "security": {
            "whitelist_enabled": True,
            "fallback_enabled": security_config.ENABLE_FALLBACK_TO_TEXT
        }
    }