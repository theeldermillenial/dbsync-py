"""Unit tests for staking models.

Tests all SCHEMA-005 staking and delegation models including
stake registrations, delegations, epoch stake, and rewards.
"""

from dbsync.models import (
    Delegation,
    DelegationVote,
    EpochStake,
    EpochStakeProgress,
    Reward,
    RewardType,
    StakeDeregistration,
    StakeRegistration,
)


class TestStakeRegistrationModel:
    """Test StakeRegistration model functionality."""

    def test_stake_registration_creation(self):
        """Test StakeRegistration model instantiation."""
        registration = StakeRegistration(
            addr_id=100,
            cert_index=0,
            epoch_no=250,
            tx_id=12345,
        )

        assert registration.addr_id == 100
        assert registration.cert_index == 0
        assert registration.epoch_no == 250
        assert registration.tx_id == 12345
        assert registration.id_ is None  # Should be None until saved

    def test_stake_registration_table_name(self):
        """Test StakeRegistration has correct table name."""
        assert StakeRegistration.__tablename__ == "stake_registration"

    def test_stake_registration_with_minimal_data(self):
        """Test StakeRegistration with minimal required data."""
        registration = StakeRegistration()

        assert registration.addr_id is None
        assert registration.cert_index is None
        assert registration.epoch_no is None
        assert registration.tx_id is None


class TestStakeDeregistrationModel:
    """Test StakeDeregistration model functionality."""

    def test_stake_deregistration_creation(self):
        """Test StakeDeregistration model instantiation."""
        deregistration = StakeDeregistration(
            addr_id=100,
            cert_index=1,
            epoch_no=251,
            tx_id=12346,
            redeemer_id=500,
        )

        assert deregistration.addr_id == 100
        assert deregistration.cert_index == 1
        assert deregistration.epoch_no == 251
        assert deregistration.tx_id == 12346
        assert deregistration.redeemer_id == 500
        assert deregistration.id_ is None

    def test_stake_deregistration_table_name(self):
        """Test StakeDeregistration has correct table name."""
        assert StakeDeregistration.__tablename__ == "stake_deregistration"

    def test_stake_deregistration_without_redeemer(self):
        """Test StakeDeregistration without redeemer (non-script address)."""
        deregistration = StakeDeregistration(
            addr_id=100,
            cert_index=1,
            epoch_no=251,
            tx_id=12346,
        )

        assert deregistration.redeemer_id is None


class TestDelegationModel:
    """Test Delegation model functionality."""

    def test_delegation_creation(self):
        """Test Delegation model instantiation."""
        delegation = Delegation(
            addr_id=100,
            cert_index=2,
            pool_hash_id=200,
            active_epoch_no=252,
            tx_id=12347,
            slot_no=5000000,
        )

        assert delegation.addr_id == 100
        assert delegation.cert_index == 2
        assert delegation.pool_hash_id == 200
        assert delegation.active_epoch_no == 252
        assert delegation.tx_id == 12347
        assert delegation.slot_no == 5000000
        assert delegation.redeemer_id is None
        assert delegation.id_ is None

    def test_delegation_table_name(self):
        """Test Delegation has correct table name."""
        assert Delegation.__tablename__ == "delegation"

    def test_delegation_with_redeemer(self):
        """Test Delegation with redeemer for script-based stake address."""
        delegation = Delegation(
            addr_id=100,
            pool_hash_id=200,
            active_epoch_no=252,
            tx_id=12347,
            redeemer_id=600,
        )

        assert delegation.redeemer_id == 600


