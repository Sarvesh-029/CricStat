"""Data processing: convert raw CricAPI JSON into clean, normalized DataFrames.

This module is the single place where provider-specific JSON shapes are
translated into CricStat's internal tabular model. Downstream analytics
code (batting_analysis, bowling_analysis, ...) only ever sees these
DataFrames, so swapping the data provider later only requires changes here.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from typing import Any, Iterable

import numpy as np
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")


def ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def save_raw(name: str, payload: Any) -> str:
    ensure_dirs()
    path = os.path.join(RAW_DIR, f"{name}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    return path


def load_raw(name: str) -> Any:
    path = os.path.join(RAW_DIR, f"{name}.json")
    if not os.path.exists(path):
        return None
    with open(path, "w" if False else "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def _s(x: Any) -> str | None:
    if x is None:
        return None
    s = str(x).strip()
    return s if s and s.lower() not in {"none", "null", "nan", "-"} else None


def _i(x: Any) -> int | None:
    if x is None:
        return None
    if isinstance(x, bool):
        return int(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    s = str(x).strip()
    if not s or s.lower() in {"none", "null", "nan", "-", "dnb", "did not bat"}:
        return None
    # handle "45 (30)" style -> take first number
    m = re.match(r"^-?\d+", s)
    if m:
        try:
            return int(m.group(0))
        except ValueError:
            return None
    try:
        return int(float(s))
    except ValueError:
        return None


def _f(x: Any) -> float | None:
    if x is None:
        return None
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    if not s or s.lower() in {"none", "null", "nan", "-", "dnb"}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def overs_to_legal_balls(overs: Any) -> int | None:
    """Convert an overs representation to legal balls.

    Handles:
      - int/float like 4.0 (whole overs) -> 24 balls
      - string "3.4" meaning 3 overs + 4 balls -> 22 balls
      - string "3.4 overs" -> 22 balls
      - None / "DNB" -> None
    We deliberately do NOT treat 3.4 as the decimal 3.4 overs.
    """
    if overs is None:
        return None
    if isinstance(overs, (int, np.integer)):
        return int(overs) * 6
    if isinstance(overs, (float, np.floating)):
        # Ambiguous: a float 3.4 from JSON could be "3 overs 4 balls" OR 3.4 overs.
        # CricAPI typically serialises overs as strings; a bare float is treated as
        # whole+fractional overs only if the fractional part is a multiple of 1/6.
        whole = int(overs)
        frac = overs - whole
        # snap fractional part to nearest ball
        balls = round(frac * 6)
        if balls >= 6:
            whole += 1
            balls -= 6
        return whole * 6 + balls
    s = str(overs).strip().lower()
    if not s or s in {"none", "null", "nan", "-", "dnb", "did not bat"}:
        return None
    s = s.replace("overs", "").replace("ov", "").strip()
    if "." in s:
        parts = s.split(".")
        try:
            whole = int(parts[0])
        except ValueError:
            return None
        ball_part = parts[1].strip()
        # ball_part may be "4" or "4 (1)" etc.
        m = re.match(r"(\d+)", ball_part)
        balls = int(m.group(1)) if m else 0
        if balls > 5:
            # Could be a decimal-overs value like 3.333; fall back to rounding.
            balls = round((float(s) - whole) * 6)
        return whole * 6 + balls
    # no decimal
    try:
        return int(float(s)) * 6
    except ValueError:
        return None


# --------------------------------------------------------------------------- #
# Normalizers
# --------------------------------------------------------------------------- #
def normalize_series(payload: dict) -> pd.DataFrame:
    """Flatten CricAPI /series response into a seasons DataFrame."""
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        for key in ("list", "series", "data"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        data = []
    rows = []
    for s in data:
        if not isinstance(s, dict):
            continue
        name = _s(s.get("name") or s.get("seriesName") or s.get("series"))
        if not name:
            continue
        rows.append(
            {
                "provider_id": _s(s.get("id") or s.get("seriesId")),
                "name": name,
                "start_date": _s(s.get("startDate") or s.get("start_date")),
                "end_date": _s(s.get("endDate") or s.get("end_date")),
                "year": _extract_year(name, s.get("startDate") or s.get("start_date")),
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.drop_duplicates(subset=["provider_id", "name"]).reset_index(drop=True)
    return df


def _extract_year(name: str, start_date: Any) -> int | None:
    # Try start_date first
    if start_date:
        m = re.search(r"(\d{4})", str(start_date))
        if m:
            return int(m.group(1))
    m = re.search(r"(20\d{2}|19\d{2})", name)
    if m:
        return int(m.group(1))
    return None


def is_ipl_series(name: str) -> bool:
    n = (name or "").lower()
    return "indian premier league" in n or "ipl" in n.split() or "ipl" in n


def normalize_series_info(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (matches_df, squads_df) for a series.

    CricAPI series_info typically returns matchList and (sometimes) squad info.
    """
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        info = data
    else:
        info = {}
    matches_raw = []
    for key in ("matchList", "matches", "matchlist"):
        if isinstance(info.get(key), list):
            matches_raw = info[key]
            break
    rows = []
    for m in matches_raw:
        if not isinstance(m, dict):
            continue
        rows.append(
            {
                "provider_id": _s(m.get("id") or m.get("matchId")),
                "name": _s(m.get("name") or m.get("matchName")),
                "match_type": _s(m.get("matchType")),
                "status": _s(m.get("status")),
                "venue": _s(m.get("venue")),
                "date": _s(m.get("date") or m.get("dateTimeGMT")),
                "team1": _s(m.get("team-1") or m.get("t1") or (m.get("teams", [None, None])[0] if isinstance(m.get("teams"), list) else None)),
                "team2": _s(m.get("team-2") or m.get("t2") or (m.get("teams", [None, None])[1] if isinstance(m.get("teams"), list) else None)),
                "winner": _s(m.get("matchWinner") or m.get("winner")),
            }
        )
    matches_df = pd.DataFrame(rows)
    squads_df = pd.DataFrame()
    return matches_df, squads_df


