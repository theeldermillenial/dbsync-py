"""Advanced test fixtures and factories for dbsync models.

This module provides comprehensive test fixtures, factories, and builders
that create realistic test data for all dbsync models. These fixtures
support both unit and integration testing with configurable parameters.
"""

import random
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

import pytest

from dbsync.models.assets import MaTxMint, MaTxOut, MultiAsset
from dbsync.models.blockchain import Block, Epoch, StakeAddress, Transaction
from dbsync.models.governance import (
    DrepRegistration,
    GovActionProposal,
    VotingProcedure,
)
from dbsync.models.pools import PoolHash, PoolMetadataRef, PoolRelay
from dbsync.models.scripts import CostModel, Redeemer, RedeemerData, Script, ScriptType
from dbsync.models.staking import (
    Delegation,
    StakeDeregistration,
    StakeRegistration,
)
from dbsync.models.transactions import TransactionInput, TransactionOutput


class TestDataFactory:
    """Factory class for generating realistic test data."""

    def __init__(self, seed: int | None = None):
        """Initialize factory with optional seed for reproducible data."""
        if seed is not None:
            random.seed(seed)

        self._epoch_counter = 1
        self._block_counter = 1
        self._tx_counter = 1
        self._addr_counter = 1

    def create_hash(self, length: int = 32) -> bytes:
        """Create a random hash of specified length."""
        return bytes([random.randint(0, 255) for _ in range(length)])

    def create_epoch_time(self, epoch_no: int) -> datetime:
        """Create realistic epoch start time."""
        # Cardano mainnet launched July 29, 2020
        mainnet_start = datetime(2020, 7, 29, tzinfo=UTC)
        # Each epoch is ~5 days
        return mainnet_start + timedelta(days=epoch_no * 5)

    def create_realistic_address(self) -> str:
        """Create a realistic Cardano address."""
        # Simplified testnet address format
        return f"addr_test1qz{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=50))}"

    def create_asset_name(self, readable: bool = False) -> bytes:
        """Create asset name bytes."""
        if readable:
            names = [b"TOKEN", b"COIN", b"NFT", b"ASSET", b"GOLD", b"SILVER"]
            return random.choice(names)
        return bytes([random.randint(0, 255) for _ in range(random.randint(0, 32))])


# Global factory instance
factory = TestDataFactory()


# Basic Model Fixtures
@pytest.fixture
def sample_epoch():
    """Create a sample Epoch."""
    epoch_no = factory._epoch_counter
    factory._epoch_counter += 1

    start_time = factory.create_epoch_time(epoch_no)
    end_time = start_time + timedelta(days=5)

    return Epoch(
        no=epoch_no,
        start_time=start_time,
        end_time=end_time,
        tx_count=random.randint(1000, 50000),
        blk_count=random.randint(100, 2000),
        out_sum=random.randint(1000000000, 100000000000),  # 1K to 100K ADA
    )


@pytest.fixture
def sample_block(sample_epoch):
    """Create a sample Block."""
    block_no = factory._block_counter
    factory._block_counter += 1

    return Block(
        hash_=factory.create_hash(32),
        epoch_no=sample_epoch.no,
        slot_no=random.randint(1000000, 9999999),
        block_no=block_no,
        previous_id=block_no - 1 if block_no > 1 else None,
        size=random.randint(1000, 65536),
        tx_count=random.randint(1, 200),
        proto_major=8,
        proto_minor=0,
        vrf_key="vrf_" + "a" * 64,
        op_cert="cert_" + "b" * 128,
    )


@pytest.fixture
def sample_transaction(sample_block):
    """Create a sample Transaction."""
    tx_id = factory._tx_counter
    factory._tx_counter += 1

    return Transaction(
        id_=tx_id,
        hash_=factory.create_hash(32),
        block_id=sample_block.id_ or 1,
        fee=random.randint(150000, 2000000),  # 0.15 to 2 ADA
        out_sum=random.randint(1000000, 1000000000),  # 1 to 1000 ADA
        size=random.randint(200, 16384),
        invalid_before=None,
        invalid_hereafter=random.randint(1000000, 9999999),
        valid_contract=True,
        script_size=random.randint(0, 8192),
    )


