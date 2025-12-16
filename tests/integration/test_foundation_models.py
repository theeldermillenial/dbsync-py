"""Integration tests for foundation models against actual database schema.

These tests validate that foundation models work correctly with the actual
Cardano DB Sync database schema and catch schema mismatches.
"""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import DataError, IntegrityError

from dbsync.models.foundation import ChainMeta, EventInfo, ExtraMigrations
from tests.integration.base import BaseIntegrationTest


class TestFoundationModelsIntegration(BaseIntegrationTest):
    """Integration tests for foundation models with real database."""

    def test_chain_meta_table_exists(self, dbsync_session):
        """Test that meta table exists and matches model expectations."""
        # Verify table exists
        assert self.verify_table_exists(dbsync_session, "meta"), (
            "meta table should exist"
        )

        # Get table count to ensure it's accessible
        count = self.get_table_count(dbsync_session, "meta")
        assert count >= 0, "Should be able to query meta table"

    def test_extra_migrations_table_exists(self, dbsync_session):
        """Test that extra_migrations table exists and matches model expectations."""
        # Verify table exists
        assert self.verify_table_exists(dbsync_session, "extra_migrations"), (
            "extra_migrations table should exist"
        )

        # Get table count to ensure it's accessible
        count = self.get_table_count(dbsync_session, "extra_migrations")
        assert count >= 0, "Should be able to query extra_migrations table"

    def test_event_info_table_exists(self, dbsync_session):
        """Test that event_info table exists and matches model expectations."""
        # Verify table exists
        assert self.verify_table_exists(dbsync_session, "event_info"), (
            "event_info table should exist"
        )

        # Get table count to ensure it's accessible
        count = self.get_table_count(dbsync_session, "event_info")
        assert count >= 0, "Should be able to query event_info table"

    def test_chain_meta_database_schema_compliance(self, dbsync_session):
        """Test ChainMeta model fields match actual database schema."""
        # Get actual database schema for meta table
        inspector = inspect(dbsync_session.bind)
        columns = inspector.get_columns("meta")

        # Convert to dict for easier lookup
        db_columns = {col["name"]: col for col in columns}

        # Check required fields exist in database
        required_db_fields = ["id", "start_time", "network_name", "version"]
        for field in required_db_fields:
            assert field in db_columns, f"Database missing required field: {field}"

        # Check field nullability matches database
        assert not db_columns["id"]["nullable"], "id should be NOT NULL"
        assert not db_columns["start_time"]["nullable"], "start_time should be NOT NULL"
        assert not db_columns["network_name"]["nullable"], (
            "network_name should be NOT NULL"
        )
        assert not db_columns["version"]["nullable"], "version should be NOT NULL"

        # Check data types
        assert "bigint" in str(db_columns["id"]["type"]).lower(), "id should be bigint"
        assert "timestamp" in str(db_columns["start_time"]["type"]).lower(), (
            "start_time should be timestamp"
        )
        assert (
            "varchar" in str(db_columns["network_name"]["type"]).lower()
            or "character varying" in str(db_columns["network_name"]["type"]).lower()
        ), "network_name should be varchar"
        assert (
            "varchar" in str(db_columns["version"]["type"]).lower()
            or "character varying" in str(db_columns["version"]["type"]).lower()
        ), "version should be varchar"

    def test_extra_migrations_database_schema_compliance(self, dbsync_session):
        """Test ExtraMigrations model fields match actual database schema."""
        # Get actual database schema for extra_migrations table
        inspector = inspect(dbsync_session.bind)
        columns = inspector.get_columns("extra_migrations")

        # Convert to dict for easier lookup
        db_columns = {col["name"]: col for col in columns}

        # Check required fields exist in database
        required_db_fields = ["id", "token", "description"]
        for field in required_db_fields:
            assert field in db_columns, f"Database missing required field: {field}"

        # Check field nullability matches database
        assert not db_columns["id"]["nullable"], "id should be NOT NULL"
        assert not db_columns["token"]["nullable"], "token should be NOT NULL"
        assert db_columns["description"]["nullable"], "description should be nullable"

        # Check data types
        assert "bigint" in str(db_columns["id"]["type"]).lower(), "id should be bigint"
        assert (
            "varchar" in str(db_columns["token"]["type"]).lower()
            or "character varying" in str(db_columns["token"]["type"]).lower()
        ), "token should be varchar"
        assert (
            "varchar" in str(db_columns["description"]["type"]).lower()
            or "character varying" in str(db_columns["description"]["type"]).lower()
        ), "description should be varchar"

    def test_event_info_database_schema_compliance(self, dbsync_session):
        """Test EventInfo model fields match actual database schema."""
        # Get actual database schema for event_info table
        inspector = inspect(dbsync_session.bind)
        columns = inspector.get_columns("event_info")

        # Convert to dict for easier lookup
        db_columns = {col["name"]: col for col in columns}

        # Check what fields actually exist in database
        actual_db_fields = set(db_columns.keys())
        expected_db_fields = {"id", "tx_id", "epoch", "type", "explanation"}

        # Verify database has expected fields
        for field in expected_db_fields:
            assert field in actual_db_fields, (
                f"Database missing expected field: {field}"
            )

        # Check field nullability matches database
        assert not db_columns["id"]["nullable"], "id should be NOT NULL"
        assert db_columns["tx_id"]["nullable"], "tx_id should be nullable"
        assert not db_columns["epoch"]["nullable"], "epoch should be NOT NULL"
        assert not db_columns["type"]["nullable"], "type should be NOT NULL"
        assert db_columns["explanation"]["nullable"], "explanation should be nullable"

        # Check data types
        assert "bigint" in str(db_columns["id"]["type"]).lower(), "id should be bigint"
        assert "bigint" in str(db_columns["tx_id"]["type"]).lower(), (
            "tx_id should be bigint"
        )
        # epoch can be integer or domain type (word31type) - PostgreSQL domains show as 'domain'
        epoch_type_str = str(db_columns["epoch"]["type"]).lower()
        assert any(t in epoch_type_str for t in ["integer", "word31type", "domain"]), (
            f"epoch should be integer, word31type, or domain, got: {epoch_type_str}"
        )
        assert (
            "varchar" in str(db_columns["type"]["type"]).lower()
            or "character varying" in str(db_columns["type"]["type"]).lower()
        ), "type should be varchar"
        assert (
            "varchar" in str(db_columns["explanation"]["type"]).lower()
            or "character varying" in str(db_columns["explanation"]["type"]).lower()
        ), "explanation should be varchar"

    def test_chain_meta_model_field_mapping_issues(self, dbsync_session):
        """Test that reveals ChainMeta model field mapping issues."""
        # This test should FAIL with current model due to missing sa_column definitions

        # Try to create a ChainMeta instance and access its SQLAlchemy table
        meta = ChainMeta()

        # Check if model has proper sa_column definitions
        table = meta.__table__

        # These should exist and map to database columns
        expected_columns = ["id", "start_time", "network_name", "version"]
        actual_columns = [col.name for col in table.columns]

        for col_name in expected_columns:
            assert col_name in actual_columns, (
                f"Model missing database column mapping: {col_name}"
            )

        # Check that columns have proper types and constraints
        id_col = table.columns["id"]
        assert id_col.primary_key, "id column should be primary key"

        # These will fail with current model due to missing sa_column definitions
        start_time_col = table.columns.get("start_time")
        assert start_time_col is not None, "start_time column should exist in model"

        network_name_col = table.columns.get("network_name")
        assert network_name_col is not None, "network_name column should exist in model"

        version_col = table.columns.get("version")
        assert version_col is not None, "version column should exist in model"

    def test_event_info_model_field_mismatch(self, dbsync_session):
        """Test that reveals EventInfo model has wrong fields entirely."""
        # This test should FAIL because EventInfo model has completely wrong fields

        # Get actual database schema
        inspector = inspect(dbsync_session.bind)
        db_columns = {col["name"]: col for col in inspector.get_columns("event_info")}

        # Check what fields the model thinks it has vs what database actually has
        event = EventInfo()
        # Get model fields from the table columns (more reliable)
        model_fields = {col.name for col in event.__table__.columns}

        # Database has these fields
        db_fields = set(db_columns.keys())

        # Model should have fields that match database
        # This will fail because model has event_name, event_time, description, severity
        # but database has tx_id, epoch, type, explanation

        missing_in_model = (
            db_fields - model_fields - {"id"}
        )  # Exclude id as it's mapped to id_
        extra_in_model = (
            model_fields - db_fields - {"id_"}
        )  # Exclude id_ as it maps to id

        assert not missing_in_model, (
            f"Model missing database fields: {missing_in_model}"
        )
        assert not extra_in_model, (
            f"Model has extra fields not in database: {extra_in_model}"
        )

    def test_chain_meta_database_insert_fails_with_current_model(self, dbsync_session):
        """Test that trying to insert ChainMeta fails due to model issues."""
        # This test should FAIL with current model

        try:
            # Try to create a valid ChainMeta record
            meta = ChainMeta(network_name="testnet", version="13.2.0")

            # This should fail because:
            # 1. Missing sa_column definitions for network_name and version
            # 2. start_time is required in DB but nullable in model
            # 3. Timezone mismatch on start_time field

            dbsync_session.add(meta)
            dbsync_session.commit()

            # If we get here, the test should fail because the insert should have failed
            pytest.fail("ChainMeta insert should have failed due to model issues")

        except (IntegrityError, DataError) as e:
            # Expected - model has issues that prevent database operations
            dbsync_session.rollback()
            # This is what we expect with the broken model
            assert True, f"Expected failure due to model issues: {e}"
        except Exception as e:
            # Any other exception also indicates model problems
            dbsync_session.rollback()
            assert True, f"Model has issues preventing database operations: {e}"

    def test_extra_migrations_database_insert_reveals_issues(self, dbsync_session):
        """Test that ExtraMigrations insert reveals model issues."""

        try:
            # Try to create a valid ExtraMigrations record
            migration = ExtraMigrations(
                token="test_migration_token", description="Test migration description"
            )

            # This might fail due to:
            # 1. token field nullability mismatch
            # 2. description type mismatch (Text vs String)

            dbsync_session.add(migration)
            dbsync_session.commit()

            # Clean up if successful
            dbsync_session.delete(migration)
            dbsync_session.commit()

        except (IntegrityError, DataError) as e:
            # Expected if model has issues
            dbsync_session.rollback()
            pytest.fail(f"ExtraMigrations model has database compatibility issues: {e}")
        except Exception as e:
            dbsync_session.rollback()
            pytest.fail(f"ExtraMigrations model has issues: {e}")

    def test_event_info_database_insert_fails_completely(self, dbsync_session):
        """Test that EventInfo insert fails completely due to wrong schema."""

        try:
            # Try to create EventInfo with model fields (which are wrong)
            event = EventInfo(
                event_name="test_event",
                description="Test event description",
                severity="INFO",
            )

            # This should fail completely because the model fields
            # don't match the database schema at all

            dbsync_session.add(event)
            dbsync_session.commit()

            pytest.fail(
                "EventInfo insert should have failed - model schema is completely wrong"
            )

        except Exception as e:
            # Expected - model is completely wrong
            dbsync_session.rollback()
            assert True, f"Expected complete failure due to wrong model schema: {e}"

    def test_model_table_creation_matches_database(self, dbsync_session):
        """Test that model-generated tables would match actual database schema."""

        # Get actual database schema
        inspector = inspect(dbsync_session.bind)

        # Test each foundation model
        models_to_test = [
            (ChainMeta, "meta"),
            (ExtraMigrations, "extra_migrations"),
            (EventInfo, "event_info"),
        ]

        for model_class, table_name in models_to_test:
            # Get actual database columns
            db_columns = {col["name"]: col for col in inspector.get_columns(table_name)}

            # Get model's table definition
            model_table = model_class.__table__
            model_columns = {col.name: col for col in model_table.columns}

            # Compare column names
            db_column_names = set(db_columns.keys())
            model_column_names = set(model_columns.keys())

            missing_in_model = db_column_names - model_column_names
            extra_in_model = model_column_names - db_column_names

            assert not missing_in_model, (
                f"{model_class.__name__} missing columns: {missing_in_model}"
            )
            assert not extra_in_model, (
                f"{model_class.__name__} has extra columns: {extra_in_model}"
            )

            # Compare column properties for common columns
            common_columns = db_column_names & model_column_names
            for col_name in common_columns:
                db_col = db_columns[col_name]
                model_col = model_columns[col_name]

                # Check nullability
                assert db_col["nullable"] == model_col.nullable, (
                    f"{model_class.__name__}.{col_name}: "
                    f"nullability mismatch - DB: {db_col['nullable']}, "
                    f"Model: {model_col.nullable}"
                )


