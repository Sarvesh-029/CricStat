"""Player endpoints."""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from ..services.batting_analysis import aggregate_batting, player_batting_summary
from ..services.bowling_analysis import aggregate_bowling, player_bowling_summary
from ..services.data_store import load

router = APIRouter(prefix="/api/players", tags=["players"])


def clean_records(df):
    import pandas as pd
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
def list_players(search: str = Query(None), limit: int = Query(50, ge=1, le=500)):
    players = load("players")
    if search and not players.empty and "name" in players.columns:
        players = players[players["name"].str.contains(search, case=False, na=False)]
    return {"count": len(players.head(limit)), "data": clean_records(players.head(limit))}


@router.get("/{player_id}/stats")
def player_stats(player_id: str):
    batting = load("batting")
    bowling = load("bowling")
    # match by player_id or name
    b_sub = batting[batting["player_id"].astype(str) == str(player_id)] if (not batting.empty and "player_id" in batting.columns) else batting
    bw_sub = bowling[bowling["player_id"].astype(str) == str(player_id)] if (not bowling.empty and "player_id" in bowling.columns) else bowling
    # fallback by name
    if b_sub.empty and not batting.empty and "player" in batting.columns:
        # try players.csv lookup
        players = load("players")
        if not players.empty:
            row = players[players["provider_id"].astype(str) == str(player_id)]
            if not row.empty and "name" in row.columns:
                name = row.iloc[0]["name"]
                b_sub = batting[batting["player"] == name]
                bw_sub = bowling[bowling["player"] == name] if not bowling.empty else bowling
    batting_summary = player_batting_summary(b_sub, b_sub["player"].iloc[0]) if (not b_sub.empty and "player" in b_sub.columns) else {}
    bowling_summary = player_bowling_summary(bw_sub, bw_sub["player"].iloc[0]) if (not bw_sub.empty and "player" in bw_sub.columns) else {}
    return {"player_id": player_id, "batting": batting_summary, "bowling": bowling_summary}


@router.get("/compare")
def compare_players(player1: str, player2: str):
    batting = load("batting")
    bowling = load("bowling")
    def stats_for(pid):
        b_sub = batting[batting["player_id"].astype(str) == str(pid)] if (not batting.empty and "player_id" in batting.columns) else pd.DataFrame()
        bw_sub = bowling[bowling["player_id"].astype(str) == str(pid)] if (not bowling.empty and "player_id" in bowling.columns) else pd.DataFrame()
        if b_sub.empty and not batting.empty:
            players = load("players")
            if not players.empty:
                row = players[players["provider_id"].astype(str) == str(pid)]
                if not row.empty:
                    name = row.iloc[0]["name"]
                    b_sub = batting[batting["player"] == name]
                    bw_sub = bowling[bowling["player"] == name] if not bowling.empty else bw_sub
        bs = player_batting_summary(b_sub, b_sub["player"].iloc[0]) if (not b_sub.empty and "player" in b_sub.columns) else {}
        bws = player_bowling_summary(bw_sub, bw_sub["player"].iloc[0]) if (not bw_sub.empty and "player" in bw_sub.columns) else {}
        return {"batting": bs, "bowling": bws}
    import pandas as pd
    return {"player1": stats_for(player1), "player2": stats_for(player2)}