"""Ingest IPL data from CricAPI and build processed CSVs.

Usage (from backend/ directory):
    python -m scripts.ingest            # full ingest
    python -m scripts.ingest --limit 5  # only first 5 matches (for testing)

Requires CRICAPI_API_KEY in .env.
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# Make `app` importable when run as a script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd

from app.config import settings
from app.services.api_service import CricAPIClient, CricAPIError
from app.services.data_processing import (
    ensure_dirs,
    is_ipl_series,
    normalize_match_info,
    normalize_players_search,
    normalize_scorecard,
    normalize_series,
    normalize_series_info,
    save_raw,
)
from app.services.data_store import save

CLIENT = CricAPIClient()


def run(limit: int | None = None) -> None:
    ensure_dirs()
    if not settings.has_api_key:
        print("ERROR: CRICAPI_API_KEY not set in backend/.env. Aborting.")
        sys.exit(1)

    # 1. Series list
    print("Fetching series list...")
    try:
        payload = CLIENT.series_list()
    except CricAPIError as e:
        print(f"Failed to fetch series list: {e}")
        sys.exit(1)
    save_raw("series_list", payload)
    series_df = normalize_series(payload)
    ipl_series = series_df[series_df["name"].apply(is_ipl_series)] if not series_df.empty else series_df
    print(f"Found {len(ipl_series)} IPL series out of {len(series_df)} total series.")

    all_matches: list[dict] = []
    all_batting: list[pd.DataFrame] = []
    all_bowling: list[pd.DataFrame] = []
    all_innings: list[pd.DataFrame] = []

    for _, s in ipl_series.iterrows():
        sid = s.get("provider_id")
        sname = s.get("name")
        if not sid:
            continue
        print(f"\nSeries: {sname} ({sid})")
        try:
            info_payload = CLIENT.series_info(str(sid))
        except CricAPIError as e:
            print(f"  skip series_info: {e}")
            continue
        save_raw(f"series_info_{sid}", info_payload)
        mdf, _ = normalize_series_info(info_payload)
        if mdf.empty:
            print("  no matches in series_info")
            continue
        mdf["season"] = sname
        # Attach season year if available
        if "year" in series_df.columns:
            mdf["season_year"] = s.get("year")

        for _, m in mdf.iterrows():
            mid = m.get("provider_id")
            if not mid:
                continue
            if limit is not None and len(all_matches) >= limit:
                break
            print(f"  match: {m.get('name')} ({mid})")
            # match_info
            try:
                mi_payload = CLIENT.match_info(str(mid))
                save_raw(f"match_info_{mid}", mi_payload)
                mi = normalize_match_info(mi_payload)
            except CricAPIError as e:
                print(f"    match_info failed: {e}")
                mi = m.to_dict()
            # scorecard
            batting_df = pd.DataFrame()
            bowling_df = pd.DataFrame()
            innings_df = pd.DataFrame()
            try:
                sc_payload = CLIENT.match_scorecard(str(mid))
                save_raw(f"match_scorecard_{mid}", sc_payload)
                batting_df, bowling_df, innings_df = normalize_scorecard(sc_payload)
            except CricAPIError as e:
                print(f"    scorecard failed: {e}")

            match_row = {
                "provider_id": mi.get("provider_id") or mid,
                "season": sname,
                "name": mi.get("name") or m.get("name"),
                "match_type": mi.get("match_type") or m.get("match_type"),
                "status": mi.get("status") or m.get("status"),
                "venue": mi.get("venue") or m.get("venue"),
                "date": mi.get("date") or m.get("date"),
                "team1": mi.get("team1") or m.get("team1"),
                "team2": mi.get("team2") or m.get("team2"),
                "winner": mi.get("winner") or m.get("winner"),
                "toss_winner": mi.get("toss_winner"),
                "toss_decision": mi.get("toss_decision"),
                "player_of_match": mi.get("player_of_match"),
                "team1_score": mi.get("team1_score"),
                "team2_score": mi.get("team2_score"),
            }
            all_matches.append(match_row)

            for df, team_col in ((batting_df, "batting_team"),):
                if not df.empty:
                    df = df.copy()
                    df["match_id"] = mid
                    df["season"] = sname
                    all_batting.append(df)
            if not bowling_df.empty:
                bowling_df = bowling_df.copy()
                bowling_df["match_id"] = mid
                bowling_df["season"] = sname
                all_bowling.append(bowling_df)
            if not innings_df.empty:
                innings_df = innings_df.copy()
                innings_df["match_id"] = mid
                innings_df["season"] = sname
                all_innings.append(innings_df)

            time.sleep(0.5)  # be polite to free tier

        if limit is not None and len(all_matches) >= limit:
            break

    # Save processed CSVs
    matches_df = pd.DataFrame(all_matches)
    save("matches", matches_df)
    print(f"\nSaved matches: {len(matches_df)}")

    if all_batting:
        batting_df = pd.concat(all_batting, ignore_index=True)
        # normalize column naming for downstream analysis: player already present
        save("batting", batting_df)
        print(f"Saved batting rows: {len(batting_df)}")
    else:
        save("batting", pd.DataFrame())

    if all_bowling:
        bowling_df = pd.concat(all_bowling, ignore_index=True)
        save("bowling", bowling_df)
        print(f"Saved bowling rows: {len(bowling_df)}")
    else:
        save("bowling", pd.DataFrame())

    if all_innings:
        innings_df = pd.concat(all_innings, ignore_index=True)
        save("innings", innings_df)
        print(f"Saved innings rows: {len(innings_df)}")
    else:
        save("innings", pd.DataFrame())

    # seasons
    if not series_df.empty:
        ipl_seasons = series_df[series_df["name"].apply(is_ipl_series)].copy()
        save("seasons", ipl_seasons)
        print(f"Saved seasons: {len(ipl_seasons)}")

    # teams: derive from matches
    teams = set()
    for m in all_matches:
        teams.add(m.get("team1"))
        teams.add(m.get("team2"))
    teams_df = pd.DataFrame({"name": sorted(t for t in teams if t)})
    save("teams", teams_df)
    print(f"Saved teams: {len(teams_df)}")

    # venues
    venues = set(m.get("venue") for m in all_matches if m.get("venue"))
    venues_df = pd.DataFrame({"name": sorted(venues)})
    save("venues", venues_df)
    print(f"Saved venues: {len(venues_df)}")

    # players: best-effort from batting/bowling names
    player_names = set()
    if all_batting:
        for df in all_batting:
            player_names.update(df["player"].dropna().tolist())
    if all_bowling:
        for df in all_bowling:
            player_names.update(df["player"].dropna().tolist())
    players_df = pd.DataFrame({"name": sorted(player_names)})
    save("players", players_df)
    print(f"Saved players: {len(players_df)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None, help="Max matches to ingest")
    args = parser.parse_args()
    run(limit=args.limit)