"""Unit tests for pure cricket statistics."""

from app.utils.stats import (
    batting_average,
    batting_strike_rate,
    bowling_average,
    bowling_economy,
    bowling_strike_rate,
    boundary_percentage,
    is_bowler_wicket,
    legal_ball,
    overs_from_balls,
    win_percentage,
)


def test_batting_average():
    assert batting_average(500, 10) == 50.0
    assert batting_average(100, 0) is None  # never dismissed
    assert batting_average(0, 5) == 0.0


def test_batting_strike_rate():
    assert batting_strike_rate(100, 80) == 125.0
    assert batting_strike_rate(50, 0) is None


def test_bowling_average():
    assert bowling_average(200, 10) == 20.0
    assert bowling_average(100, 0) is None


def test_bowling_economy_not_decimal_overs():
    # 120 runs in 120 balls = 6.0 per over
    assert bowling_economy(120, 120) == 6.0
    # 1 run per ball -> 6 per over
    assert bowling_economy(24, 24) == 6.0
    assert bowling_economy(10, 0) is None


def test_bowling_strike_rate():
    assert bowling_strike_rate(120, 4) == 30.0
    assert bowling_strike_rate(10, 0) is None


def test_overs_from_balls():
    assert overs_from_balls(120) == 20.0
    assert overs_from_balls(124) == 124 / 6.0


def test_win_percentage():
    assert win_percentage(8, 10) == 80.0
    assert win_percentage(5, 0) is None


def test_boundary_percentage():
    assert round(boundary_percentage(120, 200), 2) == 60.0
    assert boundary_percentage(10, 0) is None


def test_bowler_wicket():
    assert is_bowler_wicket("caught") is True
    assert is_bowler_wicket("bowled") is True
    assert is_bowler_wicket("run out") is False
    assert is_bowler_wicket("retired hurt") is False


def test_legal_ball():
    assert legal_ball(None) is True
    assert legal_ball("wide") is False
    assert legal_ball("no-ball") is False
    assert legal_ball("bye") is True


def test_overs_to_legal_balls():
    from app.services.data_processing import overs_to_legal_balls
    assert overs_to_legal_balls("3.4") == 22
    assert overs_to_legal_balls("4") == 24
    assert overs_to_legal_balls(4.0) is not None
    assert overs_to_legal_balls(None) is None
    assert overs_to_legal_balls("DNB") is None