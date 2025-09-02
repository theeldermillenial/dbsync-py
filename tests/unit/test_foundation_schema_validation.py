"""Comprehensive schema validation tests for foundation models.

These tests validate that foundation models exactly match the database schema
and will fail if there are any mismatches. Unlike the existing schema validation,
these tests are designed to run in the standard test suite and catch issues.
"""

import pytest
from sqlalchemy import inspect, MetaData, Table, Column, BigInteger, Integer, String, Text, DateTime, Boolean
from sqlalchemy.types import TypeDecorator

from dbsync.models.foundation import ChainMeta, EventInfo, ExtraMigrations


class TestFoundationModelSchemaValidation:
    """Validate foundation models against expected database schema."""

    def test_chain_meta_model_has_required_fields(self):
        """Test ChainMeta model has all required fields with correct types."""
        
        # Create model instance to access its table definition
        meta = ChainMeta()
        table = meta.__table__
        
        # Expected fields based on database schema analysis
        expected_fields = {
            'id': {'type_class': BigInteger, 'nullable': False, 'primary_key': True},
            'start_time': {'type_class': DateTime, 'nullable': False, 'primary_key': False},
            'network_name': {'type_class': (String, Text), 'nullable': False, 'primary_key': False},
            'version': {'type_class': (String, Text), 'nullable': False, 'primary_key': False},
        }
        
        # Get actual model columns
        actual_columns = {col.name: col for col in table.columns}
        
        # Check all expected fields exist
        for field_name, expected_props in expected_fields.items():
            assert field_name in actual_columns, f"ChainMeta missing required field: {field_name}"
            
            col = actual_columns[field_name]
            
            # Check type
            expected_types = expected_props['type_class']
            if not isinstance(expected_types, tuple):
                expected_types = (expected_types,)
            
            # Handle custom types and type decorators
            col_type = col.type
            if isinstance(col_type, TypeDecorator):
                col_type = col_type.impl
            
            type_matches = any(isinstance(col_type, expected_type) for expected_type in expected_types)
            assert type_matches, (
                f"ChainMeta.{field_name} has wrong type: "
                f"expected one of {expected_types}, got {type(col_type)}"
            )
            
            # Check nullability
            assert col.nullable == expected_props['nullable'], (
                f"ChainMeta.{field_name} nullability mismatch: "
                f"expected {expected_props['nullable']}, got {col.nullable}"
            )
            
            # Check primary key
            assert col.primary_key == expected_props['primary_key'], (
                f"ChainMeta.{field_name} primary_key mismatch: "
                f"expected {expected_props['primary_key']}, got {col.primary_key}"
            )

    def test_chain_meta_model_sa_column_definitions(self):
        """Test ChainMeta model has proper sa_column definitions for all fields."""
        
        meta = ChainMeta()
        table = meta.__table__
        
        # All fields should have proper column definitions
        required_columns = ['id', 'start_time', 'network_name', 'version']
        actual_columns = [col.name for col in table.columns]
        
        for col_name in required_columns:
            assert col_name in actual_columns, (
                f"ChainMeta missing sa_column definition for {col_name}. "
                f"Available columns: {actual_columns}"
            )

    def test_chain_meta_timezone_configuration(self):
        """Test ChainMeta start_time field has correct timezone configuration."""
        
        meta = ChainMeta()
        table = meta.__table__
        
        start_time_col = table.columns.get('start_time')
        assert start_time_col is not None, "start_time column should exist"
        
        # Check timezone configuration
        if hasattr(start_time_col.type, 'timezone'):
            # Database uses 'timestamp without time zone', so timezone should be False
            assert start_time_col.type.timezone is False, (
                "start_time should use DateTime(timezone=False) to match database schema"
            )

    def test_extra_migrations_model_has_required_fields(self):
        """Test ExtraMigrations model has all required fields with correct types."""
        
        migration = ExtraMigrations()
        table = migration.__table__
        
        # Expected fields based on database schema analysis
        expected_fields = {
            'id': {'type_class': BigInteger, 'nullable': False, 'primary_key': True},
            'token': {'type_class': (String, Text), 'nullable': False, 'primary_key': False},
            'description': {'type_class': (String, Text), 'nullable': True, 'primary_key': False},
        }
        
        # Get actual model columns
        actual_columns = {col.name: col for col in table.columns}
        
        # Check all expected fields exist
        for field_name, expected_props in expected_fields.items():
            assert field_name in actual_columns, f"ExtraMigrations missing required field: {field_name}"
            
            col = actual_columns[field_name]
            
            # Check type
            expected_types = expected_props['type_class']
            if not isinstance(expected_types, tuple):
                expected_types = (expected_types,)
            
            # Handle custom types and type decorators
            col_type = col.type
            if isinstance(col_type, TypeDecorator):
                col_type = col_type.impl
            
            type_matches = any(isinstance(col_type, expected_type) for expected_type in expected_types)
            assert type_matches, (
                f"ExtraMigrations.{field_name} has wrong type: "
                f"expected one of {expected_types}, got {type(col_type)}"
            )
            
            # Check nullability
            assert col.nullable == expected_props['nullable'], (
                f"ExtraMigrations.{field_name} nullability mismatch: "
                f"expected {expected_props['nullable']}, got {col.nullable}"
            )

    def test_extra_migrations_token_unique_constraint(self):
        """Test ExtraMigrations token field has unique constraint."""
        
        migration = ExtraMigrations()
        table = migration.__table__
        
        token_col = table.columns.get('token')
        assert token_col is not None, "token column should exist"
        
        # Check for unique constraint
        # Note: This test will fail with current model as unique constraint is missing
        assert token_col.unique, "token field should have unique=True constraint"

    def test_extra_migrations_description_type_consistency(self):
        """Test ExtraMigrations description field uses consistent type."""
        
        migration = ExtraMigrations()
        table = migration.__table__
        
        description_col = table.columns.get('description')
        assert description_col is not None, "description column should exist"
        
        # Should use String type to match database character varying, not Text
        col_type = description_col.type
        if isinstance(col_type, TypeDecorator):
            col_type = col_type.impl
            
        # This test will fail if using Text instead of String
        assert isinstance(col_type, String), (
            f"description should use String type to match database character varying, "
            f"not {type(col_type)}"
        )

    def test_event_info_model_schema_mismatch_detection(self):
        """Test that EventInfo model schema mismatch is detected."""
        
        event = EventInfo()
        table = event.__table__
        
        # Expected fields based on actual database schema
        expected_db_fields = {
            'id': {'type_class': BigInteger, 'nullable': False, 'primary_key': True},
            'tx_id': {'type_class': BigInteger, 'nullable': True, 'primary_key': False},
            'epoch': {'type_class': (BigInteger, int), 'nullable': False, 'primary_key': False},  # Integer in DB
            'type': {'type_class': (String, Text), 'nullable': False, 'primary_key': False},
            'explanation': {'type_class': (String, Text), 'nullable': True, 'primary_key': False},
        }
        
        # Get actual model columns
        actual_columns = {col.name: col for col in table.columns}
        
        # Check for fields that should exist but don't (missing fields)
        missing_fields = []
        for field_name in expected_db_fields:
            if field_name not in actual_columns:
                missing_fields.append(field_name)
        
        # Check for fields that exist but shouldn't (extra fields)
        extra_fields = []
        expected_field_names = set(expected_db_fields.keys())
        for field_name in actual_columns:
            if field_name not in expected_field_names:
                extra_fields.append(field_name)
        
        # This test should FAIL with current EventInfo model
        assert not missing_fields, (
            f"EventInfo model missing required database fields: {missing_fields}. "
            f"Database expects: {list(expected_db_fields.keys())}, "
            f"Model has: {list(actual_columns.keys())}"
        )
        
        assert not extra_fields, (
            f"EventInfo model has extra fields not in database: {extra_fields}. "
            f"Database expects: {list(expected_db_fields.keys())}, "
            f"Model has: {list(actual_columns.keys())}"
        )

    def test_event_info_model_field_types_match_database(self):
        """Test EventInfo model field types match database schema."""
        
        event = EventInfo()
        table = event.__table__
        
        # This test will only run if the model has the correct fields
        # It will be skipped if the model is completely wrong
        
        expected_types = {
            'id': BigInteger,
            'tx_id': BigInteger, 
            'epoch': (BigInteger, Integer),  # Database uses integer type
            'type': (String, Text),
            'explanation': (String, Text),
        }
        
        actual_columns = {col.name: col for col in table.columns}
        
        for field_name, expected_type_classes in expected_types.items():
            if field_name not in actual_columns:
                pytest.skip(f"EventInfo model missing field {field_name} - cannot test type")
                
            col = actual_columns[field_name]
            
            if not isinstance(expected_type_classes, tuple):
                expected_type_classes = (expected_type_classes,)
            
            # Handle custom types and type decorators
            col_type = col.type
            if isinstance(col_type, TypeDecorator):
                col_type = col_type.impl
            
            type_matches = any(isinstance(col_type, expected_type) for expected_type in expected_type_classes)
            assert type_matches, (
                f"EventInfo.{field_name} has wrong type: "
                f"expected one of {expected_type_classes}, got {type(col_type)}"
            )


