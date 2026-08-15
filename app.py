"""
Entrypoint for the AI Student Info Board.

Run with:
    uvicorn app:app --host 0.0.0.0 --port 8000

Then point a kiosk browser at http://localhost:8000 (see README for the
Chromium --kiosk command to run on a physical display).
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from src.config import REFRESH_INTERVAL_MINUTES
from src.pipeline import load_latest, run_once

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("campusboard.app")

app = FastAPI(title="AI Student Info Board")

templates = Jinja2Templates(directory="src/kiosk/templates")
app.mount("/static", StaticFiles(directory="src/kiosk/static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

scheduler = BackgroundScheduler()


@app.on_event("startup")
def on_startup():
    # Run once immediately so the kiosk has content right away, then keep
    # refreshing on a timer.
    try:
        run_once()
    except Exception as exc:  # noqa: BLE001
        logger.error("Initial pipeline run failed: %s", exc)

    scheduler.add_job(
        run_once,
        "interval",
        minutes=REFRESH_INTERVAL_MINUTES,
        id="pipeline_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started: refreshing every %s minute(s)", REFRESH_INTERVAL_MINUTES)


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown(wait=False)


@app.get("/")
def kiosk(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/bulletins")
def api_bulletins():
    return JSONResponse(load_latest())


@app.post("/api/refresh")
def api_refresh():
    """Manual trigger, useful for demos so you don't wait for the timer."""
    bulletins = run_once()
    return JSONResponse({"count": len(bulletins)})
