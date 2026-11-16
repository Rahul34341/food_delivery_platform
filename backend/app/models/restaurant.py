from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer,
    String, Text, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Restaurant(Base):
    __tablename__ = "restaurants"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True
    )

    name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    address: Mapped[str] = mapped_column(
        String(255), nullable=False
    )

    city: Mapped[str] = mapped_column(
        String(100), nullable=False
    )

    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    banner_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )

    owner = relationship(
        "User", back_populates="restaurants"
    )

    menu_categories = relationship(
        "MenuCategory",
        back_populates="restaurant",
        cascade="all, delete-orphan",
    )