class TestFoundationModelFieldMappings:
    """Test that model fields properly map to database columns."""

    def test_chain_meta_field_annotations_vs_actual_columns(self):
        """Test ChainMeta field annotations match actual SQLAlchemy columns."""
        
        # Get model field annotations
        annotations = ChainMeta.__annotations__
        
        # Get actual table columns
        meta = ChainMeta()
        table_columns = {col.name: col for col in meta.__table__.columns}
        
        # Map model field names to database column names
        field_to_column_mapping = {
            'id_': 'id',
            'start_time': 'start_time',
            'network_name': 'network_name', 
            'version': 'version',
        }
        
        # Check that annotated fields have corresponding columns
        for field_name, column_name in field_to_column_mapping.items():
            assert field_name in annotations, f"ChainMeta missing field annotation: {field_name}"
            assert column_name in table_columns, f"ChainMeta missing database column: {column_name}"

    def test_extra_migrations_field_annotations_vs_actual_columns(self):
        """Test ExtraMigrations field annotations match actual SQLAlchemy columns."""
        
        # Get model field annotations
        annotations = ExtraMigrations.__annotations__
        
        # Get actual table columns
        migration = ExtraMigrations()
        table_columns = {col.name: col for col in migration.__table__.columns}
        
        # Map model field names to database column names
        field_to_column_mapping = {
            'id_': 'id',
            'token': 'token',
            'description': 'description',
        }
        
        # Check that annotated fields have corresponding columns
        for field_name, column_name in field_to_column_mapping.items():
            assert field_name in annotations, f"ExtraMigrations missing field annotation: {field_name}"
            assert column_name in table_columns, f"ExtraMigrations missing database column: {column_name}"

    def test_event_info_field_annotations_vs_database_schema(self):
        """Test EventInfo field annotations should match database schema."""
        
        # Get model field annotations
        annotations = EventInfo.__annotations__
        
        # Expected field mappings based on database schema
        expected_field_to_column_mapping = {
            'id_': 'id',
            'tx_id': 'tx_id',
            'epoch': 'epoch',
            'type': 'type',
            'explanation': 'explanation',
        }
        
        # Check that model should have these field annotations
        for field_name in expected_field_to_column_mapping:
            # This will fail because EventInfo has wrong fields
            assert field_name in annotations, (
                f"EventInfo missing required field annotation: {field_name}. "
                f"Model has: {list(annotations.keys())}, "
                f"Should have: {list(expected_field_to_column_mapping.keys())}"
            )


