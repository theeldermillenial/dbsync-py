"""Unit tests for SCHEMA-004: Transaction Details Models.

Tests for transaction inputs, outputs, scripts, redeemers, and other transaction detail models.
"""

from dbsync.models import (
    CollateralTransactionInput,
    CollateralTransactionOutput,
    Datum,
    ExtraKeyWitness,
    ReferenceTransactionInput,
    ScriptPurposeType,
    TransactionCbor,
    TransactionInput,
    TransactionOutput,
    TxMetadata,
    Withdrawal,
)
from dbsync.models.scripts import (
    Redeemer,
    RedeemerData,
    Script,
)


class TestTransactionInputModel:
    """Test TransactionInput model functionality."""

    def test_transaction_input_creation(self):
        """Test TransactionInput model instantiation."""
        tx_input = TransactionInput(
            tx_in_id=100,
            tx_out_id=999,
            tx_out_index=0,
            redeemer_id=5,
        )

        assert tx_input.tx_in_id == 100
        assert tx_input.tx_out_id == 999
        assert tx_input.tx_out_index == 0
        assert tx_input.redeemer_id == 5

    def test_transaction_input_table_name(self):
        """Test TransactionInput table name."""
        assert TransactionInput.__tablename__ == "tx_in"

    def test_transaction_input_relationships(self):
        """Test TransactionInput has required relationships."""
        tx_input = TransactionInput()
        assert hasattr(tx_input, "transaction")
        assert hasattr(tx_input, "transaction_output")
        assert hasattr(tx_input, "redeemer")

    def test_transaction_input_without_redeemer(self):
        """Test TransactionInput without redeemer (non-script input)."""
        tx_input = TransactionInput(
            tx_in_id=100,
            tx_out_id=999,
            tx_out_index=0,
        )
        assert tx_input.redeemer_id is None


class TestTransactionOutputModel:
    """Test TransactionOutput model functionality."""

    def test_transaction_output_creation(self):
        """Test TransactionOutput model instantiation."""
        tx_output = TransactionOutput(
            tx_id=100,
            index=0,
            address_id=42,
            stake_address_id=7,
            value=5000000,
            data_hash=b"\x04" * 32,
            inline_datum_id=12,
            reference_script_id=8,
        )

        assert tx_output.tx_id == 100
        assert tx_output.index == 0
        assert tx_output.address_id == 42
        assert tx_output.stake_address_id == 7
        assert tx_output.value == 5000000
        assert tx_output.data_hash == b"\x04" * 32
        assert tx_output.inline_datum_id == 12
        assert tx_output.reference_script_id == 8

    def test_transaction_output_table_name(self):
        """Test TransactionOutput table name."""
        assert TransactionOutput.__tablename__ == "tx_out"

    def test_transaction_output_relationships(self):
        """Test TransactionOutput has required relationships."""
        tx_output = TransactionOutput()
        assert hasattr(tx_output, "transaction")
        assert hasattr(tx_output, "inline_datum")
        assert hasattr(tx_output, "reference_script")

    def test_transaction_output_minimal(self):
        """Test TransactionOutput with minimal data."""
        tx_output = TransactionOutput(
            tx_id=100,
            index=0,
            value=1000000,
        )
        assert tx_output.tx_id == 100
        assert tx_output.index == 0
        assert tx_output.value == 1000000
        assert tx_output.address_id is None
        assert tx_output.data_hash is None


class TestCollateralTransactionInputModel:
    """Test CollateralTransactionInput model functionality."""

    def test_collateral_input_creation(self):
        """Test CollateralTransactionInput model instantiation."""
        collateral_input = CollateralTransactionInput(
            tx_in_id=100,
            tx_out_id=999,
            tx_out_index=1,
        )

        assert collateral_input.tx_in_id == 100
        assert collateral_input.tx_out_id == 999
        assert collateral_input.tx_out_index == 1

    def test_collateral_input_table_name(self):
        """Test CollateralTransactionInput table name."""
        assert CollateralTransactionInput.__tablename__ == "collateral_tx_in"

    def test_collateral_input_relationships(self):
        """Test CollateralTransactionInput has required relationships."""
        collateral_input = CollateralTransactionInput()
        assert hasattr(collateral_input, "transaction")
        assert hasattr(collateral_input, "transaction_output")


