"""Pure, side-effect-free cricket statistical calculations.

All functions are deliberately defensive: they never raise on zero denominators
and never silently substitute missing data with a misleading zero for metrics
that cannot be computed. Where a metric is undefined, ``None`` is returned and
the caller is expected to surface "N/A" to the user.

Conventions
-----------
* Balls faced exclude wides and no-balls (legal deliveries only) for the
  batter. Byes/leg-byes still count as a ball faced.
* Legal balls bowled exclude wides and no-balls.
* Bowler wickets exclude run-outs, retired hurt, obstructing the field and
  other non-bowler dismissals.
* Overs are ALWAYS derived from legal balls (balls / 6), never from a decimal
  representation such as 19.4 meaning 19 overs + 4 balls treated as 19.4.
* Batting average uses times dismissed (innings - not_outs) as denominator.
"""

from __future__ import annotations

from typing import Optional

# Dismissal types that are NOT credited to the bowler.
NON_BOWLER_DISMISSALS = {
    "run out",
    "retired hurt",
    "retired out",
    "obstructing the field",
    "timed out",
    "hit the ball twice",
    "handled the ball",
}


def safe_divide(numerator: float, denominator: float) -> Optional[float]:
    """Return numerator/denominator or None when denominator is 0/None."""
    if denominator is None or denominator == 0:
        return None
    if numerator is None:
        return None
    return numerator / denominator


def batting_average(runs: int | float, dismissals: int) -> Optional[float]:
    """Runs / times dismissed. Returns None if never dismissed (infinite)."""
    if dismissals is None or dismissals <= 0:
        # Not-out career or no innings: average is undefined (infinite) -> None
        return None
    if runs is None:
        return None
    return runs / dismissals


def batting_strike_rate(runs: int | float, balls_faced: int) -> Optional[float]:
    """(Runs / Balls) * 100."""
    val = safe_divide(runs, balls_faced)
    if val is None:
        return None
    return val * 100.0


def bowling_average(runs_conceded: int | float, wickets: int) -> Optional[float]:
    """Runs conceded / wickets. None if no wickets."""
    return safe_divide(runs_conceded, wickets)


def overs_from_balls(legal_balls: int) -> float:
    """Convert legal balls to overs as a true decimal (e.g. 124 balls -> 20.6667)."""
    if legal_balls is None or legal_balls < 0:
        return 0.0
    return legal_balls / 6.0


def bowling_economy(runs_conceded: int | float, legal_balls: int) -> Optional[float]:
    """Runs conceded per over. Uses (runs/balls)*6, never decimal overs."""
    if legal_balls is None or legal_balls <= 0:
        return None
    if runs_conceded is None:
        return None
    return (runs_conceded / legal_balls) * 6.0


def bowling_strike_rate(legal_balls: int, wickets: int) -> Optional[float]:
    """Balls per wicket."""
    return safe_divide(legal_balls, wickets)


def win_percentage(wins: int, decided_matches: int) -> Optional[float]:
    """(Wins / decided matches) * 100. Excludes no-results."""
    val = safe_divide(wins, decided_matches)
    if val is None:
        return None
    return val * 100.0


def boundary_percentage(boundary_runs: int | float, total_runs: int | float) -> Optional[float]:
    """(Runs from 4s+6s / total runs) * 100."""
    val = safe_divide(boundary_runs, total_runs)
    if val is None:
        return None
    return val * 100.0


def is_bowler_wicket(dismissal_type: Optional[str]) -> bool:
    """Whether a dismissal is credited to the bowler."""
    if not dismissal_type:
        return False
    return dismissal_type.strip().lower() not in NON_BOWLER_DISMISSALS


def legal_ball(extra_type: Optional[str]) -> bool:
    """A delivery counts as a legal ball unless it is a wide or no-ball."""
    if extra_type is None:
        return True
    return extra_type.strip().lower() not in {"wide", "no-ball", "noball", "no ball"}


def not_out_count(innings: int, dismissals: int) -> int:
    if innings is None or dismissals is None:
        return 0
    return max(0, innings - dismissals)


def fantasy_points_basic(runs: int, fours: int, sixes: int, wickets: int) -> int:
    """A simple, transparent fantasy-style score (not an official metric)."""
    return (runs or 0) + 4 * (fours or 0) + 6 * (sixes or 0) + 25 * (wickets or 0)