@pytest.fixture
def sample_stake_address():
    """Create a sample StakeAddress."""
    return StakeAddress(
        id_=factory._addr_counter,
        hash_raw=factory.create_hash(28),
        view=f"stake_test1{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=50))}",
        script_hash=factory.create_hash(28) if random.choice([True, False]) else None,
    )


# Transaction-related Fixtures
@pytest.fixture
def sample_tx_output(sample_transaction):
    """Create a sample TransactionOutput."""
    return TransactionOutput(
        tx_id=sample_transaction.id_ or 1,
        index=random.randint(0, 10),
        address_id=random.randint(1, 1000),
        stake_address_id=random.randint(1, 1000)
        if random.choice([True, False])
        else None,
        value=random.randint(1000000, 100000000),  # 1 to 100 ADA
        data_hash=factory.create_hash(32) if random.choice([True, False]) else None,
        inline_datum_id=random.randint(1, 1000)
        if random.choice([True, False])
        else None,
        reference_script_id=random.randint(1, 1000)
        if random.choice([True, False])
        else None,
    )


@pytest.fixture
def sample_tx_input(sample_transaction):
    """Create a sample TransactionInput."""
    return TransactionInput(
        tx_in_id=sample_transaction.id_ or 1,
        tx_out_id=random.randint(1, 1000),
        tx_out_index=random.randint(0, 10),
        redeemer_id=random.randint(1, 100) if random.choice([True, False]) else None,
    )


# Asset-related Fixtures
@pytest.fixture
def sample_multi_asset():
    """Create a sample MultiAsset."""
    return MultiAsset(
        id_=random.randint(1, 10000),
        policy=factory.create_hash(28),
        name=factory.create_asset_name(readable=True),
        fingerprint=f"asset1{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=50))}",
    )


@pytest.fixture
def sample_ma_tx_out(sample_tx_output, sample_multi_asset):
    """Create a sample MaTxOut (Multi-Asset Transaction Output)."""
    return MaTxOut(
        id_=random.randint(1, 10000),
        quantity=random.randint(1, 1000000000),
        tx_out_id=sample_tx_output.id_ or 1,
        ident=sample_multi_asset.id_ or 1,
    )


@pytest.fixture
def sample_ma_tx_mint(sample_transaction, sample_multi_asset):
    """Create a sample MaTxMint (Multi-Asset Transaction Mint)."""
    return MaTxMint(
        id_=random.randint(1, 10000),
        quantity=random.randint(-1000000, 1000000),  # Can be negative for burning
        tx_id=sample_transaction.id_ or 1,
        ident=sample_multi_asset.id_ or 1,
    )


# Script-related Fixtures
@pytest.fixture
def sample_native_script(sample_transaction):
    """Create a sample native Script."""
    return Script(
        id_=random.randint(1, 10000),
        tx_id=sample_transaction.id_ or 1,
        hash_=factory.create_hash(28),
        type_=ScriptType.NATIVE,
        json_={"type": "sig", "keyHash": factory.create_hash(28).hex()},
        serialised_size=random.randint(50, 500),
    )


@pytest.fixture
def sample_plutus_script(sample_transaction):
    """Create a sample Plutus Script."""
    return Script(
        id_=random.randint(1, 10000),
        tx_id=sample_transaction.id_ or 1,
        hash_=factory.create_hash(28),
        type_=random.choice(
            [ScriptType.PLUTUS_V1, ScriptType.PLUTUS_V2, ScriptType.PLUTUS_V3]
        ),
        bytes_=bytes(
            [random.randint(0, 255) for _ in range(random.randint(500, 8192))]
        ),
        serialised_size=random.randint(500, 8192),
    )


@pytest.fixture
def sample_redeemer_data(sample_transaction):
    """Create a sample RedeemerData."""
    return RedeemerData(
        id_=random.randint(1, 10000),
        hash_=factory.create_hash(32),
        tx_id=sample_transaction.id_ or 1,
        value={"constructor": 0, "fields": [{"int": 42}]},
        bytes_=bytes([random.randint(0, 255) for _ in range(random.randint(50, 1000))]),
    )


