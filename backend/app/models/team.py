from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    short_name: Mapped[str | None] = mapped_column(String(16))
    logo_url: Mapped[str | None] = mapped_column(String(512))

    home_matches = relationship("Match", foreign_keys="Match.team1_id", back_populates="team1")
    away_matches = relationship("Match", foreign_keys="Match.team2_id", back_populates="team2")