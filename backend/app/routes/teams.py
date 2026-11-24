"""Team endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, Query

from ..services.data_store import load
from ..services.team_analysis import aggregate_teams, head_to_head

router = APIRouter(prefix="/api/teams", tags=["teams"])


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
def list_teams():
    teams = load("teams")
    return {"count": len(teams), "data": clean_records(teams)}


@router.get("/{team_id}/stats")
def team_stats(team_id: str):
    matches = load("matches")
    teams = load("teams")
    name = team_id
    if not teams.empty and "provider_id" in teams.columns:
        row = teams[teams["provider_id"].astype(str) == str(team_id)]
        if not row.empty and "name" in row.columns:
            name = row.iloc[0]["name"]
    if not teams.empty and "name" in teams.columns and team_id in set(teams["name"].tolist()):
        name = team_id
    agg = aggregate_teams(matches)
    sub = agg[agg["team"] == name] if not agg.empty else agg
    h2h = {}
    if not matches.empty:
        for opp in (teams["name"].tolist() if (not teams.empty and "name" in teams.columns) else []):
            if opp != name:
                h2h[opp] = head_to_head(matches, name, opp)
    return {"team": name, "stats": clean_records(sub), "head_to_head": h2h}


@router.get("/compare")
def compare_teams(team1: str, team2: str):
    matches = load("matches")
    return {
        "team1": team1,
        "team2": team2,
        "head_to_head": head_to_head(matches, team1, team2),
    }