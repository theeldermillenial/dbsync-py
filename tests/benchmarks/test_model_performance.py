"""Performance benchmarks for dbsync-py models."""

import pytest
from sqlmodel import select

from dbsync.models import (
    Block,
    MultiAsset,
    Transaction,
)


class TestModelInstantiationBenchmarks:
    """Benchmark model instantiation performance."""

    def test_block_model_creation(self, benchmark, sample_block_data):
        """Benchmark Block model instantiation."""

        def create_block():
            return Block(**sample_block_data)

        result = benchmark(create_block)
        assert result.id_ == 1
        assert result.block_no == 500000

    def test_transaction_model_creation(self, benchmark, sample_transaction_data):
        """Benchmark Transaction model instantiation."""

        def create_transaction():
            return Transaction(**sample_transaction_data)

        result = benchmark(create_transaction)
        assert result.id_ == 1
        assert result.fee == 170000

    def test_multi_asset_model_creation(self, benchmark, sample_multi_asset_data):
        """Benchmark MultiAsset model instantiation."""

        def create_multi_asset():
            return MultiAsset(**sample_multi_asset_data)

        result = benchmark(create_multi_asset)
        assert result.id_ == 1
        assert result.fingerprint == "asset1abc123def456"

    def test_bulk_model_creation(self, benchmark, sample_block_data):
        """Benchmark bulk model creation."""

        def create_bulk_blocks():
            blocks = []
            for i in range(100):
                data = sample_block_data.copy()
                data["id_"] = i + 1
                data["block_no"] = 500000 + i
                blocks.append(Block(**data))
            return blocks

        result = benchmark(create_bulk_blocks)
        assert len(result) == 100
        assert result[0].block_no == 500000
        assert result[99].block_no == 500099


class TestQueryBenchmarks:
    """Benchmark database query performance."""

    @pytest.mark.slow
    def test_simple_block_query(self, benchmark, benchmark_session):
        """Benchmark simple block query."""

        def query_blocks():
            return benchmark_session.exec(select(Block).limit(10)).all()

        result = benchmark(query_blocks)
        # Result may be empty if no data, but should execute without error
        assert isinstance(result, list)

    @pytest.mark.slow
    def test_complex_join_query(self, benchmark, benchmark_session):
        """Benchmark complex join query."""

        def complex_query():
            return benchmark_session.exec(
                select(Block, Transaction)
                .join(Transaction, Block.id == Transaction.block_id)
                .limit(5)
            ).all()

        result = benchmark(complex_query)
        assert isinstance(result, list)

    @pytest.mark.slow
    def test_aggregate_query(self, benchmark, benchmark_session):
        """Benchmark aggregate query."""
        from sqlalchemy import func

        def aggregate_query():
            return benchmark_session.exec(select(func.count(Block.id))).first()

        result = benchmark(aggregate_query)
        # Should return a count (could be 0)
        assert result is not None


class TestModelValidationBenchmarks:
    """Benchmark model validation performance."""

    def test_model_validation_performance(self, benchmark):
        """Benchmark Pydantic model validation."""

        def validate_models():
            # Test validation with various model types
            block_data = {
                "id_": 1,
                "hash_": b"a" * 32,
                "epoch_no": 100,
                "slot_no": 1000000,
                "block_no": 500000,
                "time": "2023-01-01T12:00:00",
                "tx_count": 10,
            }

            tx_data = {
                "id_": 1,
                "hash_": b"b" * 32,
                "block_id": 1,
                "block_index": 0,
                "out_sum": 1000000,
                "fee": 170000,
            }

            # Create and validate models
            block = Block(**block_data)
            tx = Transaction(**tx_data)

            return block, tx

        result = benchmark(validate_models)
        assert len(result) == 2
        assert result[0].block_no == 500000
        assert result[1].fee == 170000


class TestSerializationBenchmarks:
    """Benchmark model serialization performance."""

    def test_model_to_dict_performance(self, benchmark, sample_block_data):
        """Benchmark model to dict conversion."""
        block = Block(**sample_block_data)

        def serialize_to_dict():
            return block.model_dump()

        result = benchmark(serialize_to_dict)
        assert isinstance(result, dict)
        assert result["block_no"] == 500000

    def test_model_to_json_performance(self, benchmark, sample_block_data):
        """Benchmark model to JSON conversion."""
        block = Block(**sample_block_data)

        def serialize_to_json():
            return block.model_dump_json()

        result = benchmark(serialize_to_json)
        assert isinstance(result, str)
        assert "500000" in result

    def test_bulk_serialization_performance(self, benchmark, sample_block_data):
        """Benchmark bulk model serialization."""
        blocks = []
        for i in range(50):
            data = sample_block_data.copy()
            data["id_"] = i + 1
            data["block_no"] = 500000 + i
            blocks.append(Block(**data))

        def bulk_serialize():
            return [block.model_dump() for block in blocks]

        result = benchmark(bulk_serialize)
        assert len(result) == 50
        assert all(isinstance(item, dict) for item in result)


class TestTypeConversionBenchmarks:
    """Benchmark type conversion performance."""

    def test_hash_type_conversion(self, benchmark):
        """Benchmark hash type conversions."""

        def convert_hashes():
            # Test various hash conversions
            hash_bytes = b"a" * 32
            hash_hex = hash_bytes.hex()

            # Convert back and forth
            converted_bytes = bytes.fromhex(hash_hex)
            converted_hex = converted_bytes.hex()

            return hash_bytes, hash_hex, converted_bytes, converted_hex

        result = benchmark(convert_hashes)
        assert len(result) == 4
        assert result[0] == result[2]  # Original bytes == converted bytes
        assert result[1] == result[3]  # Original hex == converted hex

    def test_lovelace_conversion(self, benchmark):
        """Benchmark Lovelace amount conversions."""

        def convert_lovelace():
            amounts = [1000000, 2500000, 45000000, 1000000000]
            # Convert to ADA and back
            ada_amounts = [amount / 1_000_000 for amount in amounts]
            lovelace_amounts = [int(ada * 1_000_000) for ada in ada_amounts]
            return amounts, ada_amounts, lovelace_amounts

        result = benchmark(convert_lovelace)
        assert len(result) == 3
        assert result[0] == result[2]  # Original == converted back