@pytest.fixture
def sample_redeemer(sample_transaction, sample_plutus_script, sample_redeemer_data):
    """Create a sample Redeemer."""
    return Redeemer(
        id_=random.randint(1, 10000),
        tx_id=sample_transaction.id_ or 1,
        unit_mem=random.randint(100000, 10000000),
        unit_steps=random.randint(1000000, 1000000000),
        fee=random.randint(100000, 2000000),
        purpose=random.choice(["spend", "mint", "cert", "reward"]),
        index=random.randint(0, 10),
        script_hash=sample_plutus_script.hash_,
        redeemer_data_id=sample_redeemer_data.id_,
    )


@pytest.fixture
def sample_cost_model():
    """Create a sample CostModel."""
    # Realistic Plutus V2 cost model parameters
    costs = {
        "addInteger-cpu-arguments-intercept": 205665,
        "addInteger-cpu-arguments-slope": 812,
        "addInteger-memory-arguments-intercept": 1,
        "addInteger-memory-arguments-slope": 1,
        "appendByteString-cpu-arguments-intercept": 1000,
        "appendByteString-cpu-arguments-slope": 571,
        "appendByteString-memory-arguments-intercept": 0,
        "appendByteString-memory-arguments-slope": 1,
        "appendString-cpu-arguments-intercept": 1000,
        "appendString-cpu-arguments-slope": 24177,
        "appendString-memory-arguments-intercept": 4,
        "appendString-memory-arguments-slope": 1,
    }

    return CostModel(
        id_=random.randint(1, 100), hash_=factory.create_hash(32), costs=costs
    )


# Staking-related Fixtures
@pytest.fixture
def sample_stake_registration(sample_transaction, sample_stake_address):
    """Create a sample StakeRegistration."""
    return StakeRegistration(
        id_=random.randint(1, 10000),
        addr_id=sample_stake_address.id_ or 1,
        cert_index=random.randint(0, 5),
        epoch_no=random.randint(200, 500),
        tx_id=sample_transaction.id_ or 1,
    )


@pytest.fixture
def sample_stake_deregistration(sample_transaction, sample_stake_address):
    """Create a sample StakeDeregistration."""
    return StakeDeregistration(
        id_=random.randint(1, 10000),
        addr_id=sample_stake_address.id_ or 1,
        cert_index=random.randint(0, 5),
        epoch_no=random.randint(200, 500),
        tx_id=sample_transaction.id_ or 1,
    )


@pytest.fixture
def sample_delegation(sample_transaction, sample_stake_address):
    """Create a sample Delegation."""
    return Delegation(
        id_=random.randint(1, 10000),
        addr_id=sample_stake_address.id_ or 1,
        cert_index=random.randint(0, 5),
        pool_hash_id=random.randint(1, 1000),
        active_epoch_no=random.randint(200, 500),
        tx_id=sample_transaction.id_ or 1,
        slot_no=random.randint(1000000, 9999999),
        redeemer_id=random.randint(1, 100) if random.choice([True, False]) else None,
    )


# Pool-related Fixtures
@pytest.fixture
def sample_pool_hash():
    """Create a sample PoolHash."""
    return PoolHash(
        id_=random.randint(1, 10000),
        hash_raw=factory.create_hash(28),
        view=f"pool1{''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=50))}",
    )


@pytest.fixture
def sample_pool_metadata_ref(sample_pool_hash):
    """Create a sample PoolMetadataRef."""
    return PoolMetadataRef(
        id_=random.randint(1, 10000),
        pool_id=sample_pool_hash.id_ or 1,
        url="https://example-pool.com/metadata.json",
        hash_=factory.create_hash(32),
        registered_tx_id=random.randint(1, 1000),
    )


