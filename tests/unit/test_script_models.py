"""Unit tests for script and smart contract models.

Tests SCHEMA-008: Script and Smart Contract Models including:
- Script model (native and Plutus scripts)
- RedeemerData model (script execution parameters)
- Redeemer model (script execution context)
- CostModel model (Plutus execution costs)
"""

from dbsync.models.scripts import (
    CostModel,
    PlutusVersion,
    Redeemer,
    RedeemerData,
    RedeemerTag,
    Script,
    ScriptType,
)


class TestScriptType:
    """Test ScriptType enumeration."""

    def test_script_type_values(self):
        """Test ScriptType enum values."""
        assert ScriptType.NATIVE == "native"
        assert ScriptType.PLUTUS_V1 == "plutusV1"
        assert ScriptType.PLUTUS_V2 == "plutusV2"
        assert ScriptType.PLUTUS_V3 == "plutusV3"

    def test_script_type_membership(self):
        """Test ScriptType membership."""
        assert "native" in ScriptType
        assert "plutusV1" in ScriptType
        assert "plutusV2" in ScriptType
        assert "plutusV3" in ScriptType
        assert "invalid" not in ScriptType


class TestPlutusVersion:
    """Test PlutusVersion enumeration."""

    def test_plutus_version_values(self):
        """Test PlutusVersion enum values."""
        assert PlutusVersion.V1 == "PlutusV1"
        assert PlutusVersion.V2 == "PlutusV2"
        assert PlutusVersion.V3 == "PlutusV3"

    def test_plutus_version_membership(self):
        """Test PlutusVersion membership."""
        assert "PlutusV1" in PlutusVersion
        assert "PlutusV2" in PlutusVersion
        assert "PlutusV3" in PlutusVersion
        assert "PlutusV4" not in PlutusVersion


class TestRedeemerTag:
    """Test RedeemerTag enumeration."""

    def test_redeemer_tag_values(self):
        """Test RedeemerTag enum values."""
        assert RedeemerTag.SPEND == "spend"
        assert RedeemerTag.MINT == "mint"
        assert RedeemerTag.CERT == "cert"
        assert RedeemerTag.REWARD == "reward"
        assert RedeemerTag.VOTE == "vote"
        assert RedeemerTag.PROPOSE == "propose"

    def test_redeemer_tag_membership(self):
        """Test RedeemerTag membership."""
        assert "spend" in RedeemerTag
        assert "mint" in RedeemerTag
        assert "cert" in RedeemerTag
        assert "reward" in RedeemerTag
        assert "vote" in RedeemerTag
        assert "propose" in RedeemerTag
        assert "invalid" not in RedeemerTag


class TestScript:
    """Test Script model."""

    def test_script_creation(self):
        """Test Script model creation."""
        script_hash = bytes.fromhex("a" * 56)  # 28 bytes
        script = Script(
            id_=1,
            tx_id=100,
            hash_=script_hash,
            type_=ScriptType.NATIVE,
            json_={"type": "sig", "keyHash": "abc123"},
            serialised_size=42,
        )

        assert script.id_ == 1
        assert script.tx_id == 100
        assert script.hash_ == script_hash
        assert script.type_ == ScriptType.NATIVE
        assert script.json_ == {"type": "sig", "keyHash": "abc123"}
        assert script.serialised_size == 42

    def test_script_hash_hex_property(self):
        """Test Script hash_hex property."""
        script_hash = bytes.fromhex("abcdef123456")
        script = Script(tx_id=100, hash_=script_hash, type_=ScriptType.NATIVE)

        assert script.hash_hex == "abcdef123456"

    def test_script_hash_hex_empty(self):
        """Test Script hash_hex property with empty hash."""
        script = Script(tx_id=100, hash_=b"", type_=ScriptType.NATIVE)

        assert script.hash_hex == ""

    def test_script_is_native_property(self):
        """Test Script is_native property."""
        native_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.NATIVE)
        plutus_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V1)

        assert native_script.is_native is True
        assert plutus_script.is_native is False

    def test_script_is_plutus_property(self):
        """Test Script is_plutus property."""
        native_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.NATIVE)
        plutus_v1_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V1)
        plutus_v2_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V2)
        plutus_v3_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V3)

        assert native_script.is_plutus is False
        assert plutus_v1_script.is_plutus is True
        assert plutus_v2_script.is_plutus is True
        assert plutus_v3_script.is_plutus is True

    def test_script_plutus_version_property(self):
        """Test Script plutus_version property."""
        native_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.NATIVE)
        plutus_v1_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V1)
        plutus_v2_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V2)
        plutus_v3_script = Script(tx_id=100, hash_=b"test", type_=ScriptType.PLUTUS_V3)

        assert native_script.plutus_version is None
        assert plutus_v1_script.plutus_version == PlutusVersion.V1
        assert plutus_v2_script.plutus_version == PlutusVersion.V2
        assert plutus_v3_script.plutus_version == PlutusVersion.V3


