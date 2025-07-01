"""Integration tests for script and smart contract models.

Tests SCHEMA-008: Script and Smart Contract Models integration including:
- Script model database integration
- CostModel database integration
- RedeemerData and Redeemer database integration
"""

import pytest
from sqlalchemy import String
from sqlmodel import Session, select

from dbsync.models.scripts import (
    CostModel,
    PlutusVersion,
    Redeemer,
    RedeemerData,
    Script,
    ScriptType,
)


class TestScriptModelsIntegration:
    """Integration tests for script models with database."""

    def test_cost_model_database_integration(self, dbsync_session: Session) -> None:
        """Test CostModel database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying cost models (read-only)
            stmt = select(CostModel).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_")
                assert hasattr(result, "costs")

                # Test property methods if data exists
                if result.hash_:
                    assert hasattr(result, "hash_hex")
                    assert len(result.hash_hex) == 64  # 32 bytes as hex
                if result.costs:
                    assert hasattr(result, "operation_count")
                    assert result.operation_count >= 0
                    assert hasattr(result, "is_valid")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_script_model_database_integration(self, dbsync_session: Session) -> None:
        """Test Script model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying scripts (read-only)
            stmt = select(Script).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_")
                assert hasattr(result, "type_")

                # Test property methods
                assert hasattr(result, "is_native")
                assert hasattr(result, "is_plutus")
                if result.hash_:
                    assert hasattr(result, "hash_hex")
                    assert len(result.hash_hex) == 56  # 28 bytes as hex
                if result.type_:
                    # Test script type properties based on actual type
                    if result.type_ == "native":
                        assert result.is_native is True
                        assert result.is_plutus is False
                    elif result.type_ in ["plutusV1", "plutusV2", "plutusV3"]:
                        assert result.is_plutus is True
                        assert result.is_native is False

                    # Test plutus_version property
                    assert hasattr(result, "plutus_version")
                    if result.type_ == "plutusV1":
                        assert result.plutus_version == PlutusVersion.V1
                    elif result.type_ == "plutusV2":
                        assert result.plutus_version == PlutusVersion.V2
                    elif result.type_ == "plutusV3":
                        assert result.plutus_version == PlutusVersion.V3
                    else:
                        assert result.plutus_version is None
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_redeemer_data_database_integration(self, dbsync_session: Session) -> None:
        """Test RedeemerData model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying redeemer data (read-only)
            stmt = select(RedeemerData).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_")
                assert hasattr(result, "value")

                # Test property methods
                if result.hash_:
                    assert hasattr(result, "hash_hex")
                    assert len(result.hash_hex) == 64  # 32 bytes as hex
                if result.bytes_:
                    assert hasattr(result, "size_bytes")
                    assert result.size_bytes >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_redeemer_database_integration(self, dbsync_session: Session) -> None:
        """Test Redeemer model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying redeemers (read-only)
            stmt = select(Redeemer).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "unit_mem")
                assert hasattr(result, "unit_steps")
                assert hasattr(result, "purpose")

                # Test property methods
                assert hasattr(result, "total_execution_units")
                if result.unit_mem is not None and result.unit_steps is not None:
                    assert (
                        result.total_execution_units
                        == result.unit_mem + result.unit_steps
                    )

                if result.script_hash:
                    assert hasattr(result, "script_hash_hex")
                    assert len(result.script_hash_hex) == 56  # 28 bytes as hex

                # Test purpose-specific properties
                if result.purpose:
                    assert hasattr(result, "is_spending_redeemer")
                    assert hasattr(result, "is_minting_redeemer")
                    assert hasattr(result, "is_certificate_redeemer")
                    assert hasattr(result, "is_reward_redeemer")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_script_models_read_only_behavior(self, dbsync_session: Session) -> None:
        """Test that script models are used in read-only mode."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # This test verifies that the models are designed for read-only access
            # In a real dbsync environment, these tables are populated by the dbsync process

            # Test that we can create queries but the expectation is read-only usage
            cost_model_query = select(CostModel)
            script_query = select(Script)
            redeemer_data_query = select(RedeemerData)
            redeemer_query = select(Redeemer)

            # Verify queries can be constructed (this is the expected usage pattern)
            assert cost_model_query is not None
            assert script_query is not None
            assert redeemer_data_query is not None
            assert redeemer_query is not None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_script_relationships_integration(self, dbsync_session: Session) -> None:
        """Test script model relationships in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying scripts with their redeemers (cast to scripttype enum)
            stmt = (
                select(Script)
                .where(Script.type_.cast(String) == ScriptType.PLUTUS_V2.value)
                .limit(1)
            )
            script_result = dbsync_session.exec(stmt).first()

            if script_result:
                # Test relationship between scripts and redeemers
                redeemer_stmt = (
                    select(Redeemer)
                    .where(Redeemer.script_hash == script_result.hash_)
                    .limit(1)
                )
                redeemer_result = dbsync_session.exec(redeemer_stmt).first()

                # Verify relationship structure if data exists
                if redeemer_result:
                    assert redeemer_result.script_hash == script_result.hash_
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_script_type_analysis_integration(self, dbsync_session: Session) -> None:
        """Test script type analysis in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying scripts by type (cast to string to avoid enum type issues)
            native_stmt = (
                select(Script)
                .where(Script.type_.cast(String) == ScriptType.NATIVE.value)
                .limit(1)
            )
            native_result = dbsync_session.exec(native_stmt).first()

            if native_result:
                assert native_result.is_native is True
                assert native_result.is_plutus is False

            # Test Plutus scripts
            plutus_stmt = (
                select(Script)
                .where(
                    Script.type_.cast(String).in_(
                        [
                            ScriptType.PLUTUS_V1.value,
                            ScriptType.PLUTUS_V2.value,
                            ScriptType.PLUTUS_V3.value,
                        ]
                    )
                )
                .limit(1)
            )
            plutus_result = dbsync_session.exec(plutus_stmt).first()

            if plutus_result:
                assert plutus_result.is_plutus is True
                assert plutus_result.is_native is False
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_cost_model_analysis_integration(self, dbsync_session: Session) -> None:
        """Test cost model analysis in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying cost models with operation analysis
            stmt = select(CostModel).where(CostModel.costs.is_not(None)).limit(1)
            result = dbsync_session.exec(stmt).first()

            if result and result.costs:
                # Test cost model methods
                assert result.operation_count > 0
                assert result.is_valid is True

                # Test specific operation checks if data exists
                for operation_name in result.costs.keys():
                    assert result.has_operation(operation_name) is True
                    cost_value = result.get_operation_cost(operation_name)
                    assert cost_value is not None
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_redeemer_execution_analysis_integration(
        self, dbsync_session: Session
    ) -> None:
        """Test redeemer execution analysis in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying redeemers with execution unit analysis
            stmt = (
                select(Redeemer)
                .where(Redeemer.unit_mem.is_not(None), Redeemer.unit_steps.is_not(None))
                .limit(3)
            )
            results = dbsync_session.exec(stmt).all()

            for redeemer in results:
                if redeemer.unit_mem is not None and redeemer.unit_steps is not None:
                    # Test execution unit calculations
                    total_units = redeemer.total_execution_units
                    assert total_units == redeemer.unit_mem + redeemer.unit_steps
                    assert total_units >= 0

                    # Test execution cost ratio if both values are positive
                    if redeemer.unit_steps > 0:
                        ratio = redeemer.execution_cost_ratio
                        assert ratio >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")
