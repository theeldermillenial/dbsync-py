"""Base model classes for Cardano DB Sync SQLModel implementation.

This module provides base classes and common patterns for all database models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict
from sqlalchemy.ext.declarative import declared_attr
from sqlmodel import SQLModel

__all__ = [
    "DBSyncBase",
]


class DBSyncBase(SQLModel):
    """Base class for all Cardano DB Sync models.

    Provides common functionality and configuration for database models.
    """

    # Pydantic v2 model configuration
    model_config = ConfigDict(
        validate_assignment=True,
        use_enum_values=True,
        arbitrary_types_allowed=True,
        extra="forbid",  # Prevent extra fields not defined in the model
        json_encoders={
            datetime: lambda v: v.isoformat(),
            bytes: lambda v: v.hex(),
        },
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """Generate table name from class name.

        Converts CamelCase to snake_case for table names.
        """
        name = cls.__name__
        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())
        return "".join(result)

    @declared_attr
    def __table_args__(cls) -> dict:
        """Common table arguments for all models.

        Allows table redefinition for testing scenarios.
        """
        return {"extend_existing": True}

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary.

        Returns:
            Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name) for column in self.__table__.columns
        }

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update model fields from dictionary.

        Args:
            data: Dictionary with field values to update
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @classmethod
    def get_column_names(cls) -> list[str]:
        """Get list of column names for this model.

        Returns:
            List of column names
        """
        return [column.name for column in cls.__table__.columns]

    def __repr__(self) -> str:
        """String representation of the model."""
        class_name = self.__class__.__name__
        attrs = []

        # Check if this is a table model (has __table__ attribute)
        if hasattr(self, "__table__") and self.__table__ is not None:
            # Show primary key fields first for table models
            for column in self.__table__.primary_key.columns:
                value = getattr(self, column.name, None)
                if value is not None:
                    attrs.append(f"{column.name}={value!r}")

            # Add a few other important fields if they exist
            for field_name in ["hash", "view", "epoch_no", "slot_no", "block_no"]:
                if hasattr(self, field_name):
                    value = getattr(self, field_name, None)
                    if value is not None and field_name not in [
                        col.name for col in self.__table__.primary_key.columns
                    ]:
                        attrs.append(f"{field_name}={value!r}")
        else:
            # For non-table models, show all non-None fields
            for field_name, field_info in self.model_fields.items():
                value = getattr(self, field_name, None)
                if value is not None:
                    attrs.append(f"{field_name}={value!r}")

        attrs_str = ", ".join(attrs[:3])  # Limit to first 3 attributes
        if len(attrs) > 3:
            attrs_str += ", ..."

        return f"{class_name}({attrs_str})"


# TimestampedModel and NetworkModel removed as they were unused
# and not needed for read-only Cardano DB Sync operations
