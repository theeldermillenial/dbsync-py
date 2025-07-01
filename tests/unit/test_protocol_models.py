"""Unit tests for protocol parameter models.

Tests for SCHEMA-010: Protocol Parameters Models
"""

from decimal import Decimal

import pytest

from dbsync.models.protocol import EpochParam, ParamProposal, RewardRest


class TestParamProposal:
    """Test cases for ParamProposal model."""

    def test_param_proposal_creation(self):
        """Test creating a parameter proposal."""
        proposal = ParamProposal(
            id_=1,
            epoch_no=300,
            key=b"genesis_key_hash_32_bytes_here_",
            min_fee_a=44,
            min_fee_b=155381,
            max_block_size=65536,
            max_tx_size=16384,
            key_deposit=2000000,
            pool_deposit=500000000,
            optimal_pool_count=500,
            influence=Decimal("0.3"),
            monetary_expand_rate=Decimal("0.003"),
            treasury_growth_rate=Decimal("0.2"),
            decentralisation=Decimal("0.0"),
            protocol_major=7,
            protocol_minor=0,
            min_pool_cost=340000000,
            registered_tx_id=12345,
        )

        assert proposal.id_ == 1
        assert proposal.epoch_no == 300
        assert proposal.key == b"genesis_key_hash_32_bytes_here_"
        assert proposal.min_fee_a == 44
        assert proposal.min_fee_b == 155381
        assert proposal.max_block_size == 65536
        assert proposal.max_tx_size == 16384
        assert proposal.key_deposit == 2000000
        assert proposal.pool_deposit == 500000000
        assert proposal.optimal_pool_count == 500
        assert proposal.influence == Decimal("0.3")
        assert proposal.monetary_expand_rate == Decimal("0.003")
        assert proposal.treasury_growth_rate == Decimal("0.2")
        assert proposal.decentralisation == Decimal("0.0")
        assert proposal.protocol_major == 7
        assert proposal.protocol_minor == 0
        assert proposal.min_pool_cost == 340000000
        assert proposal.registered_tx_id == 12345

    def test_param_proposal_minimal(self):
        """Test creating a minimal parameter proposal."""
        proposal = ParamProposal(
            epoch_no=300,
            key=b"genesis_key_hash_32_bytes_here_",
            protocol_major=8,  # Only proposing a hard fork
        )

        assert proposal.epoch_no == 300
        assert proposal.key == b"genesis_key_hash_32_bytes_here_"
        assert proposal.protocol_major == 8
        assert proposal.min_fee_a is None
        assert proposal.min_fee_b is None

    def test_get_proposal_summary(self):
        """Test getting proposal summary."""
        proposal = ParamProposal(
            min_fee_a=44,
            min_fee_b=155381,
            max_block_size=65536,
            key_deposit=2000000,
            optimal_pool_count=500,
            influence=Decimal("0.3"),
            protocol_major=7,
            protocol_minor=0,
        )

        summary = proposal.get_proposal_summary()

        expected_summary = {
            "min_fee_a": 44,
            "min_fee_b": 155381,
            "max_block_size": 65536,
            "key_deposit": 2000000,
            "optimal_pool_count": 500,
            "influence": 0.3,
            "protocol_version": {"major": 7, "minor": 0},
        }

        assert summary == expected_summary

    def test_get_proposal_summary_empty(self):
        """Test getting proposal summary with no parameters set."""
        proposal = ParamProposal()
        summary = proposal.get_proposal_summary()
        assert summary == {}

    def test_is_hard_fork_proposal(self):
        """Test checking if proposal is a hard fork."""
        # Hard fork proposal
        hard_fork_proposal = ParamProposal(protocol_major=8)
        assert hard_fork_proposal.is_hard_fork_proposal() is True

        # Non-hard fork proposal
        regular_proposal = ParamProposal(min_fee_a=50)
        assert regular_proposal.is_hard_fork_proposal() is False

        # Empty proposal
        empty_proposal = ParamProposal()
        assert empty_proposal.is_hard_fork_proposal() is False

    def test_alonzo_era_parameters(self):
        """Test Alonzo era specific parameters."""
        proposal = ParamProposal(
            cost_model_id=1,
            price_mem=Decimal("0.0577"),
            price_step=Decimal("0.0000721"),
            max_tx_ex_mem=14000000,
            max_tx_ex_steps=10000000000,
            max_block_ex_mem=62000000,
            max_block_ex_steps=40000000000,
            max_val_size=5000,
            collateral_percent=150,
            max_collateral_inputs=3,
        )

        assert proposal.cost_model_id == 1
        assert proposal.price_mem == Decimal("0.0577")
        assert proposal.price_step == Decimal("0.0000721")
        assert proposal.max_tx_ex_mem == 14000000
        assert proposal.max_tx_ex_steps == 10000000000
        assert proposal.max_block_ex_mem == 62000000
        assert proposal.max_block_ex_steps == 40000000000
        assert proposal.max_val_size == 5000
        assert proposal.collateral_percent == 150
        assert proposal.max_collateral_inputs == 3


