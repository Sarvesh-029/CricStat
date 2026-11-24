"""Bowling analytics built on Pandas/NumPy."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from ..utils.stats import (
    bowling_average,
    bowling_economy,
    bowling_strike_rate,
    overs_from_balls,
)

MIN_OVERS_FOR_ECONOMY = 20  # minimum overs bowled
MIN_WICKETS_FOR_AVERAGE = 10


def aggregate_bowling(bowling_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-player bowling totals.

    Expected columns: player, player_id, overs, legal_balls, maidens, runs_conceded, wickets.
    """
    if bowling_df is None or bowling_df.empty:
        return pd.DataFrame()

    df = bowling_df.copy()
    for col in ("legal_balls", "maidens", "runs_conceded", "wickets"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    # fill legal_balls from overs if missing
    if "legal_balls" not in df.columns or df["legal_balls"].isna().all():
        df["legal_balls"] = df.get("overs").apply(lambda x: None) if "overs" in df else None
    df["legal_balls"] = df["legal_balls"].fillna(0).astype(int) if False else df["legal_balls"]
    # ensure numeric
    df["legal_balls"] = pd.to_numeric(df["legal_balls"], errors="coerce").fillna(0).astype(int)
    for col in ("maidens", "runs_conceded", "wickets"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        else:
            df[col] = 0

    g = df.groupby(["player", "player_id"], dropna=False, as_index=False).agg(
        innings=("player", "size"),
        legal_balls=("legal_balls", "sum"),
        maidens=("maidens", "sum"),
        runs_conceded=("runs_conceded", "sum"),
        wickets=("wickets", "sum"),
    )
    g["overs"] = g["legal_balls"].apply(overs_from_balls)
    g["bowling_average"] = g.apply(lambda r: bowling_average(r["runs_conceded"], r["wickets"]), axis=1)
    g["economy"] = g.apply(lambda r: bowling_economy(r["runs_conceded"], r["legal_balls"]), axis=1)
    g["bowling_strike_rate"] = g.apply(lambda r: bowling_strike_rate(r["legal_balls"], r["wickets"]), axis=1)
    # best figures
    if "runs_conceded" in df.columns and "wickets" in df.columns:
        idx = df.groupby(["player", "player_id"])["wickets"].idxmax()
        best = df.loc[idx, ["player", "player_id", "wickets", "runs_conceded"]].copy()
        best["best_figures"] = best.apply(lambda r: f"{int(r['wickets'])}/{int(r['runs_conceded'])}", axis=1)
        g = g.merge(best[["player", "player_id", "best_figures"]], on=["player", "player_id"], how="left")
    # 4w / 5w hauls
    hauls = df.copy()
    hauls["is_4w"] = hauls["wickets"] >= 4
    hauls["is_5w"] = hauls["wickets"] >= 5
    h = hauls.groupby(["player", "player_id"], as_index=False).agg(
        four_wicket_hauls=("is_4w", "sum"),
        five_wicket_hauls=("is_5w", "sum"),
    )
    g = g.merge(h, on=["player", "player_id"], how="left")
    g["four_wicket_hauls"] = g["four_wicket_hauls"].fillna(0).astype(int)
    g["five_wicket_hauls"] = g["five_wicket_hauls"].fillna(0).astype(int)
    return g


def bowling_leaderboard(bowling_df: pd.DataFrame, metric: str, top_n: int = 50) -> pd.DataFrame:
    agg = aggregate_bowling(bowling_df)
    if agg.empty:
        return agg
    if metric in {"bowling_average", "economy", "bowling_strike_rate"}:
        # eligibility: enough overs
        agg = agg[agg["legal_balls"] >= MIN_OVERS_FOR_ECONOMY * 6]
        if metric == "bowling_average":
            agg = agg[agg["wickets"] >= MIN_WICKETS_FOR_AVERAGE]

    sort_map = {
        "wickets": ("wickets", False),
        "bowling_average": ("bowling_average", True),  # lower better
        "economy": ("economy", True),
        "bowling_strike_rate": ("bowling_strike_rate", True),
        "maidens": ("maidens", False),
        "four_wicket_hauls": ("four_wicket_hauls", False),
        "five_wicket_hauls": ("five_wicket_hauls", False),
        "legal_balls": ("legal_balls", False),
    }
    if metric not in sort_map:
        raise ValueError(f"Unknown bowling metric: {metric}")
    col, asc = sort_map[metric]
    agg = agg.sort_values(col, ascending=asc, na_position="last")
    agg = agg.head(top_n).reset_index(drop=True)
    agg.insert(0, "rank", range(1, len(agg) + 1))
    return agg


def player_bowling_summary(bowling_df: pd.DataFrame, player: str) -> dict:
    sub = bowling_df[bowling_df["player"] == player] if not bowling_df.empty else bowling_df
    agg = aggregate_bowling(sub)
    if agg.empty:
        return {}
    return agg.iloc[0].to_dict()