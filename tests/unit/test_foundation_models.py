"""Tests for SCHEMA-002 Foundation Models.

This module tests the foundation models and types from SCHEMA-002,
specifically the ChainMeta model and its functionality.
"""

import datetime

from dbsync.models import ChainMeta, EventInfo, ExtraMigrations


class TestChainMetaModel:
    """Test suite for ChainMeta model from SCHEMA-002."""

    def test_chainmeta_creation(self):
        """Test ChainMeta model creation with basic fields."""
        meta = ChainMeta(
            network_name="mainnet",
            version="13.2.0",
        )

        assert meta.network_name == "mainnet"
        assert meta.version == "13.2.0"

    def test_chainmeta_with_timestamps(self):
        """Test ChainMeta with timestamp fields."""
        start_time = datetime.datetime(2017, 9, 23, 21, 44, 51, tzinfo=datetime.UTC)

        meta = ChainMeta(
            network_name="mainnet",
            start_time=start_time,
        )

        assert meta.start_time == start_time
        assert meta.network_name == "mainnet"

    def test_chainmeta_simplified_fields(self):
        """Test ChainMeta with simplified fields available."""
        start_time = datetime.datetime.now(datetime.UTC)

        meta = ChainMeta(
            network_name="mainnet",
            version="13.2.0",
            start_time=start_time,
        )

        assert meta.network_name == "mainnet"
        assert meta.version == "13.2.0"
        assert meta.start_time == start_time

    def test_is_mainnet_method(self):
        """Test is_mainnet() method logic."""
        # Test with network_name
        mainnet_meta = ChainMeta(network_name="mainnet")
        assert mainnet_meta.is_mainnet() is True

        # Test false case
        testnet_meta = ChainMeta(network_name="testnet")
        assert testnet_meta.is_mainnet() is False

    def test_is_testnet_method(self):
        """Test is_testnet() method logic."""
        # Test with network_name testnet
        testnet_meta = ChainMeta(network_name="testnet")
        assert testnet_meta.is_testnet() is True

        # Test with network_name preprod
        preprod_meta = ChainMeta(network_name="preprod")
        assert preprod_meta.is_testnet() is True

        # Test with network_name preview
        preview_meta = ChainMeta(network_name="preview")
        assert preview_meta.is_testnet() is True

        # Test false case
        mainnet_meta = ChainMeta(network_name="mainnet")
        assert mainnet_meta.is_testnet() is False

    def test_get_network_info_method(self):
        """Test get_network_info() method returns correct dictionary."""
        start_time = datetime.datetime.now(datetime.UTC)

        meta = ChainMeta(
            network_name="mainnet",
            start_time=start_time,
            version="13.2.0",
        )

        network_info = meta.get_network_info()

        expected_info = {
            "network_name": "mainnet",
            "is_mainnet": True,
            "is_testnet": False,
            "start_time": start_time,
            "version": "13.2.0",
        }

        assert network_info == expected_info

    def test_chainmeta_table_name(self):
        """Test ChainMeta has correct table name."""
        assert ChainMeta.__tablename__ == "meta"

    def test_chainmeta_primary_key(self):
        """Test ChainMeta has primary key field."""
        meta = ChainMeta()
        assert hasattr(meta, "id_")
        assert meta.id_ is None  # Should be None for new instances

    def test_chainmeta_field_types(self):
        """Test ChainMeta field type annotations."""
        # Check that key fields have correct type annotations
        annotations = ChainMeta.__annotations__

        assert "id_" in annotations
        assert "network_name" in annotations
        assert "start_time" in annotations
        assert "version" in annotations

    def test_chainmeta_minimal_data(self):
        """Test ChainMeta with minimal data."""
        meta = ChainMeta(
            network_name="testnet",
        )

        assert meta.network_name == "testnet"
        assert meta.version is None
        assert meta.start_time is None

    def test_chainmeta_repr(self):
        """Test ChainMeta string representation."""
        meta = ChainMeta(network_name="testnet")
        repr_str = repr(meta)

        # Should include class name
        assert "ChainMeta" in repr_str
        assert "(" in repr_str and ")" in repr_str


class TestFoundationModelTypes:
    """Test suite for foundation model custom types and utilities."""

    def test_chainmeta_inheritance(self):
        """Test ChainMeta inherits from DBSyncBase."""
        from dbsync.models.base import DBSyncBase

        meta = ChainMeta()
        assert isinstance(meta, DBSyncBase)

    def test_chainmeta_has_base_methods(self):
        """Test ChainMeta has inherited base methods."""
        meta = ChainMeta(network_name="mainnet")

        # Should have base methods from DBSyncBase
        assert hasattr(meta, "to_dict")
        assert hasattr(meta, "update_from_dict")
        assert hasattr(meta, "get_column_names")