def normalize_match_info(payload: dict) -> dict:
    """Flatten a match_info payload into a dict of scalar fields."""
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return {}
    teams = data.get("teams") if isinstance(data.get("teams"), list) else None
    team1 = teams[0] if teams and len(teams) > 0 else data.get("team-1") or data.get("t1")
    team2 = teams[1] if teams and len(teams) > 1 else data.get("team-2") or data.get("t2")
    toss = data.get("toss") if isinstance(data.get("toss"), dict) else {}
    score = data.get("score") if isinstance(data.get("score"), list) else []
    return {
        "provider_id": _s(data.get("id") or data.get("matchId")),
        "name": _s(data.get("name") or data.get("matchName")),
        "match_type": _s(data.get("matchType")),
        "status": _s(data.get("status")),
        "venue": _s(data.get("venue")),
        "date": _s(data.get("date") or data.get("dateTimeGMT")),
        "team1": _s(team1),
        "team2": _s(team2),
        "winner": _s(data.get("matchWinner") or data.get("winner")),
        "toss_winner": _s(toss.get("winner") or data.get("tossWinner")),
        "toss_decision": _s(toss.get("decision") or data.get("tossDecision")),
        "player_of_match": _s(data.get("playerOfMatch") or data.get("player_of_match")),
        "team1_score": _s(score[0].get("r") if score and isinstance(score[0], dict) else None),
        "team2_score": _s(score[1].get("r") if len(score) > 1 and isinstance(score[1], dict) else None),
    }


