"""Team analytics built on Pandas/NumPy."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from ..utils.stats import win_percentage


def aggregate_teams(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per-team win/loss records from a matches DataFrame.

    Expected columns: team1, team2, winner (team name), plus optional season.
    """
    if matches_df is None or matches_df.empty:
        return pd.DataFrame()

    df = matches_df.copy()
    teams = set(df["team1"].dropna().tolist()) | set(df["team2"].dropna().tolist())
    rows = []
    for team in sorted(teams):
        played = int(((df["team1"] == team) | (df["team2"] == team)).sum())
        won = int((df["winner"] == team).sum())
        lost = int(((df["winner"].notna()) & (df["winner"] != team) & ((df["team1"] == team) | (df["team2"] == team))).sum())
        no_result = played - won - lost
        decided = won + lost
        rows.append(
            {
                "team": team,
                "matches": played,
                "won": won,
                "lost": lost,
                "no_result": no_result,
                "win_percentage": win_percentage(won, decided),
            }
        )
    return pd.DataFrame(rows)


def head_to_head(matches_df: pd.DataFrame, team_a: str, team_b: str) -> dict:
    if matches_df is None or matches_df.empty:
        return {"matches": 0, "team_a_wins": 0, "team_b_wins": 0, "no_result": 0}
    mask = (
        ((matches_df["team1"] == team_a) & (matches_df["team2"] == team_b))
        | ((matches_df["team1"] == team_b) & (matches_df["team2"] == team_a))
    )
    sub = matches_df[mask]
    a_wins = int((sub["winner"] == team_a).sum())
    b_wins = int((sub["winner"] == team_b).sum())
    nr = int(sub["winner"].isna().sum())
    return {
        "matches": int(len(sub)),
        "team_a_wins": a_wins,
        "team_b_wins": b_wins,
        "no_result": nr,
    }


def season_wise_team(matches_df: pd.DataFrame, team: str) -> pd.DataFrame:
    if matches_df is None or matches_df.empty or "season" not in matches_df.columns:
        return pd.DataFrame()
    df = matches_df[((matches_df["team1"] == team) | (matches_df["team2"] == team))].copy()
    rows = []
    for season, g in df.groupby("season"):
        agg = aggregate_teams(g)
        r = agg[agg["team"] == team]
        if not r.empty:
            out = r.iloc[0].to_dict()
            out["season"] = season
            rows.append(out)
    return pd.DataFrame(rows)