class TestDelegationVoteModel:
    """Test DelegationVote model functionality."""

    def test_delegation_vote_creation(self):
        """Test DelegationVote model instantiation."""
        vote_delegation = DelegationVote(
            addr_id=100,
            cert_index=3,
            drep_hash_id=300,
            tx_id=12348,
            redeemer_id=700,
        )

        assert vote_delegation.addr_id == 100
        assert vote_delegation.cert_index == 3
        assert vote_delegation.drep_hash_id == 300
        assert vote_delegation.tx_id == 12348
        assert vote_delegation.redeemer_id == 700
        assert vote_delegation.id_ is None

    def test_delegation_vote_table_name(self):
        """Test DelegationVote has correct table name."""
        assert DelegationVote.__tablename__ == "delegation_vote"

    def test_delegation_vote_conway_era(self):
        """Test DelegationVote represents Conway era governance feature."""
        vote_delegation = DelegationVote(
            addr_id=100,
            drep_hash_id=300,
            tx_id=12348,
        )

        # Conway era features
        assert vote_delegation.drep_hash_id == 300  # DRep delegation
        assert vote_delegation.redeemer_id is None  # Optional redeemer


class TestEpochStakeModel:
    """Test EpochStake model functionality."""

    def test_epoch_stake_creation(self):
        """Test EpochStake model instantiation."""
        epoch_stake = EpochStake(
            addr_id=100,
            pool_id=200,
            amount=50000000000,  # 50,000 ADA in lovelace
            epoch_no=252,
        )

        assert epoch_stake.addr_id == 100
        assert epoch_stake.pool_id == 200
        assert epoch_stake.amount == 50000000000
        assert epoch_stake.epoch_no == 252
        assert epoch_stake.id_ is None

    def test_epoch_stake_table_name(self):
        """Test EpochStake has correct table name."""
        assert EpochStake.__tablename__ == "epoch_stake"

    def test_epoch_stake_large_amounts(self):
        """Test EpochStake can handle large stake amounts."""
        # Test with 1 million ADA
        large_stake = EpochStake(
            addr_id=100,
            pool_id=200,
            amount=1000000000000,  # 1M ADA in lovelace
            epoch_no=252,
        )

        assert large_stake.amount == 1000000000000

    def test_epoch_stake_historical_tracking(self):
        """Test EpochStake for historical stake distribution tracking."""
        # Multiple epochs for same address/pool combination
        stake_epoch_250 = EpochStake(
            addr_id=100, pool_id=200, amount=50000000000, epoch_no=250
        )
        stake_epoch_251 = EpochStake(
            addr_id=100, pool_id=200, amount=55000000000, epoch_no=251
        )

        assert stake_epoch_250.epoch_no == 250
        assert stake_epoch_251.epoch_no == 251
        assert stake_epoch_251.amount > stake_epoch_250.amount  # Stake increased


class TestEpochStakeProgressModel:
    """Test EpochStakeProgress model functionality."""

    def test_epoch_stake_progress_creation(self):
        """Test EpochStakeProgress model instantiation."""
        progress = EpochStakeProgress(
            epoch_no=252,
            completed=True,
        )

        assert progress.epoch_no == 252
        assert progress.completed is True
        assert progress.id_ is None

    def test_epoch_stake_progress_table_name(self):
        """Test EpochStakeProgress has correct table name."""
        assert EpochStakeProgress.__tablename__ == "epoch_stake_progress"

    def test_epoch_stake_progress_incomplete(self):
        """Test EpochStakeProgress for incomplete calculation."""
        progress = EpochStakeProgress(
            epoch_no=253,
            completed=False,
        )

        assert progress.completed is False

    def test_epoch_stake_progress_monitoring(self):
        """Test EpochStakeProgress for sync monitoring."""
        # Simulating calculation progress
        progress_start = EpochStakeProgress(epoch_no=252, completed=False)
        progress_complete = EpochStakeProgress(epoch_no=252, completed=True)

        assert progress_start.completed is False
        assert progress_complete.completed is True


