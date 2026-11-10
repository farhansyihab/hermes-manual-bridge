from fastapi import FastAPI
import uvicorn
from .routers import chat, ui, history

app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop Middleware untuk Hermes Agent <-> DeepSeek",
    version="0.2.1"
)

# Include routers
app.include_router(chat.router)
app.include_router(ui.router)
app.include_router(history.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hermes-middleware", "version": "0.2.1"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)