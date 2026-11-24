"""Batting analytics built on Pandas/NumPy.

All functions accept (and return) pandas DataFrames so they can be reused both
by the FastAPI routes (from DB-backed frames) and by the analysis notebooks.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from ..utils.stats import (
    batting_average,
    batting_strike_rate,
    boundary_percentage,
    safe_divide,
)

# Minimum eligibility thresholds for rate-based leaderboards.
MIN_INNINGS_FOR_AVERAGE = 10
MIN_BALLS_FOR_STRIKE_RATE = 200
MIN_INNINGS_FOR_BOUNDARY_PCT = 10


def aggregate_batting(batting_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-player batting totals from a batting scorecard DataFrame.

    Expected columns in ``batting_df``:
        player, player_id, runs, balls, fours, sixes, dismissal, not_out
    (plus optional match_id / season for filtering).
    """
    if batting_df is None or batting_df.empty:
        return pd.DataFrame()

    df = batting_df.copy()
    for col in ("runs", "balls", "fours", "sixes"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["dismissed"] = (~df.get("not_out", False).fillna(False).astype(bool)).astype(int)
    # if dismissal text present, treat as dismissed
    if "dismissal" in df.columns:
        notout_mask = df["dismissal"].astype(str).str.lower().str.contains("not out", na=False)
        df["dismissed"] = (~notout_mask).astype(int)

    g = df.groupby(["player", "player_id"], dropna=False, as_index=False).agg(
        innings=("player", "size"),
        runs=("runs", "sum"),
        balls=("balls", "sum"),
        fours=("fours", "sum"),
        sixes=("sixes", "sum"),
        dismissals=("dismissed", "sum"),
        not_outs=("dismissed", lambda s: int((s == 0).sum())),
    )
    # Recompute not_outs properly
    g["not_outs"] = (g["innings"] - g["dismissals"]).clip(lower=0)

    g["batting_average"] = g.apply(
        lambda r: batting_average(r["runs"], r["dismissals"]), axis=1
    )
    g["strike_rate"] = g.apply(
        lambda r: batting_strike_rate(r["runs"], r["balls"]), axis=1
    )
    boundary_runs = g["fours"] * 4 + g["sixes"] * 6
    g["boundary_percentage"] = [
        boundary_percentage(br, tr) for br, tr in zip(boundary_runs, g["runs"])
    ]
    g["highest_score"] = df.groupby(["player", "player_id"])["runs"].max().values if "runs" in df else None
    # centuries / half-centuries
    df["is_century"] = df["runs"] >= 100
    df["is_fifty"] = (df["runs"] >= 50) & (df["runs"] < 100)
    agg2 = df.groupby(["player", "player_id"], as_index=False).agg(
        centuries=("is_century", "sum"),
        half_centuries=("is_fifty", "sum"),
        highest_score=("runs", "max"),
        matches=("player", "size"),
    )
    g = g.merge(agg2, on=["player", "player_id"], how="left")
    return g


def batting_leaderboard(batting_df: pd.DataFrame, metric: str, season: Optional[str] = None,
                        min_innings: int = MIN_INNINGS_FOR_AVERAGE,
                        min_balls: int = MIN_BALLS_FOR_STRIKE_RATE,
                        top_n: int = 50) -> pd.DataFrame:
    """Return a ranked leaderboard for a given batting metric."""
    agg = aggregate_batting(batting_df)
    if agg.empty:
        return agg

    # Apply eligibility thresholds for rate metrics.
    if metric in {"batting_average"}:
        agg = agg[agg["innings"] >= min_innings]
    if metric in {"strike_rate"}:
        agg = agg[agg["balls"] >= min_balls]
    if metric in {"boundary_percentage"}:
        agg = agg[agg["innings"] >= min_innings]

    sort_map = {
        "runs": ("runs", False),
        "centuries": ("centuries", False),
        "half_centuries": ("half_centuries", False),
        "sixes": ("sixes", False),
        "fours": ("fours", False),
        "batting_average": ("batting_average", False),
        "strike_rate": ("strike_rate", False),
        "highest_score": ("highest_score", False),
        "innings": ("innings", False),
    }
    if metric not in sort_map:
        raise ValueError(f"Unknown batting metric: {metric}")
    col, asc = sort_map[metric]
    agg = agg.sort_values(col, ascending=asc, na_position="last")
    agg = agg.head(top_n).reset_index(drop=True)
    agg.insert(0, "rank", range(1, len(agg) + 1))
    return agg


def player_batting_summary(batting_df: pd.DataFrame, player: str) -> dict:
    sub = batting_df[batting_df["player"] == player] if not batting_df.empty else batting_df
    agg = aggregate_batting(sub)
    if agg.empty:
        return {}
    row = agg.iloc[0].to_dict()
    # season-wise
    if "season" in sub.columns:
        season_rows = []
        for season, g in sub.groupby("season"):
            a = aggregate_batting(g)
            if not a.empty:
                r = a.iloc[0].to_dict()
                r["season"] = season
                season_rows.append(r)
        row["season_wise"] = season_rows
    return row


def season_batting_leaderboard(batting_df: pd.DataFrame, season: str, metric: str, top_n: int = 10) -> pd.DataFrame:
    if batting_df.empty or "season" not in batting_df.columns:
        return pd.DataFrame()
    sub = batting_df[batting_df["season"].astype(str) == str(season)]
    return batting_leaderboard(sub, metric, top_n=top_n)