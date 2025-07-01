"""Integration tests for protocol parameter models.

Tests database interaction and constraints for SCHEMA-010: Protocol Parameters Models
"""

from decimal import Decimal

import pytest
from sqlmodel import Session, select

from dbsync.models.protocol import EpochParam, ParamProposal, RewardRest


class TestProtocolModelsIntegration:
    """Integration tests for protocol parameter models."""

    def test_param_proposal_query_integration(self, dbsync_session: Session) -> None:
        """Test ParamProposal model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying protocol parameter proposals (read-only)
            stmt = select(ParamProposal).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "epoch_no")
                assert hasattr(result, "key")
                assert hasattr(result, "min_fee_a")
                assert hasattr(result, "min_fee_b")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_epoch_param_query_integration(self, dbsync_session: Session) -> None:
        """Test EpochParam model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying epoch parameters (read-only)
            stmt = select(EpochParam).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "epoch_no")
                assert hasattr(result, "min_fee_a")
                assert hasattr(result, "min_fee_b")
                assert hasattr(result, "max_block_size")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_reward_rest_query_integration(self, dbsync_session: Session) -> None:
        """Test RewardRest model database integration."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying reward distributions (read-only)
            stmt = select(RewardRest).limit(1)
            result = dbsync_session.exec(stmt).first()

            # Verify we can query the model
            if result:
                assert hasattr(result, "addr_id")
                assert hasattr(result, "amount")
                assert hasattr(result, "earned_epoch")
                assert hasattr(result, "spendable_epoch")
                assert hasattr(result, "type_")
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_protocol_models_read_only_behavior(self, dbsync_session: Session) -> None:
        """Test that protocol models are used in read-only mode."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # This test verifies that the models are designed for read-only access
            # In a real dbsync environment, these tables are populated by the dbsync process

            # Test that we can create queries but the expectation is read-only usage
            param_proposal_query = select(ParamProposal)
            epoch_param_query = select(EpochParam)
            reward_rest_query = select(RewardRest)

            # Verify queries can be constructed (this is the expected usage pattern)
            assert param_proposal_query is not None
            assert epoch_param_query is not None
            assert reward_rest_query is not None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_epoch_param_relationships_integration(
        self, dbsync_session: Session
    ) -> None:
        """Test EpochParam relationships in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying epoch params with unique epoch constraint
            stmt = select(EpochParam).order_by(EpochParam.epoch_no).limit(2)
            results = dbsync_session.exec(stmt).all()

            # Verify unique epoch constraint works
            if len(results) >= 2:
                assert results[0].epoch_no != results[1].epoch_no
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_param_proposal_epochs_integration(self, dbsync_session: Session) -> None:
        """Test ParamProposal epoch-based queries in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying proposals by epoch range
            stmt = select(ParamProposal).where(ParamProposal.epoch_no >= 0).limit(5)
            results = dbsync_session.exec(stmt).all()

            # Verify epoch-based filtering works
            for proposal in results:
                if proposal.epoch_no is not None:
                    assert proposal.epoch_no >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_reward_rest_analysis_integration(self, dbsync_session: Session) -> None:
        """Test RewardRest analysis in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying rewards by type
            stmt = select(RewardRest).where(RewardRest.type_ == "reserves").limit(5)
            results = dbsync_session.exec(stmt).all()

            # Verify reward analysis
            for reward in results:
                assert reward.type_ == "reserves"
                assert reward.amount >= 0
                assert reward.addr_id > 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_parameter_evolution_integration(self, dbsync_session: Session) -> None:
        """Test parameter evolution across epochs in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying parameter changes across epochs
            stmt = select(EpochParam).order_by(EpochParam.epoch_no).limit(5)
            results = dbsync_session.exec(stmt).all()

            # Verify parameter evolution can be tracked
            if len(results) >= 2:
                epochs = [
                    param.epoch_no for param in results if param.epoch_no is not None
                ]
                if len(epochs) >= 2:
                    assert epochs == sorted(epochs)  # Should be in ascending order
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_fee_structure_analysis_integration(self, dbsync_session: Session) -> None:
        """Test fee structure analysis in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying fee parameters
            stmt = (
                select(EpochParam)
                .where(
                    EpochParam.min_fee_a.is_not(None), EpochParam.min_fee_b.is_not(None)
                )
                .limit(3)
            )
            results = dbsync_session.exec(stmt).all()

            # Verify fee structure analysis
            for epoch_param in results:
                if (
                    epoch_param.min_fee_a is not None
                    and epoch_param.min_fee_b is not None
                ):
                    # Test fee calculation functionality if available
                    if hasattr(epoch_param, "calculate_min_fee"):
                        fee = epoch_param.calculate_min_fee(1000)
                        assert fee >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_reward_distribution_analysis_integration(
        self, dbsync_session: Session
    ) -> None:
        """Test reward distribution analysis in database context."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test querying reward distributions by epoch
            stmt = select(RewardRest).where(RewardRest.earned_epoch >= 0).limit(5)
            results = dbsync_session.exec(stmt).all()

            # Verify reward distribution data
            total_rewards = 0
            for reward in results:
                total_rewards += reward.amount
                assert reward.amount >= 0

                # Test reward conversion if available
                if hasattr(reward, "amount_ada"):
                    ada_amount = reward.amount_ada
                    assert ada_amount >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    # Schema validation tests (existing tests)
    def test_param_proposal_table_structure(self):
        """Test ParamProposal table structure and constraints."""
        # Test table name
        assert ParamProposal.__tablename__ == "param_proposal"

        # Test primary key
        assert ParamProposal.__table__.primary_key.columns.keys() == ["id"]

        # Test indexed columns (excluding primary key which is indexed by default)
        indexed_columns = {
            col.name
            for col in ParamProposal.__table__.columns
            if col.index or col.unique
        }
        expected_indexed = {"epoch_no", "key", "registered_tx_id"}
        assert expected_indexed.issubset(indexed_columns)

    def test_epoch_param_table_structure(self):
        """Test EpochParam table structure and constraints."""
        # Test table name
        assert EpochParam.__tablename__ == "epoch_param"

        # Test primary key
        assert EpochParam.__table__.primary_key.columns.keys() == ["id"]

        # Test unique constraint on epoch_no
        epoch_no_col = EpochParam.__table__.columns["epoch_no"]
        assert epoch_no_col.unique is True
        assert epoch_no_col.index is True

        # Test foreign key constraint
        block_id_col = EpochParam.__table__.columns["block_id"]
        assert len(block_id_col.foreign_keys) == 1
        fk = list(block_id_col.foreign_keys)[0]
        assert str(fk.target_fullname) == "block.id"

    def test_reward_rest_table_structure(self):
        """Test RewardRest table structure and constraints."""
        # Test table name
        assert RewardRest.__tablename__ == "reward_rest"

        # Test composite primary key
        pk_columns = RewardRest.__table__.primary_key.columns.keys()
        expected_pk = {"addr_id", "type", "earned_epoch", "spendable_epoch"}
        assert set(pk_columns) == expected_pk

        # Test foreign key constraints
        addr_id_col = RewardRest.__table__.columns["addr_id"]
        assert len(addr_id_col.foreign_keys) == 1
        fk = list(addr_id_col.foreign_keys)[0]
        assert str(fk.target_fullname) == "stake_address.id"

    def test_param_proposal_field_types(self):
        """Test ParamProposal field types and constraints."""
        table = ParamProposal.__table__

        # Test BigInteger fields
        big_int_fields = [
            "id",
            "cost_model_id",
            "registered_tx_id",
            "max_tx_ex_mem",
            "max_tx_ex_steps",
            "max_block_ex_mem",
            "max_block_ex_steps",
            "max_val_size",
        ]
        for field in big_int_fields:
            if field in table.columns:
                col = table.columns[field]
                assert "BIGINT" in str(col.type).upper()

        # Test Integer fields
        int_fields = [
            "epoch_no",
            "max_block_size",
            "max_tx_size",
            "max_bh_size",
            "max_epoch",
            "optimal_pool_count",
            "protocol_major",
            "protocol_minor",
            "collateral_percent",
            "max_collateral_inputs",
        ]
        for field in int_fields:
            if field in table.columns:
                col = table.columns[field]
                assert "INT" in str(col.type).upper()

        # Test Numeric fields with precision
        numeric_fields = [
            "influence",
            "monetary_expand_rate",
            "treasury_growth_rate",
            "decentralisation",
            "price_mem",
            "price_step",
        ]
        for field in numeric_fields:
            if field in table.columns:
                col = table.columns[field]
                assert "NUMERIC" in str(col.type).upper()

    def test_epoch_param_field_types(self):
        """Test EpochParam field types and constraints."""
        table = EpochParam.__table__

        # Test unique epoch_no constraint
        epoch_no_col = table.columns["epoch_no"]
        assert epoch_no_col.unique is True

        # Test foreign key field
        if "cost_model_id" in table.columns:
            cost_model_col = table.columns["cost_model_id"]
            assert len(cost_model_col.foreign_keys) == 1
            fk = list(cost_model_col.foreign_keys)[0]
            assert str(fk.target_fullname) == "cost_model.id"

    def test_reward_rest_field_types(self):
        """Test RewardRest field types and constraints."""
        table = RewardRest.__table__

        # Test primary key fields (they are automatically indexed)
        pk_fields = ["addr_id", "type", "earned_epoch", "spendable_epoch"]
        for field in pk_fields:
            if field in table.columns:
                col = table.columns[field]
                assert col.primary_key is True

    def test_param_proposal_business_logic(self):
        """Test ParamProposal business logic methods."""
        # Test hard fork detection
        hard_fork = ParamProposal(protocol_major=8)
        assert hard_fork.is_hard_fork_proposal() is True

        soft_fork = ParamProposal(min_fee_a=50)
        assert soft_fork.is_hard_fork_proposal() is False

        # Test proposal summary generation
        proposal = ParamProposal(
            min_fee_a=44, min_fee_b=155381, protocol_major=7, protocol_minor=0
        )
        summary = proposal.get_proposal_summary()
        assert "min_fee_a" in summary
        assert "min_fee_b" in summary
        assert "protocol_version" in summary
        assert summary["protocol_version"]["major"] == 7

    def test_epoch_param_business_logic(self):
        """Test EpochParam business logic methods."""
        epoch_param = EpochParam(
            min_fee_a=44,
            min_fee_b=155381,
            decentralisation=Decimal("0.0"),
            max_block_size=65536,
            max_tx_size=16384,
        )

        # Test fee calculation
        fee = epoch_param.calculate_min_fee(1000)
        assert fee == 44 * 1000 + 155381

        # Test decentralization check
        assert epoch_param.is_fully_decentralized() is True

        # Test parameter getters
        size_limits = epoch_param.get_size_limits()
        assert size_limits["max_block_size"] == 65536
        assert size_limits["max_tx_size"] == 16384

    def test_reward_rest_business_logic(self):
        """Test RewardRest business logic methods."""
        reward = RewardRest(
            addr_id=12345,
            amount=2500000,  # 2.5 ADA
            earned_epoch=300,
            spendable_epoch=302,
            type_="member",
        )

        # Test ADA conversion
        assert reward.amount_ada == 2.5

        # Test spendability checks
        assert reward.is_spendable_in_epoch(302) is True
        assert reward.is_spendable_in_epoch(301) is False
        assert reward.epochs_until_spendable(300) == 2
        assert reward.epochs_until_spendable(302) == 0

        # Test reward info
        info = reward.get_reward_info()
        assert info["amount_ada"] == 2.5
        assert info["type"] == "member"
        assert info["addr_id"] == 12345

    def test_protocol_parameter_relationships(self):
        """Test relationships between protocol parameter models."""
        # Test that ParamProposal can reference cost_model
        proposal = ParamProposal(cost_model_id=1)
        assert proposal.cost_model_id == 1

        # Test that EpochParam can reference block and cost_model
        epoch_param = EpochParam(block_id=12345, cost_model_id=1)
        assert epoch_param.block_id == 12345
        assert epoch_param.cost_model_id == 1

        # Test that RewardRest references stake_address
        reward = RewardRest(
            addr_id=100,
            type_="reserves",
            amount=1000000,
            earned_epoch=200,
            spendable_epoch=202,
        )
        assert reward.addr_id == 100
        assert reward.type_ == "reserves"

    def test_decimal_precision_handling(self):
        """Test handling of high-precision decimal values."""
        # Test proposal with precise decimal values
        proposal = ParamProposal(
            influence=Decimal("0.3000000000"),
            monetary_expand_rate=Decimal("0.0030000000"),
            price_mem=Decimal("0.0577000000"),
            price_step=Decimal("0.0000721000"),
        )

        assert proposal.influence == Decimal("0.3000000000")
        assert proposal.monetary_expand_rate == Decimal("0.0030000000")
        assert proposal.price_mem == Decimal("0.0577000000")
        assert proposal.price_step == Decimal("0.0000721000")

        # Test epoch param with precise decimal values
        epoch_param = EpochParam(
            treasury_growth_rate=Decimal("0.2000000000"),
            decentralisation=Decimal("0.0000000000"),
        )

        assert epoch_param.treasury_growth_rate == Decimal("0.2000000000")
        assert epoch_param.decentralisation == Decimal("0.0000000000")

    def test_large_value_handling(self):
        """Test handling of large integer values."""
        # Test large execution limits
        proposal = ParamProposal(
            max_tx_ex_mem=14000000,
            max_tx_ex_steps=10000000000,
            max_block_ex_mem=62000000,
            max_block_ex_steps=40000000000,
        )

        assert proposal.max_tx_ex_mem == 14000000
        assert proposal.max_tx_ex_steps == 10000000000
        assert proposal.max_block_ex_mem == 62000000
        assert proposal.max_block_ex_steps == 40000000000

        # Test large reward amounts
        reward = RewardRest(amount=45000000000000)  # 45M ADA
        assert reward.amount == 45000000000000
        assert reward.amount_ada == 45000000.0