@pytest.fixture
def sample_pool_relay(sample_pool_hash):
    """Create a sample PoolRelay."""
    return PoolRelay(
        id_=random.randint(1, 10000),
        update_id=random.randint(1, 1000),
        ipv4="192.168.1.100",
        ipv6=None,
        dns_name="relay.example-pool.com",
        port=3001,
    )


# Governance-related Fixtures (Conway Era)
@pytest.fixture
def sample_drep_registration(sample_transaction, sample_stake_address):
    """Create a sample DrepRegistration."""
    return DrepRegistration(
        id_=random.randint(1, 10000),
        tx_id=sample_transaction.id_ or 1,
        cert_index=random.randint(0, 5),
        deposit=500000000,  # 500 ADA deposit
        drep_hash_id=sample_stake_address.id_ or 1,
        voting_anchor_id=random.randint(1, 100)
        if random.choice([True, False])
        else None,
    )


@pytest.fixture
def sample_voting_procedure(sample_transaction):
    """Create a sample VotingProcedure."""
    voter_role = random.choice(["ConstitutionalCommittee", "DRep", "SPO"])
    voter_id = random.randint(1, 1000)

    # Set the appropriate voter field based on role
    kwargs = {
        "id_": random.randint(1, 10000),
        "tx_id": sample_transaction.id_ or 1,
        "index": random.randint(0, 10),
        "gov_action_proposal_id": random.randint(1, 1000),
        "voter_role": voter_role,
        "vote": random.choice(["Yes", "No", "Abstain"]),
        "voting_anchor_id": random.randint(1, 100)
        if random.choice([True, False])
        else None,
    }

    if voter_role == "ConstitutionalCommittee":
        kwargs["committee_voter"] = voter_id
    elif voter_role == "DRep":
        kwargs["drep_voter"] = voter_id
    else:  # SPO
        kwargs["pool_voter"] = voter_id

    return VotingProcedure(**kwargs)


@pytest.fixture
def sample_gov_action_proposal(sample_transaction, sample_stake_address):
    """Create a sample GovActionProposal."""
    return GovActionProposal(
        id_=random.randint(1, 10000),
        tx_id=sample_transaction.id_ or 1,
        index=random.randint(0, 10),
        prev_gov_action_proposal=random.randint(1, 100)
        if random.choice([True, False])
        else None,
        deposit=random.randint(1000000000, 10000000000),  # 1000-10000 ADA
        return_address=sample_stake_address.id_ or 1,
        expiration=random.randint(500, 600),  # Epoch number
        ratified_epoch=random.randint(600, 700)
        if random.choice([True, False])
        else None,
        enacted_epoch=random.randint(700, 800)
        if random.choice([True, False])
        else None,
        dropped_epoch=None,
        expired_epoch=None,
        type_="ParameterChange",
        description="Test governance action",
        param_proposal=random.randint(1, 100) if random.choice([True, False]) else None,
    )


# Composite Fixtures (Multiple Related Models)
@pytest.fixture
def complete_transaction_scenario(
    sample_transaction,
    sample_tx_output,
    sample_tx_input,
    sample_ma_tx_out,
    sample_redeemer,
):
    """Create a complete transaction scenario with all related models."""
    return {
        "transaction": sample_transaction,
        "outputs": [sample_tx_output],
        "inputs": [sample_tx_input],
        "multi_assets": [sample_ma_tx_out],
        "redeemers": [sample_redeemer],
    }


@pytest.fixture
def complete_staking_scenario(
    sample_stake_address, sample_stake_registration, sample_pool_hash
):
    """Create a complete staking scenario with properly linked IDs."""
    # Create delegation with matching pool_hash_id
    delegation = Delegation(
        id_=random.randint(1, 10000),
        addr_id=sample_stake_address.id_ or 1,
        cert_index=random.randint(0, 5),
        pool_hash_id=sample_pool_hash.id_ or 1,  # Match the pool hash ID
        active_epoch_no=random.randint(200, 500),
        tx_id=random.randint(1, 10000),
        slot_no=random.randint(1000000, 9999999),
        redeemer_id=random.randint(1, 100) if random.choice([True, False]) else None,
    )

    return {
        "stake_address": sample_stake_address,
        "registration": sample_stake_registration,
        "delegation": delegation,
        "pool": sample_pool_hash,
    }