class TestRedeemerData:
    """Test RedeemerData model."""

    def test_redeemer_data_creation(self):
        """Test RedeemerData model creation."""
        data_hash = bytes.fromhex("a" * 64)  # 32 bytes
        data_bytes = b"test redeemer data"
        redeemer_data = RedeemerData(
            id_=1,
            hash_=data_hash,
            tx_id=100,
            value={"constructor": 0, "fields": []},
            bytes_=data_bytes,
        )

        assert redeemer_data.id_ == 1
        assert redeemer_data.hash_ == data_hash
        assert redeemer_data.tx_id == 100
        assert redeemer_data.value == {"constructor": 0, "fields": []}
        assert redeemer_data.bytes_ == data_bytes

    def test_redeemer_data_hash_hex_property(self):
        """Test RedeemerData hash_hex property."""
        data_hash = bytes.fromhex("123456abcdef")
        redeemer_data = RedeemerData(hash_=data_hash, tx_id=100, bytes_=b"test")

        assert redeemer_data.hash_hex == "123456abcdef"

    def test_redeemer_data_size_bytes_property(self):
        """Test RedeemerData size_bytes property."""
        data_bytes = b"test data"
        redeemer_data = RedeemerData(hash_=b"test", tx_id=100, bytes_=data_bytes)

        assert redeemer_data.size_bytes == len(data_bytes)

    def test_redeemer_data_size_bytes_none(self):
        """Test RedeemerData size_bytes property with None bytes."""
        redeemer_data = RedeemerData(hash_=b"test", tx_id=100, bytes_=None)

        assert redeemer_data.size_bytes == 0


