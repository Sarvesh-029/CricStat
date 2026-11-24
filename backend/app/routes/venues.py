"""Venue endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from ..services.data_store import load

router = APIRouter(prefix="/api/venues", tags=["venues"])


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
def list_venues():
    venues = load("venues")
    matches = load("matches")
    # augment with match counts
    if not matches.empty and "venue" in matches.columns:
        counts = matches.groupby("venue").size().reset_index(name="matches_played")
        if not venues.empty and "name" in venues.columns:
            venues = venues.merge(counts, left_on="name", right_on="venue", how="left")
    return {"count": len(venues), "data": clean_records(venues)}


@router.get("/{venue_id}/stats")
def venue_stats(venue_id: str):
    matches = load("matches")
    name = venue_id
    venues = load("venues")
    if not venues.empty and "provider_id" in venues.columns:
        row = venues[venues["provider_id"].astype(str) == str(venue_id)]
        if not row.empty and "name" in row.columns:
            name = row.iloc[0]["name"]
    sub = matches[matches["venue"] == name] if (not matches.empty and "venue" in matches.columns) else matches
    return {"venue": name, "matches": len(sub), "data": clean_records(sub)}