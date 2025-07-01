"""Tests for schema validation utilities."""

from unittest.mock import Mock, patch

import pytest

from tests.schema_validation.schema_validator import (
    FieldDefinition,
    SchemaValidator,
    TableDefinition,
    ValidationResult,
    generate_schema_report,
    validate_schema_compliance,
)


def test_field_definition_creation():
    """Test creating field definitions."""
    field = FieldDefinition(name="id", type_="bigint", nullable=False, primary_key=True)

    assert field.name == "id"
    assert field.type_ == "bigint"
    assert not field.nullable
    assert field.primary_key
    assert field.foreign_key is None


def test_validation_result_creation():
    """Test creating validation results."""
    result = ValidationResult(table_name="test_table")

    assert result.table_name == "test_table"
    assert result.is_valid
    assert result.errors == []
    assert result.warnings == []
    assert result.missing_fields == []
    assert result.extra_fields == []
    assert result.type_mismatches == []


def test_validator_initialization():
    """Test validator initialization."""
    validator = SchemaValidator()

    assert isinstance(validator.official_schema, dict)
    assert isinstance(validator.model_registry, dict)
    # Should have loaded models from dbsync.models
    assert len(validator.model_registry) > 0


def test_load_model_registry():
    """Test loading model registry."""
    validator = SchemaValidator()

    # Should have loaded common tables
    assert "block" in validator.model_registry
    assert "tx" in validator.model_registry
    assert "tx_out" in validator.model_registry
    assert "stake_address" in validator.model_registry


def test_parse_table_fields():
    """Test parsing table fields from markdown."""
    validator = SchemaValidator()

    table_content = """
    | `id` | `bigint` | NOT NULL | PRIMARY KEY |
    | `hash` | `bytea` | NOT NULL | UNIQUE |
    | `size` | `integer` | NULL | Size in bytes |
    """

    fields = validator._parse_table_fields(table_content)

    assert len(fields) == 3

    # Check first field
    id_field = fields[0]
    assert id_field.name == "id"
    assert id_field.type_ == "bigint"
    assert not id_field.nullable
    assert id_field.primary_key


def test_validate_field_type_compatibility():
    """Test field type validation."""
    validator = SchemaValidator()

    # Mock column with different types
    mock_column = Mock()

    # Test bigint compatibility
    mock_column.type = Mock()
    mock_column.type.__str__ = Mock(return_value="BIGINTEGER")

    official_field = FieldDefinition("id", "bigint")
    is_valid, error = validator._validate_field_type(official_field, mock_column)
    assert is_valid

    # Test custom type compatibility
    mock_column.type.__str__ = Mock(return_value="LovelaceType")
    official_field = FieldDefinition("amount", "lovelace")
    is_valid, error = validator._validate_field_type(official_field, mock_column)
    assert is_valid

    # Test incompatible types
    mock_column.type.__str__ = Mock(return_value="TEXT")
    official_field = FieldDefinition("count", "bigint")
    is_valid, error = validator._validate_field_type(official_field, mock_column)
    assert not is_valid
    assert "Type mismatch" in error


@pytest.mark.integration
def test_real_model_validation():
    """Test validation with real models."""
    validator = SchemaValidator()

    # Should have loaded real models
    assert len(validator.model_registry) > 50  # We have 79 tables implemented

    # Test specific models exist
    assert "block" in validator.model_registry
    assert "tx" in validator.model_registry
    assert "tx_out" in validator.model_registry
    assert "stake_address" in validator.model_registry


@patch("tests.schema_validation.schema_validator.SchemaValidator")
def test_validate_schema_compliance(mock_validator_class):
    """Test validate_schema_compliance function."""
    mock_validator = Mock()
    mock_results = {"test": "results"}
    mock_validator.validate_all_models.return_value = mock_results
    mock_validator_class.return_value = mock_validator

    results = validate_schema_compliance()

    assert results == mock_results
    mock_validator_class.assert_called_once()
    mock_validator.validate_all_models.assert_called_once()


@patch("tests.schema_validation.schema_validator.SchemaValidator")
def test_generate_schema_report(mock_validator_class):
    """Test generate_schema_report function."""
    mock_validator = Mock()
    mock_results = {"test": "results"}
    mock_report = "Test report"
    mock_validator.validate_all_models.return_value = mock_results
    mock_validator.generate_validation_report.return_value = mock_report
    mock_validator_class.return_value = mock_validator

    report = generate_schema_report()

    assert report == mock_report
    mock_validator_class.assert_called_once()
    mock_validator.validate_all_models.assert_called_once()
    mock_validator.generate_validation_report.assert_called_once_with(mock_results)


# Additional tests removed for brevity


# Keeping only the essential integration tests
class TestTableDefinition:
    """Test TableDefinition dataclass."""

    def test_table_definition_creation(self):
        """Test creating table definitions."""
        fields = [
            FieldDefinition("id", "bigint", primary_key=True),
            FieldDefinition("name", "text"),
        ]

        table = TableDefinition(
            name="test_table", fields=fields, description="Test table"
        )

        assert table.name == "test_table"
        assert len(table.fields) == 2
        assert table.description == "Test table"


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult(
            table_name="test_table",
            is_valid=False,
            errors=["Missing field: id"],
            missing_fields=["id"],
        )

        assert not result.is_valid
        assert "Missing field: id" in result.errors
        assert "id" in result.missing_fields