class TestRedeemer:
    """Test Redeemer model."""

    def test_redeemer_creation(self):
        """Test Redeemer model creation."""
        script_hash = bytes.fromhex("a" * 56)  # 28 bytes
        redeemer = Redeemer(
            id_=1,
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            fee=150000,
            purpose=RedeemerTag.SPEND,
            index=0,
            script_hash=script_hash,
            redeemer_data_id=42,
        )

        assert redeemer.id_ == 1
        assert redeemer.tx_id == 100
        assert redeemer.unit_mem == 1000000
        assert redeemer.unit_steps == 500000000
        assert redeemer.fee == 150000
        assert redeemer.purpose == RedeemerTag.SPEND
        assert redeemer.index == 0
        assert redeemer.script_hash == script_hash
        assert redeemer.redeemer_data_id == 42

    def test_redeemer_total_execution_units_property(self):
        """Test Redeemer total_execution_units property."""
        redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.SPEND,
            index=0,
        )

        assert redeemer.total_execution_units == 501000000

    def test_redeemer_execution_cost_ratio_property(self):
        """Test Redeemer execution_cost_ratio property."""
        redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.SPEND,
            index=0,
        )

        assert redeemer.execution_cost_ratio == 1000000 / 500000000

    def test_redeemer_execution_cost_ratio_zero_steps(self):
        """Test Redeemer execution_cost_ratio property with zero steps."""
        redeemer_with_mem = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=0,
            purpose=RedeemerTag.SPEND,
            index=0,
        )
        redeemer_no_mem = Redeemer(
            tx_id=100, unit_mem=0, unit_steps=0, purpose=RedeemerTag.SPEND, index=0
        )

        assert redeemer_with_mem.execution_cost_ratio == float("inf")
        assert redeemer_no_mem.execution_cost_ratio == 0.0

    def test_redeemer_script_hash_hex_property(self):
        """Test Redeemer script_hash_hex property."""
        script_hash = bytes.fromhex("abcdef123456")
        redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.SPEND,
            index=0,
            script_hash=script_hash,
        )

        assert redeemer.script_hash_hex == "abcdef123456"

    def test_redeemer_script_hash_hex_none(self):
        """Test Redeemer script_hash_hex property with None hash."""
        redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.SPEND,
            index=0,
            script_hash=None,
        )

        assert redeemer.script_hash_hex == ""

    def test_redeemer_purpose_properties(self):
        """Test Redeemer purpose-specific properties."""
        spend_redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.SPEND,
            index=0,
        )
        mint_redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.MINT,
            index=0,
        )
        cert_redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.CERT,
            index=0,
        )
        reward_redeemer = Redeemer(
            tx_id=100,
            unit_mem=1000000,
            unit_steps=500000000,
            purpose=RedeemerTag.REWARD,
            index=0,
        )

        # Test spending redeemer
        assert spend_redeemer.is_spending_redeemer is True
        assert spend_redeemer.is_minting_redeemer is False
        assert spend_redeemer.is_certificate_redeemer is False
        assert spend_redeemer.is_reward_redeemer is False

        # Test minting redeemer
        assert mint_redeemer.is_spending_redeemer is False
        assert mint_redeemer.is_minting_redeemer is True
        assert mint_redeemer.is_certificate_redeemer is False
        assert mint_redeemer.is_reward_redeemer is False

        # Test certificate redeemer
        assert cert_redeemer.is_spending_redeemer is False
        assert cert_redeemer.is_minting_redeemer is False
        assert cert_redeemer.is_certificate_redeemer is True
        assert cert_redeemer.is_reward_redeemer is False

        # Test reward redeemer
        assert reward_redeemer.is_spending_redeemer is False
        assert reward_redeemer.is_minting_redeemer is False
        assert reward_redeemer.is_certificate_redeemer is False
        assert reward_redeemer.is_reward_redeemer is True


