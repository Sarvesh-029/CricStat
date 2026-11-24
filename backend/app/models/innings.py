from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Innings(Base):
    __tablename__ = "innings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id"), index=True)
    batting_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"), index=True)
    bowling_team_id: Mapped[int | None] = mapped_column(ForeignKey("teams.id"))
    innings_number: Mapped[int | None] = mapped_column(Integer)
    total_runs: Mapped[int | None] = mapped_column(Integer)
    total_wickets: Mapped[int | None] = mapped_column(Integer)
    total_overs: Mapped[float | None] = mapped_column()  # legal overs as decimal
    total_balls: Mapped[int | None] = mapped_column(Integer)
    extras: Mapped[int | None] = mapped_column(Integer)

    match = relationship("Match", back_populates="innings")
    batting_team = relationship("Team", foreign_keys=[batting_team_id])
    bowling_team = relationship("Team", foreign_keys=[bowling_team_id])
    deliveries = relationship("Delivery", back_populates="innings", cascade="all, delete-orphan")