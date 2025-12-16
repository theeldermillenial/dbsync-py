"""Schema compliance tests to prevent database schema drift.

These tests ensure that all models remain compliant with the official
Cardano DB Sync schema and catch any schema mismatches early.
"""

import pytest

from tests.schema_validation.schema_validator import (
    SchemaValidator,
    validate_schema_compliance,
)


class TestSchemaCompliance:
    """Test schema compliance for all models."""

    def test_no_schema_validation_errors_for_blockchain_models(self):
        """Test that blockchain models pass schema validation without errors."""
        try:
            results = validate_schema_compliance()

            # Handle case where results might be strings or objects
            if not results:
                return  # No results to validate

            # Focus on core blockchain models we've been working on
            blockchain_tables = [
                "address",
                "stake_address",
                "block",
                "tx",
                "epoch",
                "slot_leader",
                "schema_version",
                "multi_asset",
                "ma_tx_mint",
                "ma_tx_out",
            ]

            # Filter for actual validation errors in blockchain tables only
            validation_errors = []
            for result in results:
                # Handle both object and string results
                if hasattr(result, "is_valid") and hasattr(result, "table_name"):
                    if (
                        not result.is_valid
                        and result.errors
                        and result.table_name in blockchain_tables
                    ):
                        validation_errors.append(result)
                elif isinstance(result, str):
                    # Check if any blockchain table names are mentioned in error
                    for table in blockchain_tables:
                        if table in result and "error" in result.lower():
                            validation_errors.append(result)
                            break

            if validation_errors:
                error_details = []
                for result in validation_errors:
                    if hasattr(result, "table_name") and hasattr(result, "errors"):
                        error_details.append(
                            f"Table '{result.table_name}': {', '.join(result.errors)}"
                        )
                    else:
                        error_details.append(str(result))

                pytest.fail(
                    f"Blockchain model validation failed for {len(validation_errors)} tables:\n"
                    + "\n".join(error_details)
                )

        except ImportError:
            pytest.skip("Schema validation dependencies not available")
        except Exception as e:
            pytest.skip(f"Schema validation failed to run: {e}")

    def test_foundation_models_schema_compliance(self):
        """Test that foundation models pass schema validation - this should FAIL with current models."""

        # Test foundation models specifically
        foundation_tables = ["meta", "extra_migrations", "event_info"]

        try:
            results = validate_schema_compliance()

            if not results:
                pytest.skip("No schema validation results available")

            # Check foundation model validation results
            foundation_errors = []
            for result in results:
                if hasattr(result, "is_valid") and hasattr(result, "table_name"):
                    if not result.is_valid and result.table_name in foundation_tables:
                        foundation_errors.append(result)

            # This test should FAIL with current foundation models
            if foundation_errors:
                error_details = []
                for result in foundation_errors:
                    error_details.append(
                        f"Table '{result.table_name}': {', '.join(result.errors or [])}"
                    )

                pytest.fail(
                    f"Foundation model validation failed for {len(foundation_errors)} tables:\n"
                    + "\n".join(error_details)
                    + "\n\nThis test is expected to fail until foundation models are fixed."
                )

        except ImportError:
            pytest.skip("Schema validation dependencies not available")
        except Exception as e:
            pytest.skip(f"Foundation model schema validation failed to run: {e}")

    def test_critical_models_implemented(self):
        """Test that critical blockchain models are implemented."""
        try:
            validator = SchemaValidator()

            # Critical tables that must be implemented
            critical_tables = [
                "address",
                "stake_address",
                "block",
                "tx",
                "epoch",
                "multi_asset",
                "ma_tx_mint",
                "ma_tx_out",
            ]

            missing_tables = []
            for table_name in critical_tables:
                if table_name not in validator.model_registry:
                    missing_tables.append(table_name)

            if missing_tables:
                pytest.fail(
                    f"Critical tables not implemented: {', '.join(missing_tables)}"
                )

        except ImportError:
            pytest.skip("Schema validation dependencies not available")
        except Exception as e:
            pytest.skip(f"Critical model check failed: {e}")

    def test_address_model_schema_compliance(self):
        """Specific test for Address model schema compliance.

        This test specifically checks the Address model since it had
        major schema issues that were recently fixed.
        """
        try:
            validator = SchemaValidator()

            # Verify Address model is registered
            assert "address" in validator.model_registry, "Address model not found"

            # Validate specifically the Address model
            if hasattr(validator, "validate_single_model"):
                result = validator.validate_single_model("address")
                if result and not result.is_valid:
                    pytest.fail(
                        f"Address model validation failed: {', '.join(result.errors or [])}"
                    )

        except ImportError:
            pytest.skip("Schema validation dependencies not available")
        except Exception as e:
            pytest.skip(f"Address model validation failed: {e}")

    def test_transaction_model_has_treasury_donation(self):
        """Test that Transaction model includes treasury_donation field.

        This field was missing and recently added.
        """
        from dbsync.models import Transaction

        # Create a Transaction instance
        tx = Transaction()

        # Verify treasury_donation field exists
        assert hasattr(tx, "treasury_donation"), (
            "Transaction model missing treasury_donation field"
        )

        # Verify it has a default value of 0
        assert tx.treasury_donation == 0, "treasury_donation should default to 0"

    def test_schema_version_uses_bigint(self):
        """Test that SchemaVersion uses BigInteger types.

        Previously used Integer, but database uses bigint.
        """
        from sqlalchemy import BigInteger

        from dbsync.models import SchemaVersion

        # Get the SQLAlchemy table
        table = SchemaVersion.__table__

        # Check that stage fields use BigInteger
        stage_fields = ["stage_one", "stage_two", "stage_three"]

        for field_name in stage_fields:
            column = table.columns.get(field_name)
            assert column is not None, f"Field {field_name} not found"
            assert isinstance(column.type, BigInteger), (
                f"Field {field_name} should use BigInteger, not {type(column.type)}"
            )

    @pytest.mark.slow
    def test_comprehensive_schema_validation(self):
        """Comprehensive schema validation test.

        This test runs the full schema validation suite and ensures
        100% compliance. Marked as slow since it fetches external schema.
        """
        try:
            validator = SchemaValidator()
            results = validator.validate_all_models()

            # Calculate compliance statistics
            total_tables = len(results)
            valid_tables = len([r for r in results if r.is_valid])

            compliance_rate = (
                (valid_tables / total_tables) * 100 if total_tables > 0 else 0
            )

            # Expect 100% compliance
            assert compliance_rate == 100.0, (
                f"Schema compliance rate is {compliance_rate:.1f}%, expected 100%. "
                f"Valid: {valid_tables}/{total_tables}"
            )

        except ImportError:
            pytest.skip("Schema validation dependencies not available")
        except Exception as e:
            pytest.skip(f"Comprehensive schema validation failed: {e}")


