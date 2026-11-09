Directory structure:
└── hermes/
    ├── middleware/
    │   ├── requirements.txt
    │   └── app/
    │       ├── __init__.py
    │       ├── main.py
    │       └── routers/
    │           └── __init__.py
    └── planning/
        └── Blueprint.md

================================================
FILE: middleware/requirements.txt
================================================
annotated-doc==0.0.5
annotated-types==0.8.0
anyio==4.16.0
click==8.5.1
fastapi==0.162.2
h11==0.16.0
httptools==0.9.0
idna==3.20
opentelemetry-api==1.45.2
pydantic==2.14.3
pydantic_core==2.50.4
python-dotenv==1.2.4
PyYAML==6.0.3
starlette==1.10.0
typing-inspection==0.4.5
typing_extensions==4.16.0
uvicorn==0.54.0
uvloop==0.23.0
watchfiles==1.3.0
websockets==17.4



================================================
FILE: middleware/app/__init__.py
================================================
[Empty file]


================================================
FILE: middleware/app/main.py
================================================
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



================================================
FILE: middleware/app/routers/__init__.py
================================================
[Empty file]