class TestFoundationModelIntegration:
    """Integration tests for SCHEMA-002 foundation models."""

    def test_chainmeta_full_lifecycle(self):
        """Test complete ChainMeta model lifecycle."""
        # Create instance
        meta = ChainMeta(
            network_name="mainnet",
            version="13.2.0",
            start_time=datetime.datetime.now(datetime.UTC),
        )

        # Test methods
        assert meta.is_mainnet() is True
        assert meta.is_testnet() is False

        network_info = meta.get_network_info()
        assert network_info["network_name"] == "mainnet"
        assert network_info["is_mainnet"] is True

        # Test string representation
        repr_str = repr(meta)
        assert "ChainMeta" in repr_str

    def test_chainmeta_edge_cases(self):
        """Test ChainMeta with edge cases and None values."""
        # Test with minimal data
        meta = ChainMeta()

        # Methods should handle None values gracefully
        assert meta.is_mainnet() is False  # Should default to False
        assert meta.is_testnet() is False  # Should default to False

        network_info = meta.get_network_info()
        assert network_info["network_name"] is None
        assert network_info["is_mainnet"] is False
        assert network_info["is_testnet"] is False

    def test_chainmeta_network_detection(self):
        """Test network detection with network_name only."""
        # Test testnet detection
        meta = ChainMeta(network_name="testnet")

        # network_name should work for testnet detection
        assert meta.is_testnet() is True
        assert meta.is_mainnet() is False


class TestExtraMigrations:
    """Test cases for ExtraMigrations model."""

    def test_extra_migrations_creation(self):
        """Test basic ExtraMigrations model creation."""
        migration = ExtraMigrations(
            token="migration_v2_performance_indexes",
            description="Add performance indexes for query optimization",
        )

        assert migration.token == "migration_v2_performance_indexes"
        assert migration.description == "Add performance indexes for query optimization"

    def test_extra_migrations_table_name(self):
        """Test ExtraMigrations table name."""
        assert ExtraMigrations.__tablename__ == "extra_migrations"

    def test_extra_migrations_fields(self):
        """Test ExtraMigrations field definitions."""
        migration = ExtraMigrations()

        # Check field existence
        assert hasattr(migration, "id_")
        assert hasattr(migration, "token")
        assert hasattr(migration, "description")

    def test_extra_migrations_with_minimal_data(self):
        """Test ExtraMigrations with minimal required data."""
        migration = ExtraMigrations(
            token="test_migration",
        )

        assert migration.token == "test_migration"
        assert migration.description is None

    def test_extra_migrations_unique_token(self):
        """Test ExtraMigrations token should be unique."""
        token = "unique_migration_token"
        migration = ExtraMigrations(
            token=token,
            description="Test migration for uniqueness",
        )

        assert migration.token == token
        # In a real database, this would enforce uniqueness
        # Here we just test that the field can hold the value

    def test_extra_migrations_long_description(self):
        """Test ExtraMigrations with long description."""
        long_description = "This is a very long description " * 20
        migration = ExtraMigrations(
            token="long_desc_migration",
            description=long_description,
        )

        assert migration.token == "long_desc_migration"
        assert migration.description == long_description
        assert len(migration.description) > 500


class TestEventInfo:
    """Test cases for EventInfo model."""

    def test_event_info_creation(self):
        """Test basic EventInfo model creation."""
        from datetime import datetime

        event_time = datetime.now()
        event = EventInfo(
            event_name="db_sync_startup",
            event_time=event_time,
            description="Database synchronization service started successfully",
            severity="INFO",
        )

        assert event.event_name == "db_sync_startup"
        assert event.event_time == event_time
        assert (
            event.description == "Database synchronization service started successfully"
        )
        assert event.severity == "INFO"

    def test_event_info_table_name(self):
        """Test EventInfo table name."""
        assert EventInfo.__tablename__ == "event_info"

    def test_event_info_fields(self):
        """Test EventInfo field definitions."""
        event = EventInfo()

        # Check field existence
        assert hasattr(event, "id_")
        assert hasattr(event, "event_name")
        assert hasattr(event, "event_time")
        assert hasattr(event, "description")
        assert hasattr(event, "severity")

    def test_event_info_with_minimal_data(self):
        """Test EventInfo with minimal required data."""
        event = EventInfo(
            event_name="test_event",
        )

        assert event.event_name == "test_event"
        assert event.event_time is None
        assert event.description is None
        assert event.severity is None

    def test_event_info_severity_levels(self):
        """Test EventInfo with different severity levels."""
        severities = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for severity in severities:
            event = EventInfo(
                event_name=f"test_event_{severity.lower()}",
                severity=severity,
            )
            assert event.severity == severity

    def test_event_info_error_event(self):
        """Test EventInfo for error event."""
        from datetime import datetime

        event = EventInfo(
            event_name="connection_failure",
            event_time=datetime.now(),
            description="Failed to connect to Cardano node: Connection timeout",
            severity="ERROR",
        )

        assert event.event_name == "connection_failure"
        assert event.severity == "ERROR"
        assert "Connection timeout" in event.description

    def test_event_info_warning_event(self):
        """Test EventInfo for warning event."""
        from datetime import datetime

        event = EventInfo(
            event_name="sync_lag_detected",
            event_time=datetime.now(),
            description="Synchronization is lagging behind by 5 blocks",
            severity="WARNING",
        )

        assert event.event_name == "sync_lag_detected"
        assert event.severity == "WARNING"
        assert "lagging behind" in event.description

    def test_event_info_long_description(self):
        """Test EventInfo with long description."""
        long_description = "This is a detailed error description " * 50
        event = EventInfo(
            event_name="detailed_error",
            description=long_description,
            severity="ERROR",
        )

        assert event.event_name == "detailed_error"
        assert event.description == long_description
        assert len(event.description) > 1000


# Note: SCHEMA-003 (Core Blockchain Infrastructure Models) tests are in test_blockchain_models.py
