from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Delivery(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    innings_id: Mapped[int] = mapped_column(ForeignKey("innings.id"), index=True)
    over_number: Mapped[int | None] = mapped_column(Integer, index=True)
    ball_number: Mapped[int | None] = mapped_column(Integer)
    batter_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), index=True)
    bowler_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), index=True)
    non_striker_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    runs_batter: Mapped[int | None] = mapped_column(Integer, default=0)
    runs_extras: Mapped[int | None] = mapped_column(Integer, default=0)
    runs_total: Mapped[int | None] = mapped_column(Integer, default=0)
    extra_type: Mapped[str | None] = mapped_column(String(16))  # wide, noball, bye, legbye
    is_wicket: Mapped[bool | None] = mapped_column(default=False)
    dismissal_type: Mapped[str | None] = mapped_column(String(32))
    player_dismissed_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"))
    is_legal_ball: Mapped[bool | None] = mapped_column(default=True)

    innings = relationship("Innings", back_populates="deliveries")
    batter = relationship("Player", foreign_keys=[batter_id])
    bowler = relationship("Player", foreign_keys=[bowler_id])