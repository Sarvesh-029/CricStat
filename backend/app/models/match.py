from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    season_id: Mapped[int | None] = mapped_column(ForeignKey("seasons.id"), index=True)
    venue_id: Mapped[int | None] = mapped_column(ForeignKey("venues.id"), index=True)
    team1_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    team2_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    winner_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    toss_winner_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    toss_decision: Mapped[str | None] = mapped_column(String(16))  # bat / field
    match_date: Mapped[str | None] = mapped_column(String(32))
    status: Mapped[str | None] = mapped_column(String(32))
    result_text: Mapped[str | None] = mapped_column(String(256))
    winning_margin: Mapped[str | None] = mapped_column(String(64))
    player_of_match_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    team1_score: Mapped[str | None] = mapped_column(String(64))
    team2_score: Mapped[str | None] = mapped_column(String(64))

    season = relationship("Season", back_populates="matches")
    venue = relationship("Venue")
    team1 = relationship("Team", foreign_keys=[team1_id], back_populates="home_matches")
    team2 = relationship("Team", foreign_keys=[team2_id], back_populates="away_matches")
    winner = relationship("Team", foreign_keys=[winner_id])
    toss_winner = relationship("Team", foreign_keys=[toss_winner_id])
    player_of_match = relationship("Player", foreign_keys=[player_of_match_id])

    innings = relationship("Innings", back_populates="match", cascade="all, delete-orphan")