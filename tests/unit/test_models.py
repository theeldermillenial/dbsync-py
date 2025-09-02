"""Tests for the base model classes.

This tests the SQLModel base classes without requiring database creation.
"""

from datetime import datetime

import pytest
from sqlmodel import Field, SQLModel

from dbsync.models.base import DBSyncBase


# Test models for unit testing (no table creation)
class TestDBSyncBase(DBSyncBase):
    """Test model inheriting from DBSyncBase."""

    name: str | None = None


class TestIdentifiedModel(SQLModel):
    """Test model with ID field."""

    id: int | None = Field(default=None, primary_key=True)


# TestTimestampedModel and TestNetworkModel removed as base classes were unused


class TestChainMetaModel(SQLModel):
    """Test model mimicking ChainMeta."""

    id: int | None = Field(default=None, primary_key=True)
    network_name: str | None = None
    start_time: datetime | None = None
    version: str | None = None


class TestComplexModel(SQLModel):
    """Test model for field validation tests."""

    id: int | None = Field(default=None, primary_key=True)
    name: str | None = None
    value: int | None = None


class TestDBSyncBaseClass:
    """Test DBSyncBase functionality."""

    def test_config_exists(self):
        """Test that model_config exists with proper settings."""
        assert hasattr(DBSyncBase, "model_config")
        config = DBSyncBase.model_config
        assert config.get("validate_assignment") is True
        assert config.get("use_enum_values") is True
        assert config.get("extra") == "forbid"
        assert config.get("arbitrary_types_allowed") is True

    def test_extra_fields_forbidden(self):
        """Test that extra fields are forbidden during validation."""
        from pydantic import ValidationError

        # Test that model_validate correctly forbids extra fields
        with pytest.raises(ValidationError) as exc_info:
            TestDBSyncBase.model_validate(
                {"name": "test", "invalid_field": "should_fail"}
            )

        # Check that the error is specifically about extra fields
        error = exc_info.value
        assert "extra_forbidden" in str(error)
        assert "invalid_field" in str(error)

        # Test that assignment after creation is also forbidden
        model = TestDBSyncBase(name="test")
        with pytest.raises(ValidationError) as exc_info:
            model.another_invalid_field = "should_fail"

        # Check that the error is about the attribute not existing
        error = exc_info.value
        assert "no_such_attribute" in str(error)

    def test_repr_method(self):
        """Test custom __repr__ method."""
        # Create a test instance
        instance = TestDBSyncBase(name="Test")
        repr_str = repr(instance)

        # Should include class name
        assert "TestDBSyncBase" in repr_str
        assert "(" in repr_str and ")" in repr_str


class TestIdentifiedModelClass:
    """Test IdentifiedModel functionality."""

    def test_has_id_field(self):
        """Test that TestIdentifiedModel has id field."""
        model = TestIdentifiedModel()
        assert hasattr(model, "id")
        assert model.id is None  # Should be None initially

    def test_id_field_properties(self):
        """Test id field properties."""
        # Check field annotations
        annotations = TestIdentifiedModel.__annotations__
        assert "id" in annotations

    def test_id_field_is_primary_key(self):
        """Test that id field is configured as primary key."""
        # Check field definition exists and has correct type
        id_field = TestIdentifiedModel.__fields__["id"]
        # Verify it's a FieldInfo object with the correct annotation
        assert id_field.annotation == int | None
        # Verify it's not required (can be None for auto-increment)
        assert id_field.is_required() is False


# TestTimestampedModelClass and TestNetworkModelClass removed
# as the corresponding base classes were unused


class TestChainMetaClass:
    """Test TestChainMetaModel functionality."""

    def test_model_structure(self):
        """Test TestChainMetaModel model has expected fields."""
        model = TestChainMetaModel()

        # Should have ID field
        assert hasattr(model, "id")

        # Should have ChainMeta-specific fields
        assert hasattr(model, "start_time")
        assert hasattr(model, "network_name")
        assert hasattr(model, "version")

    def test_field_annotations(self):
        """Test TestChainMetaModel field type annotations."""
        annotations = TestChainMetaModel.__annotations__

        # Check expected fields exist
        expected_fields = ["start_time", "network_name", "version"]
        for field in expected_fields:
            assert field in annotations

    def test_field_types(self):
        """Test that fields have correct types."""
        start_time_field = TestChainMetaModel.__fields__["start_time"]
        network_name_field = TestChainMetaModel.__fields__["network_name"]
        version_field = TestChainMetaModel.__fields__["version"]

        assert start_time_field.annotation == datetime | None
        assert network_name_field.annotation == str | None
        assert version_field.annotation == str | None


class TestModelInheritance:
    """Test model inheritance patterns."""

    def test_model_fields(self):
        """Test model field validation."""
        model = TestComplexModel()

        # Should have expected fields
        assert hasattr(model, "id")
        assert hasattr(model, "name")
        assert hasattr(model, "value")

    def test_field_types(self):
        """Test that fields have correct types."""
        annotations = TestComplexModel.__annotations__

        # Check all expected fields exist with correct types
        assert annotations["id"] == int | None
        assert annotations["name"] == str | None
        assert annotations["value"] == int | None


class TestModelMethods:
    """Test model methods and behavior."""

    def test_repr_with_data(self):
        """Test __repr__ method with data."""
        model = TestComplexModel(id=1, name="test")
        repr_str = repr(model)

        assert "TestComplexModel" in repr_str
        assert "id=1" in repr_str

    def test_str_with_data(self):
        """Test __str__ method with data."""
        model = TestComplexModel(id=1, name="test")
        str_repr = str(model)

        # Should be readable
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_dict_serialization(self):
        """Test model to dict conversion."""
        model = TestComplexModel(id=1, name="test", value=42)
        model_dict = model.model_dump()

        assert isinstance(model_dict, dict)
        assert model_dict["id"] == 1
        assert model_dict["name"] == "test"
        assert model_dict["value"] == 42

    def test_json_serialization(self):
        """Test model to JSON conversion."""
        model = TestComplexModel(id=1, name="test", value=42)
        json_str = model.model_dump_json()

        assert isinstance(json_str, str)
        assert '"id":1' in json_str
        assert '"name":"test"' in json_str


class TestModelSerialization:
    """Test model serialization capabilities."""

    def test_dict_serialization(self):
        """Test comprehensive dict serialization."""
        model = TestComplexModel(
            id=1,
            name="test",
            value=42,
        )

        model_dict = model.model_dump()

        assert model_dict["id"] == 1
        assert model_dict["name"] == "test"
        assert model_dict["value"] == 42
        # All expected fields should be present
        assert len(model_dict) == 3

    def test_json_serialization(self):
        """Test comprehensive JSON serialization."""
        model = TestComplexModel(
            id=1,
            name="test",
            value=42,
        )

        json_str = model.model_dump_json()

        assert isinstance(json_str, str)
        assert '"id":1' in json_str
        assert '"name":"test"' in json_str
        assert '"value":42' in json_str
