"""Unit tests for SCHEMA-003: Core Blockchain Infrastructure Models.

Tests for Block, Transaction, Epoch, Address, SlotLeader, and other core blockchain models.
"""

import datetime

from dbsync.models import (
    Address,
    Block,
    Epoch,
    EpochSyncTime,
    ReverseIndex,
    SchemaVersion,
    SlotLeader,
    StakeAddress,
    Transaction,
)


class TestBlockModel:
    """Test Block model functionality."""

    def test_block_creation(self):
        """Test Block model instantiation."""
        block_hash = b"\x01" * 32
        timestamp = datetime.datetime.now(datetime.UTC)

        block = Block(
            hash_=block_hash,
            block_no=1000,
            slot_no=2000,
            epoch_no=50,
            time=timestamp,
            size=1024,
            tx_count=25,
            proto_major=8,
            proto_minor=0,
        )

        assert block.hash_ == block_hash
        assert block.block_no == 1000
        assert block.slot_no == 2000
        assert block.epoch_no == 50
        assert block.time == timestamp
        assert block.size == 1024
        assert block.tx_count == 25
        assert block.proto_major == 8
        assert block.proto_minor == 0

    def test_block_table_name(self):
        """Test Block table name."""
        assert Block.__tablename__ == "block"

    def test_block_primary_key(self):
        """Test Block has primary key."""
        block = Block()
        assert hasattr(block, "id_")
        assert block.id_ is None  # Should be None for new instances

    def test_block_relationships(self):
        """Test Block has required relationships."""
        block = Block()
        assert hasattr(block, "slot_leader")
        assert hasattr(block, "epoch")
        assert hasattr(block, "previous_block")
        assert hasattr(block, "next_blocks")
        assert hasattr(block, "transactions")

    def test_block_foreign_keys(self):
        """Test Block foreign key fields."""
        block = Block(
            previous_id=999,
            slot_leader_id=5,
        )
        assert block.previous_id == 999
        assert block.slot_leader_id == 5


class TestTransactionModel:
    """Test Transaction model functionality."""

    def test_transaction_creation(self):
        """Test Transaction model instantiation."""
        tx_hash = b"\x02" * 32

        tx = Transaction(
            hash_=tx_hash,
            block_id=1,
            block_index=0,
            fee=200000,
            out_sum=5000000,
            deposit=2000000,
            size=512,
            invalid_before=12345,
            invalid_hereafter=54321,
            valid_contract=True,
            script_size=128,
        )

        assert tx.hash_ == tx_hash
        assert tx.block_id == 1
        assert tx.block_index == 0
        assert tx.fee == 200000
        assert tx.out_sum == 5000000
        assert tx.deposit == 2000000
        assert tx.size == 512
        assert tx.invalid_before == 12345
        assert tx.invalid_hereafter == 54321
        assert tx.valid_contract is True
        assert tx.script_size == 128

    def test_transaction_table_name(self):
        """Test Transaction table name."""
        assert Transaction.__tablename__ == "tx"

    def test_transaction_relationships(self):
        """Test Transaction has required relationships."""
        tx = Transaction()
        assert hasattr(tx, "block")


class TestEpochModel:
    """Test Epoch model functionality."""

    def test_epoch_creation(self):
        """Test Epoch model instantiation."""
        start_time = datetime.datetime.now(datetime.UTC)
        end_time = start_time + datetime.timedelta(days=5)

        epoch = Epoch(
            no=100,
            out_sum=1000000000000,
            fees=500000000,
            tx_count=75000,
            blk_count=21600,
            start_time=start_time,
            end_time=end_time,
        )

        assert epoch.no == 100
        assert epoch.out_sum == 1000000000000
        assert epoch.fees == 500000000
        assert epoch.tx_count == 75000
        assert epoch.blk_count == 21600
        assert epoch.start_time == start_time
        assert epoch.end_time == end_time

    def test_epoch_table_name(self):
        """Test Epoch table name."""
        assert Epoch.__tablename__ == "epoch"

    def test_epoch_relationships(self):
        """Test Epoch has required relationships."""
        epoch = Epoch()
        assert hasattr(epoch, "blocks")


class TestAddressModel:
    """Test Address model functionality."""

    def test_address_creation(self):
        """Test Address model instantiation."""
        address_hash = b"\x03" * 28

        address = Address(
            hash_=address_hash,
            view="addr1xyz123...",
            stake_address_id=42,
        )

        assert address.hash_ == address_hash
        assert address.view == "addr1xyz123..."
        assert address.stake_address_id == 42

    def test_address_table_name(self):
        """Test Address table name."""
        assert Address.__tablename__ == "address"

    def test_address_relationships(self):
        """Test Address has required relationships."""
        address = Address()
        assert hasattr(address, "stake_address")


