from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn
from .routers import chat, ui, history

app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop Middleware untuk Hermes Agent <-> DeepSeek",
    version="0.2.1"
)

# ============================================================
# Mount static files (CSS, JS, images, dll.)
# Folder "static/" berada di sibling folder "app/" yaitu:
#   /home/farhan/Proyek/Hermes/middleware/static/
# ============================================================
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include routers
app.include_router(chat.router)
app.include_router(ui.router)
app.include_router(history.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hermes-middleware", "version": "0.2.1"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)