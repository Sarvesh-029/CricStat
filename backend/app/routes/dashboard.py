"""Dashboard endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter

from ..services.data_store import load

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/overview")
def overview():
    matches = load("matches")
    batting = load("batting")
    bowling = load("bowling")
    teams = load("teams")
    players = load("players")
    seasons = load("seasons")

    total_runs = int(batting["runs"].sum()) if not batting.empty and "runs" in batting else 0
    total_wickets = int(bowling["wickets"].sum()) if not bowling.empty and "wickets" in bowling else 0

    highest_team_score = None
    if not matches.empty and "team1_score" in matches.columns:
        scores = pd_scores(matches)
        highest_team_score = int(scores.max()) if len(scores) else None

    most_runs_player = None
    if not batting.empty:
        agg = batting.groupby("player", as_index=False)["runs"].sum().sort_values("runs", ascending=False)
        if not agg.empty:
            most_runs_player = {"player": agg.iloc[0]["player"], "runs": int(agg.iloc[0]["runs"])}

    most_wickets_player = None
    if not bowling.empty:
        agg = bowling.groupby("player", as_index=False)["wickets"].sum().sort_values("wickets", ascending=False)
        if not agg.empty:
            most_wickets_player = {"player": agg.iloc[0]["player"], "wickets": int(agg.iloc[0]["wickets"])}

    most_successful_team = None
    if not matches.empty:
        from ..services.team_analysis import aggregate_teams
        ta = aggregate_teams(matches)
        if not ta.empty:
            r = ta.sort_values("won", ascending=False).iloc[0]
            most_successful_team = {"team": r["team"], "wins": int(r["won"])}

    return {
        "seasons_covered": int(seasons["name"].nunique()) if not seasons.empty and "name" in seasons else 0,
        "matches_played": int(len(matches)),
        "teams": int(teams["name"].nunique()) if not teams.empty and "name" in teams else 0,
        "players": int(players["name"].nunique()) if not players.empty and "name" in players else 0,
        "total_runs": total_runs,
        "total_wickets": total_wickets,
        "highest_team_score": highest_team_score,
        "most_successful_team": most_successful_team,
        "top_run_scorer": most_runs_player,
        "top_wicket_taker": most_wickets_player,
        "data_available": not matches.empty,
    }


def pd_scores(matches):
    import pandas as pd
    s1 = pd.to_numeric(matches.get("team1_score"), errors="coerce")
    s2 = pd.to_numeric(matches.get("team2_score"), errors="coerce")
    return pd.concat([s1, s2]).dropna()


@router.get("/trends")
def trends():
    matches = load("matches")
    batting = load("batting")
    bowling = load("bowling")
    out = {"season_runs": [], "season_wickets": [], "team_wins": []}
    if not matches.empty and "season" in matches.columns:
        # runs per season needs batting join; fall back to matches count
        pass
    if not batting.empty and "season" in batting.columns:
        sr = batting.groupby("season", as_index=False)["runs"].sum()
        out["season_runs"] = sr.to_dict(orient="records")
    if not bowling.empty and "season" in bowling.columns:
        sw = bowling.groupby("season", as_index=False)["wickets"].sum()
        out["season_wickets"] = sw.to_dict(orient="records")
    if not matches.empty and "season" in matches.columns:
        from ..services.team_analysis import aggregate_teams
        # team wins across all seasons
        tw = matches.groupby(["season", "winner"], as_index=False).size() if "winner" in matches else pd.DataFrame()
        if not tw.empty:
            tw = tw.rename(columns={"size": "wins"})
            out["team_wins"] = tw.to_dict(orient="records")
    return out