class TestReferenceTransactionInputModel:
    """Test ReferenceTransactionInput model functionality."""

    def test_reference_input_creation(self):
        """Test ReferenceTransactionInput model instantiation."""
        reference_input = ReferenceTransactionInput(
            tx_in_id=100,
            tx_out_id=999,
            tx_out_index=2,
        )

        assert reference_input.tx_in_id == 100
        assert reference_input.tx_out_id == 999
        assert reference_input.tx_out_index == 2

    def test_reference_input_table_name(self):
        """Test ReferenceTransactionInput table name."""
        assert ReferenceTransactionInput.__tablename__ == "reference_tx_in"

    def test_reference_input_relationships(self):
        """Test ReferenceTransactionInput has required relationships."""
        reference_input = ReferenceTransactionInput()
        assert hasattr(reference_input, "transaction")
        assert hasattr(reference_input, "transaction_output")


class TestCollateralTransactionOutputModel:
    """Test CollateralTransactionOutput model functionality."""

    def test_collateral_output_creation(self):
        """Test CollateralTransactionOutput model instantiation."""
        collateral_output = CollateralTransactionOutput(
            tx_id=100,
            index=0,
            address_id=42,
            value=2000000,
        )

        assert collateral_output.tx_id == 100
        assert collateral_output.index == 0
        assert collateral_output.address_id == 42
        assert collateral_output.value == 2000000

    def test_collateral_output_table_name(self):
        """Test CollateralTransactionOutput table name."""
        assert CollateralTransactionOutput.__tablename__ == "collateral_tx_out"

    def test_collateral_output_relationships(self):
        """Test CollateralTransactionOutput has required relationships."""
        collateral_output = CollateralTransactionOutput()
        assert hasattr(collateral_output, "transaction")
        assert hasattr(collateral_output, "inline_datum")
        assert hasattr(collateral_output, "reference_script")


class TestTransactionCborModel:
    """Test TransactionCbor model functionality."""

    def test_transaction_cbor_creation(self):
        """Test TransactionCbor model instantiation."""
        cbor_data = b"\x84\xa4\x00\x81\x82\x58\x20"  # Sample CBOR bytes
        tx_cbor = TransactionCbor(
            tx_id=100,
            cbor_bytes=cbor_data,
        )

        assert tx_cbor.tx_id == 100
        assert tx_cbor.cbor_bytes == cbor_data

    def test_transaction_cbor_table_name(self):
        """Test TransactionCbor table name."""
        assert TransactionCbor.__tablename__ == "tx_cbor"

    def test_transaction_cbor_relationships(self):
        """Test TransactionCbor has required relationships."""
        tx_cbor = TransactionCbor()
        assert hasattr(tx_cbor, "transaction")


class TestDatumModel:
    """Test Datum model functionality."""

    def test_datum_creation(self):
        """Test Datum model instantiation."""
        datum_hash = b"\x05" * 32
        datum_value = {"constructor": 0, "fields": [{"int": 42}]}
        cbor_bytes = b"\x80\x42"

        datum = Datum(
            hash_=datum_hash,
            tx_id=100,
            value=datum_value,
            cbor_bytes=cbor_bytes,
        )

        assert datum.hash_ == datum_hash
        assert datum.tx_id == 100
        assert datum.value == datum_value
        assert datum.cbor_bytes == cbor_bytes

    def test_datum_table_name(self):
        """Test Datum table name."""
        assert Datum.__tablename__ == "datum"

    def test_datum_relationships(self):
        """Test Datum has required relationships."""
        datum = Datum()
        assert hasattr(datum, "transaction")

    def test_datum_json_value(self):
        """Test Datum with complex JSON value."""
        complex_value = {
            "constructor": 1,
            "fields": [
                {"bytes": "deadbeef"},
                {"list": [{"int": 1}, {"int": 2}]},
                {"map": [{"k": {"bytes": "key"}, "v": {"int": 100}}]},
            ],
        }
        datum = Datum(value=complex_value)
        assert datum.value == complex_value