class TestStakeAddressModel:
    """Test StakeAddress model functionality."""

    def test_stake_address_creation(self):
        """Test StakeAddress model instantiation."""
        stake_hash = b"\x04" * 28
        script_hash = b"\x05" * 28

        stake_address = StakeAddress(
            hash_raw=stake_hash,
            view="stake1xyz456...",
            script_hash=script_hash,
        )

        assert stake_address.hash_raw == stake_hash
        assert stake_address.view == "stake1xyz456..."
        assert stake_address.script_hash == script_hash

    def test_stake_address_table_name(self):
        """Test StakeAddress table name."""
        assert StakeAddress.__tablename__ == "stake_address"

    def test_stake_address_relationships(self):
        """Test StakeAddress has required relationships."""
        stake_address = StakeAddress()
        assert hasattr(stake_address, "addresses")


class TestSlotLeaderModel:
    """Test SlotLeader model functionality."""

    def test_slot_leader_creation(self):
        """Test SlotLeader model instantiation."""
        leader_hash = b"\x06" * 28

        slot_leader = SlotLeader(
            hash_=leader_hash,
            pool_hash_id=123,
            description="Test Pool",
        )

        assert slot_leader.hash_ == leader_hash
        assert slot_leader.pool_hash_id == 123
        assert slot_leader.description == "Test Pool"

    def test_slot_leader_table_name(self):
        """Test SlotLeader table name."""
        assert SlotLeader.__tablename__ == "slot_leader"

    def test_slot_leader_relationships(self):
        """Test SlotLeader has required relationships."""
        slot_leader = SlotLeader()
        assert hasattr(slot_leader, "blocks")


class TestSchemaVersionModel:
    """Test SchemaVersion model functionality."""

    def test_schema_version_creation(self):
        """Test SchemaVersion model instantiation."""
        version = SchemaVersion(
            stage_one=13,
            stage_two=2,
            stage_three=0,
        )

        assert version.stage_one == 13
        assert version.stage_two == 2
        assert version.stage_three == 0

    def test_schema_version_table_name(self):
        """Test SchemaVersion table name."""
        assert SchemaVersion.__tablename__ == "schema_version"


class TestEpochSyncTimeModel:
    """Test EpochSyncTime model functionality."""

    def test_epoch_sync_time_creation(self):
        """Test EpochSyncTime model instantiation."""
        sync_time = EpochSyncTime(
            no=50,
            seconds=3600,
            state="synced",
        )

        assert sync_time.no == 50
        assert sync_time.seconds == 3600
        assert sync_time.state == "synced"

    def test_epoch_sync_time_table_name(self):
        """Test EpochSyncTime table name."""
        assert EpochSyncTime.__tablename__ == "epoch_sync_time"


class TestReverseIndexModel:
    """Test ReverseIndex model functionality."""

    def test_reverse_index_creation(self):
        """Test ReverseIndex model instantiation."""
        reverse_index = ReverseIndex(
            block_id=1000,
            min_ids="[1,2,3]",
        )

        assert reverse_index.block_id == 1000
        assert reverse_index.min_ids == "[1,2,3]"

    def test_reverse_index_table_name(self):
        """Test ReverseIndex table name."""
        assert ReverseIndex.__tablename__ == "reverse_index"

    def test_reverse_index_relationships(self):
        """Test ReverseIndex has required relationships."""
        reverse_index = ReverseIndex()
        assert hasattr(reverse_index, "block")


class TestBlockchainModelTypes:
    """Test SCHEMA-003 model type annotations and inheritance."""

    def test_all_models_have_primary_keys(self):
        """Test all blockchain models have primary key fields."""
        models = [
            Block,
            Transaction,
            Epoch,
            Address,
            StakeAddress,
            SlotLeader,
            SchemaVersion,
            EpochSyncTime,
            ReverseIndex,
        ]

        for model in models:
            instance = model()
            assert hasattr(instance, "id_")
            assert instance.id_ is None  # Should be None for new instances

    def test_model_inheritance(self):
        """Test blockchain models inherit from DBSyncBase."""
        from dbsync.models.base import DBSyncBase

        models = [
            Block,
            Transaction,
            Epoch,
            Address,
            StakeAddress,
            SlotLeader,
            SchemaVersion,
            EpochSyncTime,
            ReverseIndex,
        ]

        for model in models:
            assert issubclass(model, DBSyncBase)

    def test_model_table_definitions(self):
        """Test all models have table definitions."""
        models = [
            (Block, "block"),
            (Transaction, "tx"),
            (Epoch, "epoch"),
            (Address, "address"),
            (StakeAddress, "stake_address"),
            (SlotLeader, "slot_leader"),
            (SchemaVersion, "schema_version"),
            (EpochSyncTime, "epoch_sync_time"),
            (ReverseIndex, "reverse_index"),
        ]

        for model, expected_table_name in models:
            assert hasattr(model, "__tablename__")
            assert model.__tablename__ == expected_table_name