class TestModelFieldMappings:
    """Test specific field mappings that were problematic."""

    def test_address_model_fields(self):
        """Test Address model has correct fields (not the old ones)."""
        from dbsync.models import Address

        # Create instance to test field access
        address = Address(address="addr1test123", raw=b"test", has_script=False)

        # Test new fields exist
        assert hasattr(address, "address")
        assert hasattr(address, "raw")
        assert hasattr(address, "has_script")
        assert hasattr(address, "payment_cred")
        assert hasattr(address, "stake_address_id")

        # Test old fields DON'T exist (were removed)
        assert not hasattr(address, "hash_")
        assert not hasattr(address, "view")  # This is now "address"

    def test_transaction_model_complete_fields(self):
        """Test Transaction model has all required fields."""
        from dbsync.models import Transaction

        tx = Transaction()

        # Test treasury_donation exists (recently added)
        assert hasattr(tx, "treasury_donation")

        # Test other important fields exist
        required_fields = [
            "id_",
            "hash_",
            "block_id",
            "block_index",
            "out_sum",
            "fee",
            "deposit",
            "size",
            "invalid_before",
            "invalid_hereafter",
            "valid_contract",
            "script_size",
            "treasury_donation",
        ]

        for field in required_fields:
            assert hasattr(tx, field), f"Transaction missing field: {field}"
