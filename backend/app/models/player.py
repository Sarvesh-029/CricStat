from __future__ import annotations

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class Player(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    provider_id: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    image_url: Mapped[str | None] = mapped_column(String(512))
    role: Mapped[str | None] = mapped_column(String(64))
    batting_style: Mapped[str | None] = mapped_column(String(64))
    bowling_style: Mapped[str | None] = mapped_column(String(64))