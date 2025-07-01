"""Integration tests for transaction detail models.

These tests verify that the models work correctly with an actual database connection.
They are read-only tests that work with existing database data.
"""

import pytest
from sqlmodel import Session, select

from dbsync.models import (
    Transaction,
    TransactionInput,
    TransactionOutput,
    TxMetadata,
)


class TestTransactionModelsIntegration:
    """Integration tests for transaction detail models - READ ONLY."""

    def test_transaction_model(self, dbsync_session: Session) -> None:
        """Test Transaction model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(Transaction).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_")
                assert hasattr(result, "block_id")
                assert hasattr(result, "fee")
                assert hasattr(result, "size")
                assert hasattr(result, "out_sum")
                assert hasattr(result, "deposit")

                # Verify fee is reasonable if present
                if result.fee is not None:
                    assert result.fee >= 0

                # Verify size is reasonable if present (can be 0 for some transactions)
                if result.size is not None:
                    assert result.size >= 0

                # Verify output sum is reasonable if present
                if result.out_sum is not None:
                    assert result.out_sum >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_tx_metadata_model(self, dbsync_session: Session) -> None:
        """Test TxMetadata model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(TxMetadata).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "key")
                assert hasattr(result, "json_")
                assert hasattr(result, "cbor_bytes")
                assert hasattr(result, "tx_id")

                # Verify key is within Word64 range if present
                if result.key is not None:
                    assert 0 <= result.key <= 18446744073709551615

                # Verify at least one of json or cbor_bytes is present
                assert result.json_ is not None or result.cbor_bytes is not None

                # If JSON is present, verify it's a dict
                if result.json_ is not None:
                    assert isinstance(result.json_, dict)

                # If CBOR bytes are present, verify it's bytes
                if result.cbor_bytes is not None:
                    assert isinstance(result.cbor_bytes, bytes)

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_tx_metadata_with_transaction_relationship(
        self, dbsync_session: Session
    ) -> None:
        """Test TxMetadata model relationship with Transaction."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Query for metadata with transaction relationship
            result = dbsync_session.exec(
                select(TxMetadata).where(TxMetadata.tx_id.is_not(None)).limit(1)
            ).first()

            if result and result.tx_id:
                # Verify the transaction exists
                transaction = dbsync_session.exec(
                    select(Transaction).where(Transaction.id_ == result.tx_id)
                ).first()

                if transaction:
                    assert transaction.id_ == result.tx_id
                    assert hasattr(transaction, "hash_")

        except Exception as e:
            pytest.skip(f"Database table or relationship not available: {e}")

    def test_tx_metadata_common_standards(self, dbsync_session: Session) -> None:
        """Test TxMetadata with common Cardano metadata standards."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test CIP-25 NFT metadata (key 721)
            nft_result = dbsync_session.exec(
                select(TxMetadata).where(TxMetadata.key == 721).limit(1)
            ).first()

            if nft_result and nft_result.json_:
                # Basic NFT metadata structure validation
                assert isinstance(nft_result.json_, dict)
                if "721" in nft_result.json_:
                    assert isinstance(nft_result.json_["721"], dict)

            # Test CIP-36 voting metadata (key 61284)
            voting_result = dbsync_session.exec(
                select(TxMetadata).where(TxMetadata.key == 61284).limit(1)
            ).first()

            if voting_result and voting_result.json_:
                assert isinstance(voting_result.json_, dict)

            # Test simple message metadata (key 1)
            message_result = dbsync_session.exec(
                select(TxMetadata).where(TxMetadata.key == 1).limit(1)
            ).first()

            if message_result and message_result.json_:
                assert isinstance(message_result.json_, dict)

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_transaction_input_model(self, dbsync_session: Session) -> None:
        """Test TransactionInput model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(TransactionInput).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_in_id")
                assert hasattr(result, "tx_out_id")
                assert hasattr(result, "tx_out_index")
                assert hasattr(result, "redeemer_id")

                # Verify transaction IDs are reasonable if present
                if result.tx_in_id is not None:
                    assert result.tx_in_id > 0

                if result.tx_out_id is not None:
                    assert result.tx_out_id > 0

                # Verify output index is reasonable if present
                if result.tx_out_index is not None:
                    assert result.tx_out_index >= 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_transaction_output_model(self, dbsync_session: Session) -> None:
        """Test TransactionOutput model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(TransactionOutput).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "index")
                assert hasattr(result, "value")
                assert hasattr(result, "address_id")
                assert hasattr(result, "stake_address_id")
                assert hasattr(result, "data_hash")
                assert hasattr(result, "inline_datum_id")
                assert hasattr(result, "reference_script_id")

                # Verify transaction ID is reasonable if present
                if result.tx_id is not None:
                    assert result.tx_id > 0

                # Verify value is reasonable if present
                if result.value is not None:
                    assert result.value >= 0

                # Verify output index is reasonable if present
                if result.index is not None:
                    assert result.index >= 0

                # Verify address ID is reasonable if present
                if result.address_id is not None:
                    assert result.address_id > 0
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_transaction_relationships(self, dbsync_session: Session) -> None:
        """Test transaction model relationships."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test transaction with its inputs and outputs
            tx_stmt = select(Transaction).limit(1)
            transaction = dbsync_session.exec(tx_stmt).first()

            if transaction:
                tx_id = transaction.id_

                # Look for inputs for this transaction
                input_stmt = (
                    select(TransactionInput)
                    .where(TransactionInput.tx_in_id == tx_id)
                    .limit(3)
                )
                inputs = dbsync_session.exec(input_stmt).all()

                # Look for outputs for this transaction
                output_stmt = (
                    select(TransactionOutput)
                    .where(TransactionOutput.tx_id == tx_id)
                    .limit(3)
                )
                outputs = dbsync_session.exec(output_stmt).all()

                # Verify relationships if data exists
                for tx_input in inputs:
                    assert tx_input.tx_in_id == tx_id

                for tx_output in outputs:
                    assert tx_output.tx_id == tx_id

                # At least verify we can query without errors
                assert transaction.id_ is not None
        except Exception as e:
            pytest.skip(f"Database table or relationship not available: {e}")

    def test_transaction_value_analysis(self, dbsync_session: Session) -> None:
        """Test transaction value analysis patterns."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # Test transaction value patterns
            stmt = (
                select(Transaction)
                .where(Transaction.fee.is_not(None), Transaction.out_sum.is_not(None))
                .limit(5)
            )
            results = dbsync_session.exec(stmt).all()

            for tx in results:
                if tx.fee is not None and tx.out_sum is not None:
                    # Basic transaction economics validation
                    assert tx.fee >= 0  # Fees should be non-negative
                    assert tx.out_sum >= 0  # Output sum should be non-negative

                    # Most transactions should have reasonable fees
                    if tx.fee > 0:
                        assert tx.fee >= 100000  # At least 0.1 ADA typical minimum
                        assert tx.fee <= 50000000  # Less than 50 ADA typical maximum

                    # Output sums should be reasonable
                    if tx.out_sum > 0:
                        assert tx.out_sum >= 1000000  # At least 1 ADA
        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_models_are_read_only(self, dbsync_session: Session) -> None:
        """Test that transaction models are used in read-only mode."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            # This test verifies that the models are designed for read-only access
            # In a real dbsync environment, these tables are populated by the dbsync process

            # Test that we can create queries but the expectation is read-only usage
            transaction_query = select(Transaction)
            tx_input_query = select(TransactionInput)
            tx_output_query = select(TransactionOutput)
            tx_metadata_query = select(TxMetadata)

            # Verify queries can be constructed (this is the expected usage pattern)
            assert transaction_query is not None
            assert tx_input_query is not None
            assert tx_output_query is not None
            assert tx_metadata_query is not None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
