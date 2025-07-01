"""Foundation models and types for Cardano DB Sync.

This module contains the fundamental types and base models that other modules depend on.
Basic foundation models and configuration types.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, Column, DateTime, String, Text
from sqlmodel import Field

from .base import DBSyncBase

__all__ = [
    "ChainMeta",
    "EventInfo",
    "ExtraMigrations",
]


class ChainMeta(DBSyncBase, table=True):
    """Chain metadata model for the meta table.

    Stores fundamental blockchain network information.
    """

    __tablename__ = "meta"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    start_time: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="Blockchain start time",
    )

    network_name: str | None = Field(
        default=None, max_length=64, description="Network name (mainnet, testnet, etc.)"
    )

    version: str | None = Field(
        default=None, max_length=32, description="DB Sync version"
    )

    def is_mainnet(self) -> bool:
        """Check if this is mainnet.

        Returns:
            True if this is mainnet, False otherwise
        """
        return self.network_name == "mainnet"

    def is_testnet(self) -> bool:
        """Check if this is a testnet.

        Returns:
            True if this is a testnet, False otherwise
        """
        return self.network_name in ("testnet", "preprod", "preview")

    def get_network_info(self) -> dict[str, Any]:
        """Get network information summary.

        Returns:
            Dictionary with network information
        """
        return {
            "network_name": self.network_name,
            "is_mainnet": self.is_mainnet(),
            "is_testnet": self.is_testnet(),
            "start_time": self.start_time,
            "version": self.version,
        }


class ExtraMigrations(DBSyncBase, table=True):
    """Extra migrations model for the extra_migrations table.

    Represents optional database migrations that may be applied
    beyond the standard schema migrations.
    """

    __tablename__ = "extra_migrations"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    token: str | None = Field(
        default=None,
        sa_column=Column(String(255), unique=True),
        description="Unique token identifying the migration",
    )

    description: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Description of what this migration does",
    )


class EventInfo(DBSyncBase, table=True):
    """Event info model for the event_info table.

    Represents significant system events and their details for monitoring
    and debugging purposes.
    """

    __tablename__ = "event_info"

    id_: int | None = Field(
        default=None,
        sa_column=Column(BigInteger, primary_key=True, autoincrement=True, name="id"),
        description="Auto-incrementing primary key",
    )

    event_name: str | None = Field(
        default=None,
        sa_column=Column(String(255)),
        description="Name of the event that occurred",
    )

    event_time: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True)),
        description="When the event occurred",
    )

    description: str | None = Field(
        default=None,
        sa_column=Column(Text),
        description="Detailed description of the event",
    )

    severity: str | None = Field(
        default=None,
        sa_column=Column(String(50)),
        description="Severity level of the event (INFO, WARNING, ERROR, etc.)",
    )