@pytest.fixture
def complete_governance_scenario(
    sample_drep_registration, sample_voting_procedure, sample_gov_action_proposal
):
    """Create a complete governance scenario."""
    return {
        "drep_registration": sample_drep_registration,
        "voting_procedure": sample_voting_procedure,
        "gov_action_proposal": sample_gov_action_proposal,
    }


# Factory Functions for Bulk Data Generation
def create_epoch_sequence(count: int, start_epoch: int = 1) -> list[Epoch]:
    """Create a sequence of connected epochs."""
    epochs = []
    for i in range(count):
        epoch_no = start_epoch + i
        start_time = factory.create_epoch_time(epoch_no)
        end_time = start_time + timedelta(days=5)

        epoch = Epoch(
            no=epoch_no,
            start_time=start_time,
            end_time=end_time,
            tx_count=random.randint(1000, 50000),
            blk_count=random.randint(100, 2000),
            out_sum=random.randint(1000000000, 100000000000),
        )
        epochs.append(epoch)

    return epochs


def create_block_sequence(count: int, epoch_no: int = 1) -> list[Block]:
    """Create a sequence of connected blocks."""
    blocks = []
    for i in range(count):
        block_no = factory._block_counter
        factory._block_counter += 1

        block = Block(
            hash_=factory.create_hash(32),
            epoch_no=epoch_no,
            slot_no=random.randint(1000000, 9999999),
            block_no=block_no,
            previous_id=blocks[-1].id_ if blocks else None,
            size=random.randint(1000, 65536),
            tx_count=random.randint(1, 200),
            proto_major=8,
            proto_minor=0,
        )
        blocks.append(block)

    return blocks


def create_transaction_batch(count: int, block_id: int = 1) -> list[Transaction]:
    """Create a batch of transactions for a block."""
    transactions = []
    for i in range(count):
        tx_id = factory._tx_counter
        factory._tx_counter += 1

        tx = Transaction(
            id_=tx_id,
            hash_=factory.create_hash(32),
            block_id=block_id,
            fee=random.randint(150000, 2000000),
            out_sum=random.randint(1000000, 1000000000),
            size=random.randint(200, 16384),
            valid_contract=True,
        )
        transactions.append(tx)

    return transactions


# Context Managers for Test Setup
@contextmanager
def reproducible_test_data(seed: int = 42):
    """Context manager for reproducible test data generation."""
    global factory
    old_factory = factory
    factory = TestDataFactory(seed=seed)
    try:
        yield factory
    finally:
        factory = old_factory


@contextmanager
def performance_test_data(scale: str = "small"):
    """Context manager for performance testing with scaled data."""
    scales = {
        "small": {"epochs": 5, "blocks_per_epoch": 10, "txs_per_block": 5},
        "medium": {"epochs": 20, "blocks_per_epoch": 50, "txs_per_block": 20},
        "large": {"epochs": 100, "blocks_per_epoch": 100, "txs_per_block": 50},
    }

    config = scales.get(scale, scales["small"])

    # Generate test data
    epochs = create_epoch_sequence(config["epochs"])
    all_blocks = []
    all_transactions = []

    for epoch in epochs:
        blocks = create_block_sequence(config["blocks_per_epoch"], epoch.no)
        all_blocks.extend(blocks)

        for block in blocks:
            transactions = create_transaction_batch(
                config["txs_per_block"], block.id_ or 1
            )
            all_transactions.extend(transactions)

    yield {
        "epochs": epochs,
        "blocks": all_blocks,
        "transactions": all_transactions,
        "config": config,
    }


# Pytest Markers for Test Categories
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "property_based: Property-based tests")
    config.addinivalue_line("markers", "parameterized: Parameterized tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "governance: Conway era governance tests")
    config.addinivalue_line("markers", "staking: Staking and delegation tests")
    config.addinivalue_line("markers", "scripts: Script and smart contract tests")
    config.addinivalue_line("markers", "assets: Multi-asset tests")