class TestCostModel:
    """Test CostModel model."""

    def test_cost_model_creation(self):
        """Test CostModel model creation."""
        cost_hash = bytes.fromhex("a" * 64)  # 32 bytes
        costs = {
            "addInteger-cpu-arguments-intercept": 197209,
            "addInteger-cpu-arguments-slope": 0,
            "addInteger-memory-arguments-intercept": 1,
            "addInteger-memory-arguments-slope": 1,
            "appendByteString-cpu-arguments-intercept": 396231,
            "appendByteString-cpu-arguments-slope": 621,
        }
        cost_model = CostModel(id_=1, hash_=cost_hash, costs=costs)

        assert cost_model.id_ == 1
        assert cost_model.hash_ == cost_hash
        assert cost_model.costs == costs

    def test_cost_model_hash_hex_property(self):
        """Test CostModel hash_hex property."""
        cost_hash = bytes.fromhex("abcdef123456")
        cost_model = CostModel(hash_=cost_hash, costs={})

        assert cost_model.hash_hex == "abcdef123456"

    def test_cost_model_hash_hex_empty(self):
        """Test CostModel hash_hex property with empty hash."""
        cost_model = CostModel(hash_=b"", costs={})

        assert cost_model.hash_hex == ""

    def test_cost_model_operation_count_property(self):
        """Test CostModel operation_count property."""
        costs = {"op1": 100, "op2": 200, "op3": 300}
        cost_model = CostModel(hash_=b"test", costs=costs)

        assert cost_model.operation_count == 3

    def test_cost_model_operation_count_empty(self):
        """Test CostModel operation_count property with empty costs."""
        cost_model = CostModel(hash_=b"test", costs={})

        assert cost_model.operation_count == 0

    def test_cost_model_operation_count_zero(self):
        """Test CostModel operation_count property with valid empty costs."""
        cost_model = CostModel(hash_=b"test", costs={})

        assert cost_model.operation_count == 0

    def test_cost_model_is_valid_property(self):
        """Test CostModel is_valid property."""
        valid_cost_model = CostModel(hash_=b"test", costs={"op1": 100})
        empty_cost_model = CostModel(hash_=b"test", costs={})

        assert valid_cost_model.is_valid is True
        assert empty_cost_model.is_valid is False

    def test_cost_model_get_operation_cost(self):
        """Test CostModel get_operation_cost method."""
        costs = {
            "addInteger-cpu-arguments-intercept": 197209,
            "appendByteString-memory-arguments-slope": 1,
        }
        cost_model = CostModel(hash_=b"test", costs=costs)

        assert (
            cost_model.get_operation_cost("addInteger-cpu-arguments-intercept")
            == 197209
        )
        assert (
            cost_model.get_operation_cost("appendByteString-memory-arguments-slope")
            == 1
        )
        assert cost_model.get_operation_cost("nonexistent-operation") is None

    def test_cost_model_get_operation_cost_empty_costs(self):
        """Test CostModel get_operation_cost method with empty costs."""
        cost_model = CostModel(hash_=b"test", costs={})

        assert cost_model.get_operation_cost("any-operation") is None

    def test_cost_model_has_operation(self):
        """Test CostModel has_operation method."""
        costs = {
            "addInteger-cpu-arguments-intercept": 197209,
            "appendByteString-memory-arguments-slope": 1,
        }
        cost_model = CostModel(hash_=b"test", costs=costs)

        assert cost_model.has_operation("addInteger-cpu-arguments-intercept") is True
        assert (
            cost_model.has_operation("appendByteString-memory-arguments-slope") is True
        )
        assert cost_model.has_operation("nonexistent-operation") is False

    def test_cost_model_has_operation_empty_costs(self):
        """Test CostModel has_operation method with empty costs."""
        cost_model = CostModel(hash_=b"test", costs={})

        assert cost_model.has_operation("any-operation") is False

    def test_cost_model_real_plutus_costs(self):
        """Test CostModel with realistic Plutus cost model data."""
        # Sample cost model based on actual Cardano parameters
        costs = {
            "addInteger-cpu-arguments-intercept": 197209,
            "addInteger-cpu-arguments-slope": 0,
            "addInteger-memory-arguments-intercept": 1,
            "addInteger-memory-arguments-slope": 1,
            "appendByteString-cpu-arguments-intercept": 396231,
            "appendByteString-cpu-arguments-slope": 621,
            "appendByteString-memory-arguments-intercept": 0,
            "appendByteString-memory-arguments-slope": 1,
            "appendString-cpu-arguments-intercept": 150000,
            "appendString-cpu-arguments-slope": 1000,
            "appendString-memory-arguments-intercept": 0,
            "appendString-memory-arguments-slope": 1,
            "bData-cpu-arguments": 150000,
            "bData-memory-arguments": 32,
        }
        cost_hash = bytes.fromhex("f" * 64)  # 32 bytes
        cost_model = CostModel(id_=42, hash_=cost_hash, costs=costs)

        # Test basic properties
        assert cost_model.id_ == 42
        assert cost_model.hash_hex == "f" * 64
        assert cost_model.operation_count == 14
        assert cost_model.is_valid is True

        # Test specific operation access
        assert (
            cost_model.get_operation_cost("addInteger-cpu-arguments-intercept")
            == 197209
        )
        assert cost_model.get_operation_cost("bData-memory-arguments") == 32
        assert cost_model.has_operation("appendString-cpu-arguments-intercept") is True
        assert cost_model.has_operation("nonexistent-operation") is False


