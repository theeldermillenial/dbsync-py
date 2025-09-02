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
        event = EventInfo(
            epoch=1,
            type="db_sync_startup",
            explanation="Database synchronization service started successfully",
            tx_id=12345,
        )

        assert event.epoch == 1
        assert event.type == "db_sync_startup"
        assert event.explanation == "Database synchronization service started successfully"
        assert event.tx_id == 12345

    def test_event_info_table_name(self):
        """Test EventInfo table name."""
        assert EventInfo.__tablename__ == "event_info"

    def test_event_info_fields(self):
        """Test EventInfo field definitions."""
        event = EventInfo()

        # Check field existence
        assert hasattr(event, "id_")
        assert hasattr(event, "tx_id")
        assert hasattr(event, "epoch")
        assert hasattr(event, "type")
        assert hasattr(event, "explanation")

    def test_event_info_with_minimal_data(self):
        """Test EventInfo with minimal required data."""
        event = EventInfo(
            epoch=1,
            type="test_event",
        )

        assert event.epoch == 1
        assert event.type == "test_event"
        assert event.tx_id is None
        assert event.explanation is None

    def test_event_info_different_types(self):
        """Test EventInfo with different event types."""
        event_types = ["sync_start", "sync_complete", "error", "warning", "info"]

        for event_type in event_types:
            event = EventInfo(
                epoch=1,
                type=event_type,
            )
            assert event.type == event_type

    def test_event_info_error_event(self):
        """Test EventInfo for error event."""
        event = EventInfo(
            epoch=5,
            type="connection_failure",
            explanation="Failed to connect to Cardano node: Connection timeout",
        )

        assert event.type == "connection_failure"
        assert event.epoch == 5
        assert "Connection timeout" in event.explanation

    def test_event_info_warning_event(self):
        """Test EventInfo for warning event."""
        event = EventInfo(
            epoch=10,
            type="sync_lag_detected",
            explanation="Synchronization is lagging behind by 5 blocks",
        )

        assert event.type == "sync_lag_detected"
        assert event.epoch == 10
        assert "lagging behind" in event.explanation

    def test_event_info_long_explanation(self):
        """Test EventInfo with long explanation."""
        long_explanation = "This is a detailed error explanation " * 50
        event = EventInfo(
            epoch=1,
            type="detailed_error",
            explanation=long_explanation,
        )

        assert event.type == "detailed_error"
        assert event.explanation == long_explanation
        assert len(event.explanation) > 1000


# Note: SCHEMA-003 (Core Blockchain Infrastructure Models) tests are in test_blockchain_models.py