class TestSchemaValidator:
    """Test SchemaValidator class."""

    def test_parse_schema_markdown(self):
        """Test parsing complete schema markdown."""
        validator = SchemaValidator()

        schema_content = """
### Table: `block`

| `id` | `bigint` | NOT NULL | PRIMARY KEY |
| `hash` | `bytea` | NOT NULL | Block hash |

### Table: `tx`

| `id` | `bigint` | NOT NULL | PRIMARY KEY |
| `hash` | `bytea` | NOT NULL | Transaction hash |
| `block_id` | `bigint` | NOT NULL | REFERENCES `block` |
"""

        tables = validator._parse_schema_markdown(schema_content)

        assert len(tables) == 2
        assert "block" in tables
        assert "tx" in tables

        # Check block table
        block_table = tables["block"]
        assert block_table.name == "block"
        assert len(block_table.fields) == 2

        # Check tx table
        tx_table = tables["tx"]
        assert tx_table.name == "tx"
        assert len(tx_table.fields) == 3

        # Check foreign key parsing
        block_id_field = tx_table.fields[2]
        assert block_id_field.name == "block_id"
        assert block_id_field.foreign_key == "block"

    @patch("requests.get")
    def test_fetch_official_schema_success(self, mock_get):
        """Test successful schema fetching."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = """
        ### Table: `test_table`

        | `id` | `bigint` | NOT NULL | PRIMARY KEY |
        """
        mock_get.return_value = mock_response

        validator = SchemaValidator()
        result = validator.fetch_official_schema()

        assert result
        assert len(validator.official_schema) == 1
        assert "test_table" in validator.official_schema

    @patch("requests.get")
    def test_fetch_official_schema_failure(self, mock_get):
        """Test schema fetching failure."""
        mock_get.side_effect = Exception("Network error")

        validator = SchemaValidator()
        result = validator.fetch_official_schema()

        assert not result
        assert len(validator.official_schema) == 0

    def test_validate_model_missing_table(self):
        """Test validating model for non-existent table."""
        validator = SchemaValidator()
        validator.official_schema = {}  # Empty schema

        # Mock model class
        mock_model = Mock()
        mock_model.__tablename__ = "non_existent_table"

        result = validator.validate_model(mock_model)

        assert not result.is_valid
        assert "not found in official schema" in result.errors[0]

    def test_validate_model_with_missing_fields(self):
        """Test validating model with missing fields."""
        validator = SchemaValidator()

        # Set up official schema
        validator.official_schema = {
            "test_table": TableDefinition(
                name="test_table",
                fields=[
                    FieldDefinition("id", "bigint", primary_key=True),
                    FieldDefinition("name", "text"),
                    FieldDefinition("missing_field", "text"),
                ],
            )
        }

        # Mock model class with table
        mock_model = Mock()
        mock_model.__tablename__ = "test_table"
        mock_model.__table__ = Mock()

        # Mock columns (missing 'missing_field')
        mock_id_col = Mock()
        mock_id_col.name = "id"
        mock_name_col = Mock()
        mock_name_col.name = "name"

        mock_model.__table__.columns = [mock_id_col, mock_name_col]

        result = validator.validate_model(mock_model)

        assert not result.is_valid
        assert "missing_field" in result.missing_fields
        assert "Missing field: missing_field" in result.errors

    def test_validate_model_with_extra_fields(self):
        """Test validating model with extra fields."""
        validator = SchemaValidator()

        # Set up official schema
        validator.official_schema = {
            "test_table": TableDefinition(
                name="test_table",
                fields=[
                    FieldDefinition("id", "bigint", primary_key=True),
                    FieldDefinition("name", "text"),
                ],
            )
        }

        # Mock model class with table
        mock_model = Mock()
        mock_model.__tablename__ = "test_table"
        mock_model.__table__ = Mock()

        # Mock columns (with extra field)
        mock_id_col = Mock()
        mock_id_col.name = "id"
        mock_name_col = Mock()
        mock_name_col.name = "name"
        mock_extra_col = Mock()
        mock_extra_col.name = "extra_field"

        mock_model.__table__.columns = [mock_id_col, mock_name_col, mock_extra_col]

        # Mock column types to avoid type mismatch errors
        mock_id_col.type = Mock()
        mock_id_col.type.__str__ = Mock(return_value="BIGINTEGER")
        mock_name_col.type = Mock()
        mock_name_col.type.__str__ = Mock(return_value="TEXT")
        mock_extra_col.type = Mock()
        mock_extra_col.type.__str__ = Mock(return_value="TEXT")

        result = validator.validate_model(mock_model)

        assert result.is_valid  # Extra fields are warnings, not errors
        assert "extra_field" in result.extra_fields
        assert "Extra field not in schema: extra_field" in result.warnings

    def test_generate_validation_report(self):
        """Test generating validation report."""
        validator = SchemaValidator()

        # Create mock results
        results = {
            "valid_table": ValidationResult(
                table_name="valid_table",
                model_class=Mock(__name__="ValidTable"),
                is_valid=True,
            ),
            "invalid_table": ValidationResult(
                table_name="invalid_table",
                model_class=Mock(__name__="InvalidTable"),
                is_valid=False,
                errors=["Missing field: id"],
                missing_fields=["id"],
            ),
            "missing_table": ValidationResult(
                table_name="missing_table",
                model_class=None,
                is_valid=False,
                errors=["Model for table 'missing_table' not implemented"],
            ),
        }

        report = validator.generate_validation_report(results)

        assert "Schema Validation Report" in report
        assert "Total Tables: 3" in report
        assert "Valid Tables: 1" in report
        assert "Invalid Tables: 2" in report
        assert "Validation Success Rate: 33.3%" in report
        assert "✅ valid_table" in report
        assert "❌ invalid_table" in report
        assert "❌ missing_table" in report

    def test_get_implementation_coverage(self):
        """Test getting implementation coverage statistics."""
        validator = SchemaValidator()

        # Mock official schema
        validator.official_schema = {
            "table1": Mock(),
            "table2": Mock(),
            "table3": Mock(),
            "table4": Mock(),
        }

        # Create mock results
        results = {
            "table1": ValidationResult(
                table_name="table1", model_class=Mock(), is_valid=True
            ),
            "table2": ValidationResult(
                table_name="table2", model_class=Mock(), is_valid=False
            ),
            "table3": ValidationResult(
                table_name="table3", model_class=Mock(), is_valid=True
            ),
            "table4": ValidationResult(
                table_name="table4", model_class=None, is_valid=False
            ),
        }

        coverage = validator.get_implementation_coverage(results)

        assert coverage["total_tables_in_schema"] == 4
        assert coverage["implemented_tables"] == 3  # table1, table2, table3
        assert coverage["valid_implementations"] == 2  # table1, table3
        assert coverage["implementation_coverage"] == 75.0
        assert coverage["validation_success_rate"] == 50.0
        assert "table4" in coverage["missing_tables"]
        assert "table2" in coverage["invalid_tables"]


class TestConvenienceFunctions:
    """Test convenience functions."""

    @patch("tests.schema_validation.schema_validator.SchemaValidator")
    def test_generate_schema_report(self, mock_validator_class):
        """Test generate_schema_report function."""
        mock_validator = Mock()
        mock_results = {"test": "results"}
        mock_report = "Test report"
        mock_validator.validate_all_models.return_value = mock_results
        mock_validator.generate_validation_report.return_value = mock_report
        mock_validator_class.return_value = mock_validator

        report = generate_schema_report()

        assert report == mock_report
        mock_validator_class.assert_called_once()
        mock_validator.validate_all_models.assert_called_once()
        mock_validator.generate_validation_report.assert_called_once_with(mock_results)


@pytest.mark.integration
class TestSchemaValidatorIntegration:
    """Integration tests for schema validator."""

    def test_real_model_validation(self):
        """Test validation with real models."""
        validator = SchemaValidator()

        # Should have loaded real models
        assert len(validator.model_registry) > 50  # We have 79 tables implemented

        # Test specific models exist
        assert "block" in validator.model_registry
        assert "tx" in validator.model_registry
        assert "tx_out" in validator.model_registry
        assert "stake_address" in validator.model_registry

        # Test model classes are properly loaded
        from dbsync.models import Block, StakeAddress, Transaction, TransactionOutput

        assert validator.model_registry["block"] == Block
        assert validator.model_registry["tx"] == Transaction
        assert validator.model_registry["tx_out"] == TransactionOutput
        assert validator.model_registry["stake_address"] == StakeAddress

    @pytest.mark.slow
    def test_full_schema_validation_offline(self):
        """Test full validation without fetching schema (offline test)."""
        validator = SchemaValidator()

        # Mock a simple schema for testing
        validator.official_schema = {
            "block": TableDefinition(
                name="block",
                fields=[
                    FieldDefinition("id", "bigint", primary_key=True),
                    FieldDefinition("hash", "bytea", nullable=False),
                    FieldDefinition("epoch_no", "integer"),
                    FieldDefinition("slot_no", "bigint"),
                    FieldDefinition("block_no", "integer"),
                ],
            ),
            "tx": TableDefinition(
                name="tx",
                fields=[
                    FieldDefinition("id", "bigint", primary_key=True),
                    FieldDefinition("hash", "bytea", nullable=False),
                    FieldDefinition("block_id", "bigint", foreign_key="block"),
                ],
            ),
        }

        results = validator.validate_all_models()

        # Should have results for at least the tables we defined
        assert "block" in results
        assert "tx" in results

        # Results should include validation details
        block_result = results["block"]
        assert block_result.model_class is not None
        assert block_result.table_name == "block"

        tx_result = results["tx"]
        assert tx_result.model_class is not None
        assert tx_result.table_name == "tx"