class TestScriptModelIntegration:
    """Test integration between script models."""

    def test_script_lifecycle_simulation(self):
        """Test complete script lifecycle simulation."""
        # Create a Plutus script
        script_hash = bytes.fromhex("a" * 56)  # 28 bytes
        script = Script(
            id_=1,
            tx_id=100,
            hash_=script_hash,
            type_=ScriptType.PLUTUS_V2,
            bytes_=b"plutus script bytecode",
            serialised_size=1024,
        )

        # Note: PlutusScript model removed - all script info is in Script model

        # Create redeemer data
        redeemer_data_hash = bytes.fromhex("b" * 64)  # 32 bytes
        redeemer_data = RedeemerData(
            id_=1,
            hash_=redeemer_data_hash,
            tx_id=101,
            value={"constructor": 0, "fields": [{"int": 42}]},
            bytes_=b"cbor encoded data",
        )

        # Create redeemer
        redeemer = Redeemer(
            id_=1,
            tx_id=101,
            unit_mem=1000000,
            unit_steps=500000000,
            fee=150000,
            purpose=RedeemerTag.SPEND,
            index=0,
            script_hash=script_hash,
            redeemer_data_id=1,
        )

        # Verify script relationships
        assert script.is_plutus is True
        assert script.plutus_version == PlutusVersion.V2
        assert script.hash_ == script_hash

        # Verify redeemer relationships
        assert redeemer.script_hash == script_hash
        assert redeemer.redeemer_data_id == redeemer_data.id_
        assert redeemer.is_spending_redeemer is True
        assert redeemer.total_execution_units == 501000000

    def test_native_script_scenario(self):
        """Test native script scenario."""
        script_hash = bytes.fromhex("c" * 56)  # 28 bytes
        native_script = Script(
            id_=2,
            tx_id=200,
            hash_=script_hash,
            type_=ScriptType.NATIVE,
            json_={
                "type": "all",
                "scripts": [{"type": "sig", "keyHash": "abc123"}],
            },
            serialised_size=128,
        )

        assert native_script.is_native is True
        assert native_script.is_plutus is False
        assert native_script.plutus_version is None
        assert native_script.json_ is not None
        assert native_script.bytes_ is None

    def test_multi_purpose_redeemer_scenario(self):
        """Test multiple redeemer purposes in one transaction."""
        tx_id = 300
        script_hash = bytes.fromhex("d" * 56)  # 28 bytes

        # Spending redeemer
        spend_redeemer = Redeemer(
            id_=1,
            tx_id=tx_id,
            unit_mem=800000,
            unit_steps=400000000,
            purpose=RedeemerTag.SPEND,
            index=0,
            script_hash=script_hash,
        )

        # Minting redeemer
        mint_redeemer = Redeemer(
            id_=2,
            tx_id=tx_id,
            unit_mem=500000,
            unit_steps=250000000,
            purpose=RedeemerTag.MINT,
            index=0,
            script_hash=script_hash,
        )

        # Certificate redeemer
        cert_redeemer = Redeemer(
            id_=3,
            tx_id=tx_id,
            unit_mem=300000,
            unit_steps=150000000,
            purpose=RedeemerTag.CERT,
            index=0,
            script_hash=script_hash,
        )

        assert spend_redeemer.is_spending_redeemer is True
        assert mint_redeemer.is_minting_redeemer is True
        assert cert_redeemer.is_certificate_redeemer is True

        # Verify execution costs
        assert spend_redeemer.total_execution_units == 400800000
        assert mint_redeemer.total_execution_units == 250500000
        assert cert_redeemer.total_execution_units == 150300000
