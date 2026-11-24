"""Match endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Query

from ..services.data_store import load

router = APIRouter(prefix="/api/matches", tags=["matches"])


def clean_records(df):
    if df is None or (hasattr(df, "empty") and df.empty):
        return []
    out = []
    for rec in df.to_dict(orient="records"):
        clean = {}
        for k, v in rec.items():
            if isinstance(v, float) and pd.isna(v):
                clean[k] = None
            else:
                clean[k] = v
        out.append(clean)
    return out


@router.get("")
def list_matches(season: str = Query(None), team: str = Query(None), venue: str = Query(None),
                limit: int = Query(100, ge=1, le=1000)):
    matches = load("matches")
    if season and not matches.empty and "season" in matches.columns:
        matches = matches[matches["season"].astype(str) == str(season)]
    if team and not matches.empty:
        matches = matches[(matches["team1"] == team) | (matches["team2"] == team)]
    if venue and not matches.empty and "venue" in matches.columns:
        matches = matches[matches["venue"].str.contains(venue, case=False, na=False)]
    return {"count": len(matches.head(limit)), "data": clean_records(matches.head(limit))}


@router.get("/{match_id}")
def match_detail(match_id: str):
    matches = load("matches")
    sub = matches[matches["provider_id"].astype(str) == str(match_id)] if (not matches.empty and "provider_id" in matches.columns) else matches
    if sub.empty and not matches.empty and "id" in matches.columns:
        sub = matches[matches["id"].astype(str) == str(match_id)]
    return {"match_id": match_id, "data": clean_records(sub)}