class TestRewardModel:
    """Test Reward model functionality."""

    def test_reward_creation(self):
        """Test Reward model instantiation."""
        reward = Reward(
            addr_id=100,
            type_=RewardType.MEMBER,
            amount=5000000,  # 5 ADA in lovelace
            earned_epoch=251,
            spendable_epoch=253,
            pool_id=200,
        )

        assert reward.addr_id == 100
        assert reward.type_ == RewardType.MEMBER
        assert reward.amount == 5000000
        assert reward.earned_epoch == 251
        assert reward.spendable_epoch == 253
        assert reward.pool_id == 200

    def test_reward_table_name(self):
        """Test Reward has correct table name."""
        assert Reward.__tablename__ == "reward"

    def test_reward_types(self):
        """Test all RewardType enum values."""
        assert RewardType.LEADER == "leader"
        assert RewardType.MEMBER == "member"
        assert RewardType.POOL_DEPOSIT_REFUND == "pool_deposit_refund"
        assert RewardType.REFUND == "refund"
        assert RewardType.RESERVES == "reserves"
        assert RewardType.TREASURY == "treasury"

    def test_reward_leader_type(self):
        """Test Reward for block production (leader) rewards."""
        leader_reward = Reward(
            addr_id=100,
            type_=RewardType.LEADER,
            amount=10000000,  # 10 ADA
            earned_epoch=251,
            spendable_epoch=253,
            pool_id=200,
        )

        assert leader_reward.type_ == RewardType.LEADER
        assert leader_reward.pool_id == 200  # Associated with pool

    def test_reward_member_type(self):
        """Test Reward for delegation (member) rewards."""
        member_reward = Reward(
            addr_id=100,
            type_=RewardType.MEMBER,
            amount=2000000,  # 2 ADA
            earned_epoch=251,
            spendable_epoch=253,
            pool_id=200,
        )

        assert member_reward.type_ == RewardType.MEMBER

    def test_reward_treasury_type(self):
        """Test Reward for treasury distribution."""
        treasury_reward = Reward(
            addr_id=100,
            type_=RewardType.TREASURY,
            amount=1000000,  # 1 ADA
            earned_epoch=251,
            spendable_epoch=253,
        )

        assert treasury_reward.type_ == RewardType.TREASURY
        assert treasury_reward.pool_id is None  # No pool association

    def test_reward_reserves_type(self):
        """Test Reward for reserves distribution."""
        reserves_reward = Reward(
            addr_id=100,
            type_=RewardType.RESERVES,
            amount=500000,  # 0.5 ADA
            earned_epoch=251,
            spendable_epoch=253,
        )

        assert reserves_reward.type_ == RewardType.RESERVES

    def test_reward_timing(self):
        """Test Reward earned vs spendable epoch timing."""
        reward = Reward(
            addr_id=100,
            type=RewardType.MEMBER,
            amount=5000000,
            earned_epoch=250,
            spendable_epoch=252,  # 2 epochs later
        )

        assert reward.earned_epoch == 250
        assert reward.spendable_epoch == 252
        assert reward.spendable_epoch > reward.earned_epoch

    def test_reward_large_amounts(self):
        """Test Reward can handle large reward amounts."""
        large_reward = Reward(
            addr_id=100,
            type=RewardType.LEADER,
            amount=100000000000,  # 100,000 ADA
            earned_epoch=251,
            spendable_epoch=253,
        )

        assert large_reward.amount == 100000000000