class TestRedeemerDataModel:
    """Test RedeemerData model functionality."""

    def test_redeemer_data_creation(self):
        """Test RedeemerData model instantiation."""
        redeemer_hash = b"\x06" * 32
        redeemer_value = {"constructor": 0, "fields": []}
        data_bytes = b"\x80"

        redeemer_data = RedeemerData(
            hash_=redeemer_hash,
            tx_id=100,
            value=redeemer_value,
            bytes_=data_bytes,
        )

        assert redeemer_data.hash_ == redeemer_hash
        assert redeemer_data.tx_id == 100
        assert redeemer_data.value == redeemer_value
        assert redeemer_data.bytes_ == data_bytes

    def test_redeemer_data_table_name(self):
        """Test RedeemerData table name."""
        assert RedeemerData.__tablename__ == "redeemer_data"

    def test_redeemer_data_relationships(self):
        """Test RedeemerData has required relationships."""
        redeemer_data = RedeemerData()
        assert hasattr(redeemer_data, "transaction")


class TestRedeemerModel:
    """Test Redeemer model functionality."""

    def test_redeemer_creation(self):
        """Test Redeemer model instantiation."""
        script_hash = b"\x07" * 28

        redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            fee=100000,
            purpose=ScriptPurposeType.SPEND,
            index=0,
            script_hash=script_hash,
            redeemer_data_id=42,
        )

        assert redeemer.tx_id == 100
        assert redeemer.unit_mem == 1000000
        assert redeemer.unit_steps == 500000000
        assert redeemer.fee == 100000
        assert redeemer.purpose == ScriptPurposeType.SPEND
        assert redeemer.index == 0
        assert redeemer.script_hash == script_hash
        assert redeemer.redeemer_data_id == 42

    def test_redeemer_table_name(self):
        """Test Redeemer table name."""
        assert Redeemer.__tablename__ == "redeemer"

    def test_redeemer_relationships(self):
        """Test Redeemer has required relationships."""
        redeemer = Redeemer()
        assert hasattr(redeemer, "transaction")
        assert hasattr(redeemer, "redeemer_data")

    def test_script_purpose_types(self):
        """Test ScriptPurposeType enum values."""
        assert ScriptPurposeType.SPEND == "spend"
        assert ScriptPurposeType.MINT == "mint"
        assert ScriptPurposeType.CERT == "cert"
        assert ScriptPurposeType.REWARD == "reward"
        assert ScriptPurposeType.VOTING == "voting"
        assert ScriptPurposeType.PROPOSING == "proposing"


class TestExtraKeyWitnessModel:
    """Test ExtraKeyWitness model functionality."""

    def test_extra_key_witness_creation(self):
        """Test ExtraKeyWitness model instantiation."""
        witness_hash = b"\x08" * 28

        extra_witness = ExtraKeyWitness(
            hash_=witness_hash,
            tx_id=100,
        )

        assert extra_witness.hash_ == witness_hash
        assert extra_witness.tx_id == 100

    def test_extra_key_witness_table_name(self):
        """Test ExtraKeyWitness table name."""
        assert ExtraKeyWitness.__tablename__ == "extra_key_witness"

    def test_extra_key_witness_relationships(self):
        """Test ExtraKeyWitness has required relationships."""
        extra_witness = ExtraKeyWitness()
        assert hasattr(extra_witness, "transaction")


class TestWithdrawalModel:
    """Test Withdrawal model functionality."""

    def test_withdrawal_creation(self):
        """Test Withdrawal model instantiation."""
        withdrawal = Withdrawal(
            addr_id=50,
            amount=10000000,
            redeemer_id=3,
            tx_id=100,
        )

        assert withdrawal.addr_id == 50
        assert withdrawal.amount == 10000000
        assert withdrawal.redeemer_id == 3
        assert withdrawal.tx_id == 100

    def test_withdrawal_table_name(self):
        """Test Withdrawal table name."""
        assert Withdrawal.__tablename__ == "withdrawal"

    def test_withdrawal_relationships(self):
        """Test Withdrawal has required relationships."""
        withdrawal = Withdrawal()
        assert hasattr(withdrawal, "transaction")
        assert hasattr(withdrawal, "redeemer")

    def test_withdrawal_without_redeemer(self):
        """Test Withdrawal without redeemer (non-script withdrawal)."""
        withdrawal = Withdrawal(
            addr_id=50,
            amount=10000000,
            tx_id=100,
        )
        assert withdrawal.redeemer_id is None