class TestFoundationModelTableNames:
    """Test that model table names match database tables."""

    def test_chain_meta_table_name(self):
        """Test ChainMeta uses correct table name."""
        assert ChainMeta.__tablename__ == "meta", f"ChainMeta should use table name 'meta', not '{ChainMeta.__tablename__}'"

    def test_extra_migrations_table_name(self):
        """Test ExtraMigrations uses correct table name."""
        assert ExtraMigrations.__tablename__ == "extra_migrations", f"ExtraMigrations should use table name 'extra_migrations', not '{ExtraMigrations.__tablename__}'"

    def test_event_info_table_name(self):
        """Test EventInfo uses correct table name."""
        assert EventInfo.__tablename__ == "event_info", f"EventInfo should use table name 'event_info', not '{EventInfo.__tablename__}'"


class TestFoundationModelInstantiation:
    """Test that models can be instantiated without errors."""

    def test_chain_meta_instantiation_with_required_fields(self):
        """Test ChainMeta can be instantiated with required fields."""
        
        from datetime import datetime
        
        # Based on database schema, these fields are required (NOT NULL)
        try:
            meta = ChainMeta(
                start_time=datetime(2017, 9, 23, 21, 44, 51),  # Cardano mainnet genesis
                network_name="testnet",
                version="13.2.0"
            )
            
            # Check that required fields are set
            assert meta.start_time is not None, "start_time should be provided and not None"
            assert meta.network_name == "testnet"
            assert meta.version == "13.2.0"
            
        except Exception as e:
            pytest.fail(f"ChainMeta instantiation failed: {e}")

    def test_extra_migrations_instantiation_with_required_fields(self):
        """Test ExtraMigrations can be instantiated with required fields."""
        
        try:
            migration = ExtraMigrations(
                token="test_migration_token"
                # description is optional (nullable in DB)
            )
            
            assert migration.token == "test_migration_token"
            assert migration.description is None  # Should be allowed
            
        except Exception as e:
            pytest.fail(f"ExtraMigrations instantiation failed: {e}")

    def test_event_info_instantiation_reveals_field_mismatch(self):
        """Test EventInfo instantiation reveals field mismatch with database."""
        
        # Current model allows these fields (which don't exist in DB)
        try:
            event = EventInfo(
                event_name="test_event",      # ❌ Doesn't exist in DB
                event_time=None,              # ❌ Doesn't exist in DB
                description="test desc",      # ❌ Doesn't exist in DB  
                severity="INFO"               # ❌ Doesn't exist in DB
            )
            
            # Model allows this, but it's completely wrong for the database
            # The test should document this mismatch
            
            # Database actually requires these fields:
            required_db_fields = ['tx_id', 'epoch', 'type', 'explanation']
            model_fields = [attr for attr in dir(event) if not attr.startswith('_')]
            
            missing_db_fields = [field for field in required_db_fields if field not in model_fields]
            
            assert not missing_db_fields, (
                f"EventInfo model missing database fields: {missing_db_fields}. "
                f"Model has wrong fields entirely."
            )
            
        except Exception as e:
            pytest.fail(f"EventInfo instantiation failed: {e}")
