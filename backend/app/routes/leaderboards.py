"""Leaderboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..services.batting_analysis import batting_leaderboard
from ..services.bowling_analysis import bowling_leaderboard
from ..services.data_store import load

router = APIRouter(prefix="/api/leaderboards", tags=["leaderboards"])

BATTING_METRICS = [
    "runs", "centuries", "half_centuries", "sixes", "fours",
    "batting_average", "strike_rate", "highest_score", "innings",
]
BOWLING_METRICS = [
    "wickets", "bowling_average", "economy", "bowling_strike_rate",
    "maidens", "four_wicket_hauls", "five_wicket_hauls",
]


def _filter_season(df, season):
    if season and not df.empty and "season" in df.columns:
        return df[df["season"].astype(str) == str(season)]
    return df


@router.get("/all-time/batting")
def all_time_batting(metric: str = Query("runs"), limit: int = Query(50, ge=1, le=500)):
    if metric not in BATTING_METRICS:
        raise HTTPException(400, f"Unknown metric: {metric}")
    batting = load("batting")
    df = batting_leaderboard(batting, metric, top_n=limit)
    return {"metric": metric, "count": len(df), "data": clean_records(df)}


@router.get("/all-time/bowling")
def all_time_bowling(metric: str = Query("wickets"), limit: int = Query(50, ge=1, le=500)):
    if metric not in BOWLING_METRICS:
        raise HTTPException(400, f"Unknown metric: {metric}")
    bowling = load("bowling")
    df = bowling_leaderboard(bowling, metric, top_n=limit)
    return {"metric": metric, "count": len(df), "data": clean_records(df)}


@router.get("/all-time/overall")
def all_time_overall(limit: int = Query(50, ge=1, le=500)):
    matches = load("matches")
    batting = load("batting")
    bowling = load("bowling")
    # matches played per player (approx from batting+bowling)
    frames = []
    if not batting.empty:
        m = batting.groupby("player", as_index=False).agg(matches=("player", "size"))
        frames.append(m)
    if frames:
        out = frames[0]
    else:
        out = pd.DataFrame(columns=["player", "matches"])
    return {"count": len(out.head(limit)), "data": clean_records(out.head(limit))}


@router.get("/season/{season_id}/batting")
def season_batting(season_id: str, metric: str = Query("runs"), limit: int = Query(10, ge=1, le=100)):
    if metric not in BATTING_METRICS:
        raise HTTPException(400, f"Unknown metric: {metric}")
    batting = load("batting")
    sub = _filter_season(batting, season_id)
    df = batting_leaderboard(sub, metric, top_n=limit)
    return {"season": season_id, "metric": metric, "count": len(df), "data": clean_records(df)}


@router.get("/season/{season_id}/bowling")
def season_bowling(season_id: str, metric: str = Query("wickets"), limit: int = Query(10, ge=1, le=100)):
    if metric not in BOWLING_METRICS:
        raise HTTPException(400, f"Unknown metric: {metric}")
    bowling = load("bowling")
    sub = _filter_season(bowling, season_id)
    df = bowling_leaderboard(sub, metric, top_n=limit)
    return {"season": season_id, "metric": metric, "count": len(df), "data": clean_records(df)}


def clean_records(df):
    import pandas as pd
    if df is None or (hasattr(df, "empty") and df.empty):
        return []
    out = []
    for rec in df.to_dict(orient="records"):
        clean = {}
        for k, v in rec.items():
            if isinstance(v, float) and (pd.isna(v)):
                clean[k] = None
            else:
                clean[k] = v
        out.append(clean)
    return out


