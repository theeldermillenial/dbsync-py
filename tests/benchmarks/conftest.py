"""Benchmark test configuration and fixtures."""

import pytest
from sqlmodel import Session, create_engine

from dbsync.config import DatabaseConfig
from dbsync.models import *  # Import all models for benchmarking


@pytest.fixture(scope="session")
def benchmark_config():
    """Configuration for benchmark tests."""
    return DatabaseConfig()


@pytest.fixture(scope="session")
def benchmark_engine(benchmark_config):
    """Database engine for benchmarks (if available)."""
    try:
        engine = create_engine(
            benchmark_config.to_url(),
            echo=False,  # Disable echo for cleaner benchmark output
            pool_pre_ping=True,
            pool_recycle=300,
        )
        # Test connection
        with engine.connect():
            pass
        return engine
    except Exception:
        pytest.skip("Database not available for benchmarks")


@pytest.fixture
def benchmark_session(benchmark_engine):
    """Database session for benchmarks."""
    with Session(benchmark_engine) as session:
        yield session


# Sample test data for benchmarking
@pytest.fixture
def sample_block_data():
    """Sample block data for benchmarking."""
    return {
        "id_": 1,
        "hash_": b"a" * 32,
        "epoch_no": 100,
        "slot_no": 1000000,
        "epoch_slot_no": 21600,
        "block_no": 500000,
        "previous_id": None,
        "slot_leader_id": 1,
        "size": 1024,
        "time": "2023-01-01T12:00:00",
        "tx_count": 10,
        "proto_major": 8,
        "proto_minor": 0,
        "vrf_key": "vrf_test_key",
        "op_cert": b"cert_data",
        "op_cert_counter": 1,
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for benchmarking."""
    return {
        "id_": 1,
        "hash_": b"b" * 32,
        "block_id": 1,
        "block_index": 0,
        "out_sum": 1000000,
        "fee": 170000,
        "deposit": 0,
        "size": 512,
        "invalid_before": None,
        "invalid_hereafter": None,
        "valid_contract": True,
        "script_size": 0,
    }


@pytest.fixture
def sample_multi_asset_data():
    """Sample multi-asset data for benchmarking."""
    return {
        "id_": 1,
        "policy": b"c" * 28,
        "name": b"TestToken",
        "fingerprint": "asset1abc123def456",
    }
