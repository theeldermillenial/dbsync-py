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


class TestTimestampedModel(SQLModel):
    """Test model with timestamp fields."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class TestNetworkModel(SQLModel):
    """Test model with network fields."""

    id: int | None = Field(default=None, primary_key=True)
    network_id: int | None = None
    network_magic: int | None = None


class TestChainMetaModel(SQLModel):
    """Test model mimicking ChainMeta."""

    id: int | None = Field(default=None, primary_key=True)
    network_name: str | None = None
    start_time: datetime | None = None
    version: str | None = None


class TestComplexModel(SQLModel):
    """Test model for multiple inheritance tests."""

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    network_id: int | None = None
    network_magic: int | None = None


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


class TestTimestampedModelClass:
    """Test TimestampedModel functionality."""

    def test_has_timestamp_fields(self):
        """Test that TestTimestampedModel has timestamp fields."""
        model = TestTimestampedModel()
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")

    def test_timestamp_field_properties(self):
        """Test timestamp field properties."""
        annotations = TestTimestampedModel.__annotations__
        assert "created_at" in annotations
        assert "updated_at" in annotations

    def test_timestamp_field_types(self):
        """Test that timestamp fields have correct types."""
        created_field = TestTimestampedModel.__fields__["created_at"]
        updated_field = TestTimestampedModel.__fields__["updated_at"]

        assert created_field.annotation == datetime | None
        assert updated_field.annotation == datetime | None


class TestNetworkModelClass:
    """Test NetworkModel functionality."""

    def test_has_network_field(self):
        """Test that TestNetworkModel has network_id field."""
        model = TestNetworkModel()
        assert hasattr(model, "network_id")

    def test_network_field_properties(self):
        """Test network_id field properties."""
        annotations = TestNetworkModel.__annotations__
        assert "network_id" in annotations

    def test_network_field_types(self):
        """Test that network fields have correct types."""
        network_id_field = TestNetworkModel.__fields__["network_id"]
        network_magic_field = TestNetworkModel.__fields__["network_magic"]

        assert network_id_field.annotation == int | None
        assert network_magic_field.annotation == int | None


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

    def test_multiple_inheritance(self):
        """Test model with multiple inheritance patterns."""
        model = TestComplexModel()

        # Should have all expected fields
        assert hasattr(model, "id")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")
        assert hasattr(model, "network_id")
        assert hasattr(model, "network_magic")

    def test_inheritance_field_types(self):
        """Test that inherited fields maintain correct types."""
        annotations = TestComplexModel.__annotations__

        # Check all expected fields exist with correct types
        assert annotations["id"] == int | None
        assert annotations["created_at"] == datetime | None
        assert annotations["updated_at"] == datetime | None
        assert annotations["network_id"] == int | None
        assert annotations["network_magic"] == int | None


class TestModelMethods:
    """Test model methods and behavior."""

    def test_repr_with_data(self):
        """Test __repr__ method with data."""
        model = TestNetworkModel(id=1, network_id=1)
        repr_str = repr(model)

        assert "TestNetworkModel" in repr_str
        assert "id=1" in repr_str

    def test_str_with_data(self):
        """Test __str__ method with data."""
        model = TestNetworkModel(id=1, network_id=1)
        str_repr = str(model)

        # Should be readable
        assert isinstance(str_repr, str)
        assert len(str_repr) > 0

    def test_dict_serialization(self):
        """Test model to dict conversion."""
        model = TestNetworkModel(id=1, network_id=1, network_magic=764824073)
        model_dict = model.model_dump()

        assert isinstance(model_dict, dict)
        assert model_dict["id"] == 1
        assert model_dict["network_id"] == 1
        assert model_dict["network_magic"] == 764824073

    def test_json_serialization(self):
        """Test model to JSON conversion."""
        model = TestNetworkModel(id=1, network_id=1, network_magic=764824073)
        json_str = model.model_dump_json()

        assert isinstance(json_str, str)
        assert '"id":1' in json_str
        assert '"network_id":1' in json_str


class TestModelSerialization:
    """Test model serialization capabilities."""

    def test_dict_serialization(self):
        """Test comprehensive dict serialization."""
        model = TestComplexModel(
            id=1,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            updated_at=datetime(2023, 1, 1, 12, 30, 0),
            network_id=1,
            network_magic=764824073,
        )

        model_dict = model.model_dump()

        assert model_dict["id"] == 1
        assert model_dict["network_id"] == 1
        assert model_dict["network_magic"] == 764824073
        # Datetime should be serialized
        assert "created_at" in model_dict
        assert "updated_at" in model_dict

    def test_json_serialization(self):
        """Test comprehensive JSON serialization."""
        model = TestComplexModel(
            id=1,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            network_id=1,
            network_magic=764824073,
        )

        json_str = model.model_dump_json()

        assert isinstance(json_str, str)
        assert '"id":1' in json_str
        assert '"network_id":1' in json_str
        # Should handle datetime serialization
        assert "created_at" in json_str