class TestBlockchainModelIntegration:
    """Integration tests for SCHEMA-003 blockchain models."""

    def test_block_transaction_relationship(self):
        """Test Block-Transaction relationship structure."""
        block = Block(hash_=b"\x01" * 32, block_no=1000)
        tx = Transaction(hash_=b"\x02" * 32, block_id=1)

        # Test that relationship attributes exist
        assert hasattr(block, "transactions")
        assert hasattr(tx, "block")

    def test_block_epoch_relationship(self):
        """Test Block-Epoch relationship structure."""
        block = Block(hash_=b"\x01" * 32, epoch_no=50)
        epoch = Epoch(no=50)

        # Test that relationship attributes exist
        assert hasattr(block, "epoch")
        assert hasattr(epoch, "blocks")

    def test_address_stake_address_relationship(self):
        """Test Address-StakeAddress relationship structure."""
        address = Address(hash_=b"\x03" * 28, stake_address_id=1)
        stake_address = StakeAddress(hash_=b"\x04" * 28)

        # Test that relationship attributes exist
        assert hasattr(address, "stake_address")
        assert hasattr(stake_address, "addresses")

    def test_block_slot_leader_relationship(self):
        """Test Block-SlotLeader relationship structure."""
        block = Block(hash_=b"\x01" * 32, slot_leader_id=5)
        slot_leader = SlotLeader(hash_=b"\x06" * 28)

        # Test that relationship attributes exist
        assert hasattr(block, "slot_leader")
        assert hasattr(slot_leader, "blocks")

    def test_block_self_referential_relationship(self):
        """Test Block self-referential relationship (previous/next blocks)."""
        block = Block(hash_=b"\x01" * 32, previous_id=999)

        # Test that relationship attributes exist
        assert hasattr(block, "previous_block")
        assert hasattr(block, "next_blocks")

    def test_reverse_index_block_relationship(self):
        """Test ReverseIndex-Block relationship structure."""
        reverse_index = ReverseIndex(block_id=1000)

        # Test that relationship attributes exist
        assert hasattr(reverse_index, "block")


class TestBlockchainModelEdgeCases:
    """Test edge cases and validation for SCHEMA-003 models."""

    def test_block_with_minimal_data(self):
        """Test Block with minimal required data."""
        block = Block()

        # Should be able to create with no data
        assert block.id_ is None
        assert block.hash_ is None
        assert block.block_no is None

    def test_transaction_with_zero_fee(self):
        """Test Transaction with zero fee (valid case)."""
        tx = Transaction(fee=0)
        assert tx.fee == 0

    def test_epoch_with_zero_counts(self):
        """Test Epoch with zero block/transaction counts."""
        epoch = Epoch(blk_count=0, tx_count=0)
        assert epoch.blk_count == 0
        assert epoch.tx_count == 0

    def test_address_without_stake_address(self):
        """Test Address without associated stake address."""
        address = Address(hash=b"\x03" * 28)
        assert address.stake_address_id is None

    def test_model_string_representations(self):
        """Test model string representations work."""
        models_with_data = [
            Block(hash=b"\x01" * 32, block_no=1000),
            Transaction(hash=b"\x02" * 32, fee=200000),
            Epoch(no=50, blk_count=21600),
            Address(hash=b"\x03" * 28, view="addr1xyz"),
            StakeAddress(hash=b"\x04" * 28, view="stake1abc"),
            SlotLeader(hash=b"\x05" * 28, description="Test Pool"),
            SchemaVersion(stage_one=13, stage_two=2, stage_three=0),
            EpochSyncTime(no=50, seconds=3600),
            ReverseIndex(block_id=1000, min_ids="[1,2,3]"),
        ]

        for model_instance in models_with_data:
            repr_str = repr(model_instance)
            assert isinstance(repr_str, str)
            assert len(repr_str) > 0
            # Should include class name
            assert model_instance.__class__.__name__ in repr_str


# Summary: SCHEMA-003 (Core Blockchain Infrastructure Models) - 9 models, comprehensive coverage
# Block, Transaction, Epoch, Address, StakeAddress, SlotLeader, SchemaVersion, EpochSyncTime, ReverseIndex