class TestEpochParam:
    """Test cases for EpochParam model."""

    def test_epoch_param_creation(self):
        """Test creating epoch parameters."""
        epoch_param = EpochParam(
            id_=1,
            epoch_no=300,
            min_fee_a=44,
            min_fee_b=155381,
            max_block_size=65536,
            max_tx_size=16384,
            max_bh_size=1100,
            key_deposit=2000000,
            pool_deposit=500000000,
            max_epoch=18,
            optimal_pool_count=500,
            influence=Decimal("0.3"),
            monetary_expand_rate=Decimal("0.003"),
            treasury_growth_rate=Decimal("0.2"),
            decentralisation=Decimal("0.0"),
            protocol_major=7,
            protocol_minor=0,
            min_utxo_value=1000000,
            min_pool_cost=340000000,
            block_id=98765,
        )

        assert epoch_param.id_ == 1
        assert epoch_param.epoch_no == 300
        assert epoch_param.min_fee_a == 44
        assert epoch_param.min_fee_b == 155381
        assert epoch_param.max_block_size == 65536
        assert epoch_param.max_tx_size == 16384
        assert epoch_param.max_bh_size == 1100
        assert epoch_param.key_deposit == 2000000
        assert epoch_param.pool_deposit == 500000000
        assert epoch_param.max_epoch == 18
        assert epoch_param.optimal_pool_count == 500
        assert epoch_param.influence == Decimal("0.3")
        assert epoch_param.monetary_expand_rate == Decimal("0.003")
        assert epoch_param.treasury_growth_rate == Decimal("0.2")
        assert epoch_param.decentralisation == Decimal("0.0")
        assert epoch_param.protocol_major == 7
        assert epoch_param.protocol_minor == 0
        assert epoch_param.min_utxo_value == 1000000
        assert epoch_param.min_pool_cost == 340000000
        assert epoch_param.block_id == 98765

    def test_calculate_min_fee(self):
        """Test minimum fee calculation."""
        epoch_param = EpochParam(min_fee_a=44, min_fee_b=155381)

        # Test fee calculation for 1000 byte transaction
        fee = epoch_param.calculate_min_fee(1000)
        expected_fee = 44 * 1000 + 155381  # 199381
        assert fee == expected_fee

        # Test fee calculation for 500 byte transaction
        fee = epoch_param.calculate_min_fee(500)
        expected_fee = 44 * 500 + 155381  # 177381
        assert fee == expected_fee

    def test_calculate_min_fee_missing_params(self):
        """Test minimum fee calculation with missing parameters."""
        epoch_param = EpochParam(min_fee_a=44)  # Missing min_fee_b

        with pytest.raises(ValueError, match="Fee parameters not set"):
            epoch_param.calculate_min_fee(1000)

    def test_get_protocol_version(self):
        """Test getting protocol version."""
        epoch_param = EpochParam(protocol_major=7, protocol_minor=0)

        version = epoch_param.get_protocol_version()
        expected_version = {"major": 7, "minor": 0}
        assert version == expected_version

    def test_get_protocol_version_none(self):
        """Test getting protocol version when not set."""
        epoch_param = EpochParam()
        version = epoch_param.get_protocol_version()
        expected_version = {"major": None, "minor": None}
        assert version == expected_version

    def test_get_size_limits(self):
        """Test getting size limits."""
        epoch_param = EpochParam(
            max_block_size=65536, max_tx_size=16384, max_bh_size=1100, max_val_size=5000
        )

        limits = epoch_param.get_size_limits()
        expected_limits = {
            "max_block_size": 65536,
            "max_tx_size": 16384,
            "max_bh_size": 1100,
            "max_val_size": 5000,
        }
        assert limits == expected_limits

    def test_get_economic_params(self):
        """Test getting economic parameters."""
        epoch_param = EpochParam(
            monetary_expand_rate=Decimal("0.003"),
            treasury_growth_rate=Decimal("0.2"),
            influence=Decimal("0.3"),
            optimal_pool_count=500,
            min_pool_cost=340000000,
            decentralisation=Decimal("0.0"),
        )

        params = epoch_param.get_economic_params()
        expected_params = {
            "monetary_expand_rate": 0.003,
            "treasury_growth_rate": 0.2,
            "influence": 0.3,
            "optimal_pool_count": 500,
            "min_pool_cost": 340000000,
            "decentralisation": 0.0,
        }
        assert params == expected_params

    def test_get_economic_params_none_values(self):
        """Test getting economic parameters with None values."""
        epoch_param = EpochParam(optimal_pool_count=500)

        params = epoch_param.get_economic_params()
        expected_params = {
            "monetary_expand_rate": None,
            "treasury_growth_rate": None,
            "influence": None,
            "optimal_pool_count": 500,
            "min_pool_cost": None,
            "decentralisation": None,
        }
        assert params == expected_params

    def test_is_fully_decentralized(self):
        """Test checking if network is fully decentralized."""
        # Fully decentralized
        decentralized_param = EpochParam(decentralisation=Decimal("0.0"))
        assert decentralized_param.is_fully_decentralized() is True

        # Not fully decentralized
        centralized_param = EpochParam(decentralisation=Decimal("0.5"))
        assert centralized_param.is_fully_decentralized() is False

        # Decentralisation parameter not set
        no_param = EpochParam()
        assert no_param.is_fully_decentralized() is False


