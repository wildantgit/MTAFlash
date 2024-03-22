from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from sqlalchemy.dialects import (
    postgresql,
)  # ARRAY contains requires dialect specific type
from sqlalchemy.orm import Mapped
from sqlmodel import Column, Field, Relationship, SQLModel, String

# class Date(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     dateText: str = Field(nullable=True)
#     data_id: Optional[str] = Field(default=None, foreign_key="data.stop")
# date: List[datetime] = Field(
#     default=None, sa_column=Column(postgresql.ARRAY(String()))
# )
# data_stop: Optional[Data] = Relationship(back_populates="date")


# Optional because if we use this field as auto id increment


class StopAlertsLink(SQLModel, table=True):
    stop_id: Optional[int] = Field(
        default=None, foreign_key="stop.id", primary_key=True
    )
    alert_id: Optional[int] = Field(
        default=None, foreign_key="alerts.id", primary_key=True
    )


class Alerts(SQLModel, table=True):

    # the value would be None before it gets to the database
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)
    alert_type: str = Field(nullable=True)
    created_at: datetime = Field(nullable=True)
    updated_at: datetime = Field(nullable=True)
    direction: str = Field(nullable=True)
    heading: str = Field(nullable=True)
    decription: str = Field(nullable=True)
    stops: List["Stop"] = Relationship(
        back_populates="alert", link_model=StopAlertsLink
    )


class Stop(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True, unique=True)

    stop: Optional[str] = Field(default=None)
    route: str

    alert: Optional["Alerts"] = Relationship(
        back_populates="stops", link_model=StopAlertsLink
    )