class TestTxMetadataModel:
    """Test TxMetadata model functionality."""

    def test_tx_metadata_creation(self):
        """Test TxMetadata model instantiation."""
        metadata_json = {
            "721": {
                "version": "1.0",
                "copyright": "Example NFT",
                "publisher": ["Test", "Publisher"],
                "website": "https://example.com",
            }
        }
        metadata_cbor = b"\xa1\x19\x02\xd1\xa4\x67version\x63\x31\x2e\x30"

        tx_metadata = TxMetadata(
            key=721,
            json_=metadata_json,
            cbor_bytes=metadata_cbor,
            tx_id=100,
        )

        assert tx_metadata.key == 721
        assert tx_metadata.json_ == metadata_json
        assert tx_metadata.cbor_bytes == metadata_cbor
        assert tx_metadata.tx_id == 100

    def test_tx_metadata_table_name(self):
        """Test TxMetadata table name."""
        assert TxMetadata.__tablename__ == "tx_metadata"

    def test_tx_metadata_relationships(self):
        """Test TxMetadata has required relationships."""
        tx_metadata = TxMetadata()
        assert hasattr(tx_metadata, "transaction")

    def test_tx_metadata_json_only(self):
        """Test TxMetadata with only JSON data (no CBOR)."""
        metadata_json = {"msg": ["Hello", "World"], "number": 42}

        tx_metadata = TxMetadata(
            key=1,
            json_=metadata_json,
            tx_id=100,
        )

        assert tx_metadata.key == 1
        assert tx_metadata.json_ == metadata_json
        assert tx_metadata.cbor_bytes is None
        assert tx_metadata.tx_id == 100

    def test_tx_metadata_cbor_only(self):
        """Test TxMetadata with only CBOR data (no JSON)."""
        # Raw CBOR that might not decode to valid JSON
        metadata_cbor = b"\x58\x20\x01\x02\x03\x04\x05\x06\x07\x08"

        tx_metadata = TxMetadata(
            key=999,
            cbor_bytes=metadata_cbor,
            tx_id=100,
        )

        assert tx_metadata.key == 999
        assert tx_metadata.json_ is None
        assert tx_metadata.cbor_bytes == metadata_cbor
        assert tx_metadata.tx_id == 100

    def test_tx_metadata_large_key(self):
        """Test TxMetadata with large Word64 key."""
        large_key = 18446744073709551615  # Max Word64 value

        tx_metadata = TxMetadata(
            key=large_key,
            json_={"test": "large_key"},
            tx_id=100,
        )

        assert tx_metadata.key == large_key

    def test_tx_metadata_zero_key(self):
        """Test TxMetadata with zero key."""
        tx_metadata = TxMetadata(
            key=0,
            json_={"test": "zero_key"},
            tx_id=100,
        )

        assert tx_metadata.key == 0

    def test_tx_metadata_nft_standard(self):
        """Test TxMetadata with CIP-25 NFT metadata standard."""
        nft_metadata = {
            "721": {
                "policy_id_123": {
                    "asset_name_456": {
                        "name": "My NFT",
                        "image": "ipfs://QmHash123",
                        "mediaType": "image/png",
                        "description": "A test NFT",
                        "attributes": [
                            {"trait_type": "Color", "value": "Blue"},
                            {"trait_type": "Rarity", "value": "Common"},
                        ],
                    }
                }
            }
        }

        tx_metadata = TxMetadata(
            key=721,
            json_=nft_metadata,
            tx_id=100,
        )

        assert tx_metadata.key == 721
        assert tx_metadata.json_ == nft_metadata
        assert "721" in tx_metadata.json_
        assert "policy_id_123" in tx_metadata.json_["721"]

    def test_tx_metadata_voting_standard(self):
        """Test TxMetadata with CIP-36 voting metadata standard."""
        voting_metadata = {
            "61284": {
                "vote_plan_id": "0x123abc",
                "proposal_index": 1,
                "vote_payload": "0x01",
            }
        }

        tx_metadata = TxMetadata(
            key=61284,
            json_=voting_metadata,
            tx_id=100,
        )

        assert tx_metadata.key == 61284
        assert tx_metadata.json_ == voting_metadata
        assert "61284" in tx_metadata.json_

    def test_tx_metadata_empty_json(self):
        """Test TxMetadata with empty JSON object."""
        tx_metadata = TxMetadata(
            key=1,
            json_={},
            tx_id=100,
        )

        assert tx_metadata.key == 1
        assert tx_metadata.json_ == {}

    def test_tx_metadata_complex_json(self):
        """Test TxMetadata with complex nested JSON structure."""
        complex_json = {
            "array": [1, 2, 3, "string", {"nested": "object"}],
            "object": {"boolean": True, "null": None, "number": 42.5, "string": "test"},
            "unicode": "🚀 Cardano metadata with emojis! 🎉",
        }

        tx_metadata = TxMetadata(
            key=12345,
            json_=complex_json,
            tx_id=100,
        )

        assert tx_metadata.key == 12345
        assert tx_metadata.json_ == complex_json
        assert tx_metadata.json_["unicode"] == "🚀 Cardano metadata with emojis! 🎉"