class TestRewardRest:
    """Test cases for RewardRest model."""

    def test_reward_rest_creation(self):
        """Test creating a reward rest record."""
        reward_rest = RewardRest(
            addr_id=12345,
            type_="member",
            amount=1500000,
            earned_epoch=300,
            spendable_epoch=302,
        )

        assert reward_rest.addr_id == 12345
        assert reward_rest.type_ == "member"
        assert reward_rest.amount == 1500000
        assert reward_rest.earned_epoch == 300
        assert reward_rest.spendable_epoch == 302

    def test_amount_ada_property(self):
        """Test ADA amount conversion property."""
        reward_rest = RewardRest(
            addr_id=12345,
            type_="member",
            amount=1500000,  # 1.5 ADA
            earned_epoch=300,
            spendable_epoch=302,
        )
        assert reward_rest.amount_ada == 1.5

        # Test with None amount
        reward_rest_none = RewardRest()
        assert reward_rest_none.amount_ada == 0.0

    def test_is_spendable_in_epoch(self):
        """Test checking if reward is spendable in given epoch."""
        reward_rest = RewardRest(
            addr_id=12345,
            type_="member",
            amount=1500000,
            earned_epoch=300,
            spendable_epoch=302,
        )

        # Spendable in the exact epoch
        assert reward_rest.is_spendable_in_epoch(302) is True

        # Spendable in later epoch
        assert reward_rest.is_spendable_in_epoch(305) is True

        # Not spendable in earlier epoch
        assert reward_rest.is_spendable_in_epoch(301) is False

    def test_is_spendable_in_epoch_none(self):
        """Test checking spendability when spendable_epoch is None."""
        reward_rest = RewardRest()
        assert reward_rest.is_spendable_in_epoch(300) is False

    def test_epochs_until_spendable(self):
        """Test calculating epochs until reward becomes spendable."""
        reward_rest = RewardRest(
            addr_id=12345,
            type_="member",
            amount=1500000,
            earned_epoch=300,
            spendable_epoch=305,
        )

        # Still need to wait
        assert reward_rest.epochs_until_spendable(300) == 5
        assert reward_rest.epochs_until_spendable(303) == 2

        # Already spendable
        assert reward_rest.epochs_until_spendable(305) == 0
        assert reward_rest.epochs_until_spendable(310) == 0

    def test_epochs_until_spendable_none(self):
        """Test epochs until spendable when spendable_epoch is None."""
        reward_rest = RewardRest()
        assert reward_rest.epochs_until_spendable(300) == 0

    def test_get_reward_info(self):
        """Test getting comprehensive reward information."""
        reward_rest = RewardRest(
            type_="member",
            amount=2500000,  # 2.5 ADA
            earned_epoch=300,
            spendable_epoch=302,
            addr_id=12345,
        )

        info = reward_rest.get_reward_info()
        expected_info = {
            "type": "member",
            "amount_lovelace": 2500000,
            "amount_ada": 2.5,
            "earned_epoch": 300,
            "spendable_epoch": 302,
            "addr_id": 12345,
        }
        assert info == expected_info

    def test_reward_types(self):
        """Test different reward types."""
        # Member reward
        member_reward = RewardRest(
            addr_id=12345,
            type_="member",
            amount=1000000,
            earned_epoch=300,
            spendable_epoch=302,
        )
        assert member_reward.type_ == "member"

        # Leader reward
        leader_reward = RewardRest(
            addr_id=12345,
            type_="leader",
            amount=5000000,
            earned_epoch=300,
            spendable_epoch=302,
        )
        assert leader_reward.type_ == "leader"

        # Treasury reward
        treasury_reward = RewardRest(
            addr_id=12345,
            type_="treasury",
            amount=10000000,
            earned_epoch=300,
            spendable_epoch=302,
        )
        assert treasury_reward.type_ == "treasury"

    def test_large_amounts(self):
        """Test handling of large reward amounts."""
        # Large amount in lovelace
        large_reward = RewardRest(
            addr_id=12345,
            type_="member",
            amount=45000000000000,  # 45M ADA
            earned_epoch=300,
            spendable_epoch=302,
        )
        assert large_reward.amount_ada == 45000000.0

        # Very small amount
        small_reward = RewardRest(
            addr_id=12345,
            type_="member",
            amount=1,  # 0.000001 ADA
            earned_epoch=300,
            spendable_epoch=302,
        )
        assert small_reward.amount_ada == 0.000001
