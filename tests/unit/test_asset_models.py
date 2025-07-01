"""Unit tests for multi-asset models.

Tests all asset-related models including native tokens, minting events,
and multi-asset outputs with CIP14 fingerprint support.
"""

from dbsync.models import (
    MaTxMint,
    MaTxOut,
    MultiAsset,
    generate_cip14_fingerprint,
)


class TestCIP14Fingerprint:
    """Tests for CIP14 asset fingerprint generation."""

    def test_generate_cip14_fingerprint_basic(self):
        """Test basic CIP14 fingerprint generation."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"TestToken"

        fingerprint = generate_cip14_fingerprint(policy_id, asset_name)

        assert fingerprint.startswith("asset")
        assert len(fingerprint) > 5  # Should have content after prefix
        assert isinstance(fingerprint, str)

    def test_generate_cip14_fingerprint_empty_name(self):
        """Test CIP14 fingerprint generation with empty asset name."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b""

        fingerprint = generate_cip14_fingerprint(policy_id, asset_name)

        assert fingerprint.startswith("asset")
        assert isinstance(fingerprint, str)

    def test_generate_cip14_fingerprint_long_name(self):
        """Test CIP14 fingerprint generation with long asset name."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"VeryLongAssetNameThatExceedsNormalLength" * 2

        fingerprint = generate_cip14_fingerprint(policy_id, asset_name)

        assert fingerprint.startswith("asset")
        assert isinstance(fingerprint, str)

    def test_generate_cip14_fingerprint_consistency(self):
        """Test that same inputs produce same fingerprint."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"ConsistencyTest"

        fingerprint1 = generate_cip14_fingerprint(policy_id, asset_name)
        fingerprint2 = generate_cip14_fingerprint(policy_id, asset_name)

        assert fingerprint1 == fingerprint2

    def test_generate_cip14_fingerprint_different_inputs(self):
        """Test that different inputs produce different fingerprints."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name1 = b"Token1"
        asset_name2 = b"Token2"

        fingerprint1 = generate_cip14_fingerprint(policy_id, asset_name1)
        fingerprint2 = generate_cip14_fingerprint(policy_id, asset_name2)

        assert fingerprint1 != fingerprint2


class TestMultiAsset:
    """Tests for the MultiAsset model."""

    def test_multi_asset_creation(self):
        """Test basic MultiAsset model creation."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"TestToken"

        asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
        )

        assert asset.policy == policy_id
        assert asset.name == asset_name
        assert asset.fingerprint is None  # Not auto-generated in constructor

    def test_multi_asset_with_fingerprint(self):
        """Test MultiAsset model with explicit fingerprint."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"TestToken"
        fingerprint = "asset1234567890abcdef"

        asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
            fingerprint=fingerprint,
        )

        assert asset.policy == policy_id
        assert asset.name == asset_name
        assert asset.fingerprint == fingerprint

    def test_multi_asset_fields(self):
        """Test MultiAsset model fields and types."""
        asset = MultiAsset()
        assert hasattr(asset, "id_")
        assert hasattr(asset, "policy")
        assert hasattr(asset, "name")
        assert hasattr(asset, "fingerprint")
        assert hasattr(asset, "mint_events")
        assert hasattr(asset, "outputs")

    def test_multi_asset_hex_properties(self):
        """Test MultiAsset hex property methods."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"TestToken"

        asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
        )

        assert asset.policy_id_hex == policy_id.hex()
        assert asset.asset_name_hex == asset_name.hex()

    def test_multi_asset_empty_name_hex(self):
        """Test MultiAsset hex properties with empty name."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes

        asset = MultiAsset(
            policy=policy_id,
            name=b"",
        )

        assert asset.policy_id_hex == policy_id.hex()
        assert asset.asset_name_hex == ""

    def test_multi_asset_pycardano_integration_not_available(self):
        """Test pycardano integration when library not available."""
        policy_id = b"1234567890123456789012345678"  # 28 bytes
        asset_name = b"TestToken"

        asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
        )

        # Test the pycardano integration methods
        # If pycardano is available, they should work; if not, they should raise ImportError
        try:
            asset_name_obj = asset.to_pycardano_asset_name()
            policy_id_obj = asset.to_pycardano_policy_id()
            # If we get here, pycardano is available and working
            assert asset_name_obj is not None
            assert policy_id_obj is not None
        except ImportError as e:
            # If pycardano is not available, verify the error message
            assert "pycardano is required" in str(e)


class TestMaTxMint:
    """Tests for the MaTxMint model."""

    def test_ma_tx_mint_creation(self):
        """Test basic MaTxMint model creation."""
        mint_event = MaTxMint(
            quantity=1000,
            tx_id=1,
            ident=1,
        )

        assert mint_event.quantity == 1000
        assert mint_event.tx_id == 1
        assert mint_event.ident == 1

    def test_ma_tx_mint_negative_quantity(self):
        """Test MaTxMint model with negative quantity (burn)."""
        burn_event = MaTxMint(
            quantity=-500,
            tx_id=1,
            ident=1,
        )

        assert burn_event.quantity == -500
        assert burn_event.tx_id == 1
        assert burn_event.ident == 1

    def test_ma_tx_mint_fields(self):
        """Test MaTxMint model fields and types."""
        mint_event = MaTxMint()
        assert hasattr(mint_event, "id_")
        assert hasattr(mint_event, "quantity")
        assert hasattr(mint_event, "tx_id")
        assert hasattr(mint_event, "ident")
        assert hasattr(mint_event, "transaction")
        assert hasattr(mint_event, "multi_asset")

    def test_ma_tx_mint_is_mint_property(self):
        """Test MaTxMint is_mint property."""
        mint_event = MaTxMint(quantity=1000, tx_id=1, ident=1)
        burn_event = MaTxMint(quantity=-500, tx_id=1, ident=1)
        zero_event = MaTxMint(quantity=0, tx_id=1, ident=1)

        assert mint_event.is_mint is True
        assert burn_event.is_mint is False
        assert zero_event.is_mint is False

    def test_ma_tx_mint_is_burn_property(self):
        """Test MaTxMint is_burn property."""
        mint_event = MaTxMint(quantity=1000, tx_id=1, ident=1)
        burn_event = MaTxMint(quantity=-500, tx_id=1, ident=1)
        zero_event = MaTxMint(quantity=0, tx_id=1, ident=1)

        assert mint_event.is_burn is False
        assert burn_event.is_burn is True
        assert zero_event.is_burn is False

    def test_ma_tx_mint_absolute_quantity_property(self):
        """Test MaTxMint absolute_quantity property."""
        mint_event = MaTxMint(quantity=1000, tx_id=1, ident=1)
        burn_event = MaTxMint(quantity=-500, tx_id=1, ident=1)
        zero_event = MaTxMint(quantity=0, tx_id=1, ident=1)

        assert mint_event.absolute_quantity == 1000
        assert burn_event.absolute_quantity == 500
        assert zero_event.absolute_quantity == 0

    def test_ma_tx_mint_large_quantities(self):
        """Test MaTxMint with large quantities."""
        large_mint = MaTxMint(
            quantity=1_000_000_000_000,  # 1 trillion
            tx_id=1,
            ident=1,
        )

        assert large_mint.quantity == 1_000_000_000_000
        assert large_mint.is_mint is True
        assert large_mint.absolute_quantity == 1_000_000_000_000


class TestMaTxOut:
    """Tests for the MaTxOut model."""

    def test_ma_tx_out_creation(self):
        """Test basic MaTxOut model creation."""
        output = MaTxOut(
            quantity=250,
            tx_out_id=1,
            ident=1,
        )

        assert output.quantity == 250
        assert output.tx_out_id == 1
        assert output.ident == 1

    def test_ma_tx_out_fields(self):
        """Test MaTxOut model fields and types."""
        output = MaTxOut()
        assert hasattr(output, "id_")
        assert hasattr(output, "quantity")
        assert hasattr(output, "tx_out_id")
        assert hasattr(output, "ident")
        assert hasattr(output, "transaction_output")
        assert hasattr(output, "multi_asset")

    def test_ma_tx_out_quantity_lovelace_property(self):
        """Test MaTxOut quantity_lovelace property."""
        output = MaTxOut(quantity=1000, tx_out_id=1, ident=1)

        assert output.quantity_lovelace == 1000

    def test_ma_tx_out_large_quantity(self):
        """Test MaTxOut with large quantity."""
        large_output = MaTxOut(
            quantity=999_999_999_999,
            tx_out_id=1,
            ident=1,
        )

        assert large_output.quantity == 999_999_999_999
        assert large_output.quantity_lovelace == 999_999_999_999

    def test_ma_tx_out_zero_quantity(self):
        """Test MaTxOut with zero quantity."""
        zero_output = MaTxOut(
            quantity=0,
            tx_out_id=1,
            ident=1,
        )

        assert zero_output.quantity == 0
        assert zero_output.quantity_lovelace == 0


class TestAssetLifecycleSimulation:
    """Tests simulating complete asset lifecycle scenarios."""

    def test_asset_creation_and_minting_lifecycle(self):
        """Test complete asset creation and minting lifecycle."""
        # 1. Create a new asset
        policy_id = b"abcdef1234567890abcdef123456"  # 28 bytes
        asset_name = b"MyToken"
        fingerprint = generate_cip14_fingerprint(policy_id, asset_name)

        asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
            fingerprint=fingerprint,
        )

        # 2. Mint some tokens
        initial_mint = MaTxMint(
            quantity=1_000_000,  # 1 million tokens
            tx_id=100,
            ident=1,  # Would be asset.id in real scenario
        )

        # 3. Add tokens to an output
        output_amount = MaTxOut(
            quantity=500_000,  # 500k tokens to output
            tx_out_id=50,
            ident=1,  # Would be asset.id in real scenario
        )

        # Verify the lifecycle
        assert asset.policy == policy_id
        assert asset.name == asset_name
        assert asset.fingerprint == fingerprint
        assert initial_mint.is_mint is True
        assert initial_mint.quantity == 1_000_000
        assert output_amount.quantity == 500_000

    def test_asset_burning_lifecycle(self):
        """Test asset burning lifecycle."""
        # 1. Create asset (already exists)
        asset = MultiAsset(
            policy=b"1234567890123456789012345678",
            name=b"BurnableToken",
        )

        # 2. Burn some tokens
        burn_event = MaTxMint(
            quantity=-250_000,  # Burn 250k tokens
            tx_id=200,
            ident=1,
        )

        # Verify burning
        assert burn_event.is_burn is True
        assert burn_event.quantity == -250_000
        assert burn_event.absolute_quantity == 250_000

    def test_nft_lifecycle(self):
        """Test NFT (unique asset) lifecycle."""
        # 1. Create NFT asset
        policy_id = b"nftpolicy123456789012345678"  # 28 bytes
        asset_name = b"UniqueNFT001"

        nft_asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
        )

        # 2. Mint exactly 1 NFT
        nft_mint = MaTxMint(
            quantity=1,  # Single NFT
            tx_id=300,
            ident=1,
        )

        # 3. NFT in output
        nft_output = MaTxOut(
            quantity=1,  # Single NFT
            tx_out_id=75,
            ident=1,
        )

        # Verify NFT properties
        assert nft_asset.policy == policy_id
        assert nft_asset.name == asset_name
        assert nft_mint.quantity == 1
        assert nft_mint.is_mint is True
        assert nft_output.quantity == 1

    def test_multi_asset_transaction_lifecycle(self):
        """Test transaction with multiple assets."""
        # 1. Create multiple assets
        token_asset = MultiAsset(
            policy=b"token123456789012345678901234",
            name=b"UtilityToken",
        )

        nft_asset = MultiAsset(
            policy=b"nft567890123456789012345678",
            name=b"CollectibleNFT",
        )

        # 2. Mint both in same transaction
        token_mint = MaTxMint(quantity=1000000, tx_id=400, ident=1)
        nft_mint = MaTxMint(quantity=1, tx_id=400, ident=2)

        # 3. Distribute to outputs
        token_output1 = MaTxOut(quantity=600000, tx_out_id=80, ident=1)
        token_output2 = MaTxOut(quantity=400000, tx_out_id=81, ident=1)
        nft_output = MaTxOut(quantity=1, tx_out_id=82, ident=2)

        # Verify multi-asset transaction
        assert token_mint.tx_id == nft_mint.tx_id  # Same transaction
        assert token_mint.quantity == 1000000
        assert nft_mint.quantity == 1
        assert token_output1.quantity + token_output2.quantity == token_mint.quantity
        assert nft_output.quantity == nft_mint.quantity

    def test_fingerprint_generation_integration(self):
        """Test fingerprint generation integration with MultiAsset."""
        policy_id = b"fingerprint12345678901234567"  # 28 bytes
        asset_name = b"FingerprintTest"

        # Generate fingerprint manually
        expected_fingerprint = generate_cip14_fingerprint(policy_id, asset_name)

        # Create asset with manual fingerprint
        asset = MultiAsset(
            policy=policy_id,
            name=asset_name,
            fingerprint=expected_fingerprint,
        )

        # Verify fingerprint matches
        assert asset.fingerprint == expected_fingerprint

        # Verify hex representations
        assert asset.policy_id_hex == policy_id.hex()
        assert asset.asset_name_hex == asset_name.hex()

    def test_asset_relationships_structure(self):
        """Test asset relationship structure."""
        # Create asset
        asset = MultiAsset(
            policy=b"relationship123456789012345678",
            name=b"RelationshipTest",
        )

        # Verify relationship attributes exist
        assert hasattr(asset, "mint_events")
        assert hasattr(asset, "outputs")
        # Note: Relationships are not lists until loaded from database
        # They are SQLModel Relationship objects before that

        # Create related objects
        mint_event = MaTxMint(quantity=1000, tx_id=1, ident=1)
        output = MaTxOut(quantity=500, tx_out_id=1, ident=1)

        # Verify relationship attributes exist
        assert hasattr(mint_event, "transaction")
        assert hasattr(mint_event, "multi_asset")
        assert hasattr(output, "transaction_output")
        assert hasattr(output, "multi_asset")
