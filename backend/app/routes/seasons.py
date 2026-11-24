"""Season endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from ..services.data_store import load

router = APIRouter(prefix="/api/seasons", tags=["seasons"])


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
def list_seasons():
    seasons = load("seasons")
    return {"count": len(seasons), "data": clean_records(seasons)}


@router.get("/{season_id}/stats")
def season_stats(season_id: str):
    matches = load("matches")
    batting = load("batting")
    bowling = load("bowling")
    m = matches[matches["season"].astype(str) == str(season_id)] if (not matches.empty and "season" in matches.columns) else matches
    b = batting[batting["season"].astype(str) == str(season_id)] if (not batting.empty and "season" in batting.columns) else batting
    bw = bowling[bowling["season"].astype(str) == str(season_id)] if (not bowling.empty and "season" in bowling.columns) else bowling
    from ..services.team_analysis import aggregate_teams
    teams = aggregate_teams(m) if not m.empty else pd.DataFrame()
    top_team = None
    if not teams.empty:
        r = teams.sort_values("won", ascending=False).iloc[0]
        top_team = {"team": r["team"], "wins": int(r["won"])}
    return {
        "season": season_id,
        "matches": len(m),
        "total_runs": int(b["runs"].sum()) if (not b.empty and "runs" in b.columns) else 0,
        "total_wickets": int(bw["wickets"].sum()) if (not bw.empty and "wickets" in bw.columns) else 0,
        "most_successful_team": top_team,
    }


@router.get("/compare")
def compare_seasons(season1: str, season2: str):
    return {"season1": season_stats(season1), "season2": season_stats(season2)}