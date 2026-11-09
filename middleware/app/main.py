from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(
    title="Hermes Manual Bridge",
    description="Human-in-the-Loop Middleware untuk Hermes Agent <-> DeepSeek",
    version="0.1.0"
)

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Hermes Bridge</title></head>
    <body>
        <h1>🚀 Hermes Manual Bridge - Online</h1>
        <p>Middleware berjalan di <code>http://localhost:8000</code></p>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "hermes-middleware"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