class TestFoundationModelsConstraints(BaseIntegrationTest):
    """Test database constraints are properly enforced."""

    def test_meta_table_not_null_constraints(self, dbsync_session):
        """Test that meta table NOT NULL constraints are enforced."""

        # Test that required fields cannot be NULL
        test_cases = [
            # Missing start_time (required in DB)
            {
                "network_name": "testnet",
                "version": "13.2.0",
                # start_time missing - should fail
            },
            # Missing network_name (required in DB)
            {
                "start_time": "2024-01-01 00:00:00",
                "version": "13.2.0",
                # network_name missing - should fail
            },
            # Missing version (required in DB)
            {
                "start_time": "2024-01-01 00:00:00",
                "network_name": "testnet",
                # version missing - should fail
            },
        ]

        for test_data in test_cases:
            try:
                # Try to insert incomplete data directly via SQL
                # This bypasses the model to test database constraints
                result = dbsync_session.execute(
                    text(f"""
                    INSERT INTO meta ({", ".join(test_data.keys())})
                    VALUES ({", ".join([f"'{v}'" for v in test_data.values()])})
                    """)
                )
                dbsync_session.commit()

                # If we get here, the constraint wasn't enforced
                pytest.fail(
                    f"Database should have rejected incomplete data: {test_data}"
                )

            except IntegrityError:
                # Expected - database enforced NOT NULL constraint
                dbsync_session.rollback()
                assert True
            except Exception as e:
                dbsync_session.rollback()
                pytest.fail(f"Unexpected error testing constraints: {e}")

    def test_extra_migrations_token_not_null_constraint(self, dbsync_session):
        """Test that extra_migrations.token NOT NULL constraint is enforced."""

        try:
            # Try to insert record without token (required field)
            result = dbsync_session.execute(
                text("INSERT INTO extra_migrations (description) VALUES ('test')")
            )
            dbsync_session.commit()

            pytest.fail("Database should have rejected record without token")

        except IntegrityError:
            # Expected - token is NOT NULL in database
            dbsync_session.rollback()
            assert True
        except Exception as e:
            dbsync_session.rollback()
            pytest.fail(f"Unexpected error: {e}")

    def test_event_info_required_fields_constraint(self, dbsync_session):
        """Test that event_info required fields are enforced."""

        # Test missing epoch (required in DB)
        try:
            result = dbsync_session.execute(
                text("INSERT INTO event_info (type) VALUES ('test_type')")
            )
            dbsync_session.commit()

            pytest.fail("Database should have rejected record without epoch")

        except IntegrityError:
            # Expected - epoch is NOT NULL in database
            dbsync_session.rollback()
            assert True
        except Exception as e:
            dbsync_session.rollback()
            pytest.fail(f"Unexpected error: {e}")

        # Test missing type (required in DB)
        try:
            result = dbsync_session.execute(
                text("INSERT INTO event_info (epoch) VALUES (1)")
            )
            dbsync_session.commit()

            pytest.fail("Database should have rejected record without type")

        except IntegrityError:
            # Expected - type is NOT NULL in database
            dbsync_session.rollback()
            assert True
        except Exception as e:
            dbsync_session.rollback()
            pytest.fail(f"Unexpected error: {e}")