def normalize_scorecard(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parse a match_scorecard payload.

    Returns (batting_df, bowling_df, innings_df). Delivery-level data is NOT
    provided by CricAPI scorecards, so deliveries are never fabricated.
    """
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    scorecard = data.get("scorecard") if isinstance(data.get("scorecard"), list) else []
    batting_rows: list[dict] = []
    bowling_rows: list[dict] = []
    innings_rows: list[dict] = []

    for idx, inn in enumerate(scorecard, start=1):
        if not isinstance(inn, dict):
            continue
        batting_team = _s(inn.get("battingTeam") or inn.get("batteam") or inn.get("team"))
        bowling_team = _s(inn.get("bowlingTeam") or inn.get("bowlteam"))
        # innings totals
        innings_rows.append(
            {
                "innings_number": idx,
                "batting_team": batting_team,
                "bowling_team": bowling_team,
                "total_runs": _i(inn.get("runs") or inn.get("total") or inn.get("score")),
                "total_wickets": _i(inn.get("wickets")),
                "total_overs": _s(inn.get("overs") or inn.get("o")),
                "total_balls": overs_to_legal_balls(inn.get("overs") or inn.get("o")),
                "extras": _i(inn.get("extras")),
            }
        )

        for b in (inn.get("batting") or inn.get("batsman") or []):
            if not isinstance(b, dict):
                continue
            batting_rows.append(
                {
                    "innings_number": idx,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "player": _s(b.get("batsman") or b.get("name") or b.get("batter")),
                    "player_id": _s(b.get("batsmanId") or b.get("id")),
                    "runs": _i(b.get("r") or b.get("runs")),
                    "balls": _i(b.get("b") or b.get("balls")),
                    "fours": _i(b.get("4s") or b.get("fours")),
                    "sixes": _i(b.get("6s") or b.get("sixes")),
                    "strike_rate": _f(b.get("sr") or b.get("strikeRate") or b.get("strikerate")),
                    "dismissal": _s(b.get("dismissal") or b.get("out") or b.get("howout")),
                    "not_out": _is_not_out(b),
                }
            )

        for bw in (inn.get("bowling") or inn.get("bowler") or []):
            if not isinstance(bw, dict):
                continue
            bowling_rows.append(
                {
                    "innings_number": idx,
                    "batting_team": batting_team,
                    "bowling_team": bowling_team,
                    "player": _s(bw.get("bowler") or bw.get("name")),
                    "player_id": _s(bw.get("bowlerId") or bw.get("id")),
                    "overs": _s(bw.get("o") or bw.get("overs")),
                    "legal_balls": overs_to_legal_balls(bw.get("o") or bw.get("overs")),
                    "maidens": _i(bw.get("m") or bw.get("maidens")),
                    "runs_conceded": _i(bw.get("r") or bw.get("runs") or bw.get("conceded")),
                    "wickets": _i(bw.get("w") or bw.get("wickets")),
                    "economy": _f(bw.get("eco") or bw.get("economy")),
                    "dots": None,  # not provided by scorecard
                }
            )

    return pd.DataFrame(batting_rows), pd.DataFrame(bowling_rows), pd.DataFrame(innings_rows)


def _is_not_out(b: dict) -> bool:
    dismissal = _s(b.get("dismissal") or b.get("out") or b.get("howout"))
    if dismissal is None:
        return True
    low = dismissal.lower()
    if low in {"not out", "batting", "notout"}:
        return True
    if "not out" in low:
        return True
    return False


def normalize_players_search(payload: dict) -> pd.DataFrame:
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, dict):
        for key in ("list", "players"):
            if isinstance(data.get(key), list):
                data = data[key]
                break
    if not isinstance(data, list):
        data = []
    rows = []
    for p in data:
        if not isinstance(p, dict):
            continue
        rows.append(
            {
                "provider_id": _s(p.get("id") or p.get("playerId")),
                "name": _s(p.get("name") or p.get("playerName")),
                "image_url": _s(p.get("playerImg") or p.get("image") or p.get("img")),
                "role": _s(p.get("role") or p.get("playingRole")),
                "country": _s(p.get("country")),
            }
        )
    return pd.DataFrame(rows)


def normalize_player_info(payload: dict) -> dict:
    data = payload.get("data", payload) if isinstance(payload, dict) else payload
    if isinstance(data, list):
        data = data[0] if data else {}
    if not isinstance(data, dict):
        return {}
    return {
        "provider_id": _s(data.get("id") or data.get("playerId")),
        "name": _s(data.get("name") or data.get("playerName")),
        "image_url": _s(data.get("playerImg") or data.get("image") or data.get("img")),
        "role": _s(data.get("role") or data.get("playingRole")),
        "batting_style": _s(data.get("battingStyle")),
        "bowling_style": _s(data.get("bowlingStyle")),
        "country": _s(data.get("country")),
        "date_of_birth": _s(data.get("dateOfBirth") or data.get("dob")),
    }