class TestScriptModel:
    """Test Script model functionality."""

    def test_script_creation(self):
        """Test Script model instantiation."""
        script_hash = b"\x09" * 28
        script_json = {"type": "sig", "keyHash": "abc123"}
        cbor_bytes = b"\x82\x00\x58\x1c"

        script = Script(
            tx_id=100,
            hash_=script_hash,
            type_="plutusV2",
            json_=script_json,
            bytes_=cbor_bytes,
            serialised_size=1024,
        )

        assert script.tx_id == 100
        assert script.hash_ == script_hash
        assert script.type_ == "plutusV2"
        assert script.json_ == script_json
        assert script.bytes_ == cbor_bytes
        assert script.serialised_size == 1024

    def test_script_table_name(self):
        """Test Script table name."""
        assert Script.__tablename__ == "script"

    def test_script_relationships(self):
        """Test Script has required relationships."""
        script = Script()
        assert hasattr(script, "transaction")

    def test_native_script_json(self):
        """Test Script with native script JSON."""
        native_script = {
            "type": "all",
            "scripts": [
                {"type": "sig", "keyHash": "abc123"},
                {"type": "after", "slot": 12345},
            ],
        }
        script = Script(type_="native", json_=native_script)
        assert script.json_ == native_script

    def test_plutus_script_cbor(self):
        """Test Script with Plutus script CBOR."""
        plutus_cbor = b"\x59\x05\xf4\x01\x00\x00\x32\x32"  # Sample Plutus CBOR
        script = Script(type_="plutusV2", bytes_=plutus_cbor)
        assert script.bytes_ == plutus_cbor


class TestTransactionModelTypes:
    """Test SCHEMA-004 model type annotations and inheritance."""

    def test_all_models_have_primary_keys(self):
        """Test all transaction models have primary key fields."""
        models = [
            TransactionInput,
            TransactionOutput,
            CollateralTransactionInput,
            ReferenceTransactionInput,
            CollateralTransactionOutput,
            TransactionCbor,
            Datum,
            RedeemerData,
            Redeemer,
            ExtraKeyWitness,
            Withdrawal,
            TxMetadata,
            Script,
        ]

        for model in models:
            instance = model()
            assert hasattr(instance, "id_")
            assert instance.id_ is None  # Should be None for new instances

    def test_model_inheritance(self):
        """Test transaction models inherit from DBSyncBase."""
        from dbsync.models.base import DBSyncBase

        models = [
            TransactionInput,
            TransactionOutput,
            CollateralTransactionInput,
            ReferenceTransactionInput,
            CollateralTransactionOutput,
            TransactionCbor,
            Datum,
            RedeemerData,
            Redeemer,
            ExtraKeyWitness,
            Withdrawal,
            TxMetadata,
            Script,
        ]

        for model in models:
            assert issubclass(model, DBSyncBase)

    def test_model_table_definitions(self):
        """Test all models have table definitions."""
        models_and_tables = [
            (TransactionInput, "tx_in"),
            (TransactionOutput, "tx_out"),
            (CollateralTransactionInput, "collateral_tx_in"),
            (ReferenceTransactionInput, "reference_tx_in"),
            (CollateralTransactionOutput, "collateral_tx_out"),
            (TransactionCbor, "tx_cbor"),
            (Datum, "datum"),
            (RedeemerData, "redeemer_data"),
            (Redeemer, "redeemer"),
            (ExtraKeyWitness, "extra_key_witness"),
            (Withdrawal, "withdrawal"),
            (TxMetadata, "tx_metadata"),
            (Script, "script"),
        ]

        for model, expected_table_name in models_and_tables:
            assert hasattr(model, "__tablename__")
            assert model.__tablename__ == expected_table_name


