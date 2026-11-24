from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes.api import api

app = FastAPI(title="AI customer support")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


app.include_router(api)

dashboard = Path(__file__).resolve().parent.parent / "dashboard" / "dist"
if dashboard.exists():
    app.mount("/", StaticFiles(directory=dashboard, html=True), name="dashboard")