class TestStakingModelsIntegration:
    """Test integration aspects of staking models."""

    def test_all_models_have_primary_keys(self):
        """Test all staking models have primary key fields."""
        models_with_id = [
            StakeRegistration,
            StakeDeregistration,
            Delegation,
            DelegationVote,
            EpochStake,
            EpochStakeProgress,
        ]

        # Test models with standard id_ primary key
        for model in models_with_id:
            instance = model()
            assert hasattr(instance, "id_")
            assert instance.id_ is None  # Should be None for new instances

        # Test Reward model has composite primary key fields
        reward = Reward()
        assert hasattr(reward, "addr_id")
        assert hasattr(reward, "type_")
        assert hasattr(reward, "earned_epoch")
        assert hasattr(reward, "pool_id")
        assert reward.addr_id is None
        assert reward.type_ is None
        assert reward.earned_epoch is None
        assert reward.pool_id is None

    def test_model_inheritance(self):
        """Test staking models inherit from DBSyncBase."""
        from dbsync.models.base import DBSyncBase

        models = [
            StakeRegistration,
            StakeDeregistration,
            Delegation,
            DelegationVote,
            EpochStake,
            EpochStakeProgress,
            Reward,
        ]

        for model in models:
            assert issubclass(model, DBSyncBase)

    def test_model_table_definitions(self):
        """Test all models have table definitions."""
        models_and_tables = [
            (StakeRegistration, "stake_registration"),
            (StakeDeregistration, "stake_deregistration"),
            (Delegation, "delegation"),
            (DelegationVote, "delegation_vote"),
            (EpochStake, "epoch_stake"),
            (EpochStakeProgress, "epoch_stake_progress"),
            (Reward, "reward"),
        ]

        for model, expected_table in models_and_tables:
            assert hasattr(model, "__tablename__")
            assert model.__tablename__ == expected_table

    def test_foreign_key_relationships(self):
        """Test foreign key relationships are properly defined."""
        # Test stake address relationships
        registration = StakeRegistration(addr_id=100)
        delegation = Delegation(addr_id=100)
        reward = Reward(addr_id=100)

        assert registration.addr_id == 100
        assert delegation.addr_id == 100
        assert reward.addr_id == 100

        # Test transaction relationships
        registration_tx = StakeRegistration(tx_id=12345)
        delegation_tx = Delegation(tx_id=12345)

        assert registration_tx.tx_id == 12345
        assert delegation_tx.tx_id == 12345

        # Test pool relationships
        delegation_pool = Delegation(pool_hash_id=200)
        epoch_stake_pool = EpochStake(pool_id=200)
        reward_pool = Reward(pool_id=200)

        assert delegation_pool.pool_hash_id == 200
        assert epoch_stake_pool.pool_id == 200
        assert reward_pool.pool_id == 200

    def test_epoch_consistency(self):
        """Test epoch number consistency across models."""
        epoch_no = 252

        registration = StakeRegistration(epoch_no=epoch_no)
        delegation = Delegation(active_epoch_no=epoch_no)
        epoch_stake = EpochStake(epoch_no=epoch_no)
        progress = EpochStakeProgress(epoch_no=epoch_no)
        reward = Reward(earned_epoch=epoch_no)

        assert registration.epoch_no == epoch_no
        assert delegation.active_epoch_no == epoch_no
        assert epoch_stake.epoch_no == epoch_no
        assert progress.epoch_no == epoch_no
        assert reward.earned_epoch == epoch_no

    def test_staking_lifecycle_simulation(self):
        """Test complete staking lifecycle simulation."""
        addr_id = 100
        pool_id = 200
        tx_id_base = 12000
        epoch_start = 250

        # 1. Stake registration
        registration = StakeRegistration(
            addr_id=addr_id,
            epoch_no=epoch_start,
            tx_id=tx_id_base + 1,
        )

        # 2. Delegation to pool
        delegation = Delegation(
            addr_id=addr_id,
            pool_hash_id=pool_id,
            active_epoch_no=epoch_start + 1,
            tx_id=tx_id_base + 2,
        )

        # 3. Epoch stake snapshot
        epoch_stake = EpochStake(
            addr_id=addr_id,
            pool_id=pool_id,
            amount=50000000000,  # 50K ADA
            epoch_no=epoch_start + 2,
        )

        # 4. Reward earned
        reward = Reward(
            addr_id=addr_id,
            type=RewardType.MEMBER,
            amount=5000000,  # 5 ADA
            earned_epoch=epoch_start + 2,
            spendable_epoch=epoch_start + 4,
            pool_id=pool_id,
        )

        # 5. Deregistration
        deregistration = StakeDeregistration(
            addr_id=addr_id,
            epoch_no=epoch_start + 10,
            tx_id=tx_id_base + 10,
        )

        # Verify lifecycle progression
        assert registration.epoch_no == epoch_start
        assert delegation.active_epoch_no == epoch_start + 1
        assert epoch_stake.epoch_no == epoch_start + 2
        assert reward.earned_epoch == epoch_start + 2
        assert deregistration.epoch_no == epoch_start + 10

        # Verify consistency
        assert all(
            model.addr_id == addr_id
            for model in [registration, delegation, epoch_stake, reward, deregistration]
        )
        assert delegation.pool_hash_id == epoch_stake.pool_id == reward.pool_id
