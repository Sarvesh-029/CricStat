"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import init_db
from .routes import dashboard, leaderboards, matches, players, seasons, teams, venues

app = FastAPI(
    title="CricStat API",
    description="IPL Statistical Analytics Platform - Every Run. Every Wicket. Every Statistic.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(dashboard.router)
app.include_router(leaderboards.router)
app.include_router(players.router)
app.include_router(teams.router)
app.include_router(matches.router)
app.include_router(venues.router)
app.include_router(seasons.router)


@app.get("/api/health")
def health():
    from .config import settings
    return {
        "status": "ok",
        "app": "CricStat",
        "api_key_configured": settings.has_api_key,
    }