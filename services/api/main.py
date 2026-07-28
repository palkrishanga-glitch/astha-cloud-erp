import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from .app.database import engine, Base
from .app.routers import auth, parties, inventory, sales, purchases, reports, search, sync, backup, ai_assistant

# Initialize Database Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ASTHA ERP Enterprise Core API",
    description="Unified Enterprise Cloud & Desktop ERP API for Astha Builders & Hardware",
    version="2.0.0"
)

# Enable CORS for Desktop (Tauri) and Web (Next.js/React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(parties.router, prefix="/api/v1")
app.include_router(inventory.router, prefix="/api/v1")
app.include_router(sales.router, prefix="/api/v1")
app.include_router(purchases.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(sync.router, prefix="/api/v1")
app.include_router(backup.router, prefix="/api/v1")
app.include_router(ai_assistant.router, prefix="/api/v1")

@app.get("/", response_class=HTMLResponse)
def root_web_ui():
    template_path = os.path.join(os.path.dirname(__file__), "app", "templates", "index.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
def health_check():
    return {"status": "healthy", "system": "ASTHA ERP Enterprise Platform v2.0"}