class TestTransactionModelIntegration:
    """Integration tests for SCHEMA-004 transaction models."""

    def test_transaction_input_output_relationship(self):
        """Test TransactionInput-TransactionOutput relationship structure."""
        tx_input = TransactionInput(tx_out_id=999, tx_out_index=0)
        tx_output = TransactionOutput(index=0, value=5000000)

        # Test that relationship attributes exist
        assert hasattr(tx_input, "transaction_output")
        assert hasattr(tx_output, "transaction")

    def test_redeemer_data_relationship(self):
        """Test Redeemer-RedeemerData relationship structure."""
        redeemer = Redeemer(redeemer_data_id=42)
        redeemer_data = RedeemerData(hash=b"\x01" * 32)

        # Test that relationship attributes exist
        assert hasattr(redeemer, "redeemer_data")
        assert hasattr(redeemer_data, "transaction")

    def test_datum_output_relationship(self):
        """Test Datum-TransactionOutput relationship structure."""
        datum = Datum(hash=b"\x02" * 32)
        tx_output = TransactionOutput(inline_datum_id=12)

        # Test that relationship attributes exist
        assert hasattr(tx_output, "inline_datum")
        assert hasattr(datum, "transaction")

    def test_script_output_relationship(self):
        """Test Script-TransactionOutput relationship structure."""
        script = Script(hash=b"\x03" * 28)
        tx_output = TransactionOutput(reference_script_id=8)

        # Test that relationship attributes exist
        assert hasattr(tx_output, "reference_script")
        assert hasattr(script, "transaction")

    def test_withdrawal_redeemer_relationship(self):
        """Test Withdrawal-Redeemer relationship structure."""
        withdrawal = Withdrawal(redeemer_id=5, amount=1000000)
        redeemer = Redeemer(purpose=ScriptPurposeType.REWARD)

        # Test that relationship attributes exist
        assert hasattr(withdrawal, "redeemer")
        assert hasattr(redeemer, "transaction")


class TestTransactionModelEdgeCases:
    """Test edge cases and validation for SCHEMA-004 models."""

    def test_zero_value_output(self):
        """Test TransactionOutput with zero value."""
        tx_output = TransactionOutput(value=0)
        assert tx_output.value == 0

    def test_large_script_execution_units(self):
        """Test Redeemer with large execution units."""
        redeemer = Redeemer(
            unit_mem=14000000,  # Max memory units
            unit_steps=10000000000,  # Max step units
        )
        assert redeemer.unit_mem == 14000000
        assert redeemer.unit_steps == 10000000000

    def test_empty_datum_value(self):
        """Test Datum with empty JSON value."""
        datum = Datum(value={})
        assert datum.value == {}

    def test_large_cbor_data(self):
        """Test models with large CBOR data."""
        large_cbor = b"\x00" * 16384  # 16KB CBOR data
        tx_cbor = TransactionCbor(cbor_bytes=large_cbor)
        assert len(tx_cbor.cbor_bytes) == 16384

    def test_model_string_representations(self):
        """Test model string representations work."""
        models_with_data = [
            TransactionInput(tx_in_id=1, tx_out_id=999),
            TransactionOutput(tx_id=1, value=5000000),
            CollateralTransactionInput(tx_in_id=1),
            ReferenceTransactionInput(tx_in_id=1),
            CollateralTransactionOutput(tx_id=1, value=2000000),
            TransactionCbor(tx_id=1, cbor_bytes=b"\x80"),
            Datum(hash=b"\x01" * 32, value={}),
            RedeemerData(hash=b"\x02" * 32, value={}),
            Redeemer(tx_id=1, purpose=ScriptPurposeType.SPEND),
            ExtraKeyWitness(hash=b"\x03" * 28, tx_id=1),
            Withdrawal(addr_id=1, amount=1000000, tx_id=1),
            Script(hash=b"\x04" * 28, type="plutusV2"),
        ]

        for model_instance in models_with_data:
            repr_str = repr(model_instance)
            assert isinstance(repr_str, str)
            assert len(repr_str) > 0
            # Should include class name
            assert model_instance.__class__.__name__ in repr_str


# Summary: SCHEMA-004 (Transaction Details Models) - 12 models, comprehensive coverage
# TransactionInput, TransactionOutput, CollateralTransactionInput, ReferenceTransactionInput,
# CollateralTransactionOutput, TransactionCbor, Datum, RedeemerData, Redeemer,
# ExtraKeyWitness, Withdrawal, Script
