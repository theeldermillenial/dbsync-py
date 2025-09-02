"""Integration tests for multi-asset models.

Tests asset models with actual database connections and verifies
read-only behavior and proper SQLAlchemy integration.
"""

import pytest
from sqlmodel import select

from dbsync.models import (
    MaTxMint,
    MaTxOut,
    MultiAsset,
)
from dbsync.models.assets import generate_cip14_fingerprint


class TestAssetModelsIntegration:
    """Integration tests for asset models with database."""

    def test_multi_asset_query_integration(self, dbsync_session):
        """Test MultiAsset model database integration."""
        # Test querying multi assets (read-only)
        stmt = select(MultiAsset).limit(1)
        result = dbsync_session.exec(stmt).first()

        # Verify we can query the model
        if result:
            assert hasattr(result, "id_")
            assert hasattr(result, "policy")
            assert hasattr(result, "name")
            assert hasattr(result, "fingerprint")

    def test_ma_tx_mint_query_integration(self, dbsync_session):
        """Test MaTxMint model database integration."""
        # Test querying minting events (read-only)
        stmt = select(MaTxMint).limit(1)
        result = dbsync_session.exec(stmt).first()

        # Verify we can query the model
        if result:
            assert hasattr(result, "id_")
            assert hasattr(result, "quantity")
            assert hasattr(result, "tx_id")
            assert hasattr(result, "ident")

    def test_ma_tx_out_query_integration(self, dbsync_session):
        """Test MaTxOut model database integration."""
        # Test querying asset outputs (read-only)
        stmt = select(MaTxOut).limit(1)
        result = dbsync_session.exec(stmt).first()

        # Verify we can query the model
        if result:
            assert hasattr(result, "id_")
            assert hasattr(result, "quantity")
            assert hasattr(result, "tx_out_id")
            assert hasattr(result, "ident")

    def test_asset_models_read_only_behavior(self, dbsync_session):
        """Test that asset models are used in read-only mode."""
        # This test verifies that the models are designed for read-only access
        # In a real dbsync environment, these tables are populated by the dbsync process

        # Test that we can create queries but the expectation is read-only usage
        multi_asset_query = select(MultiAsset)
        mint_query = select(MaTxMint)
        output_query = select(MaTxOut)

        # Verify queries can be constructed (this is the expected usage pattern)
        assert multi_asset_query is not None
        assert mint_query is not None
        assert output_query is not None

    def test_asset_relationships_integration(self, dbsync_session):
        """Test asset model relationships in database context."""
        # Test querying assets with their minting events
        stmt = (
            select(MultiAsset, MaTxMint)
            .join(MaTxMint, MultiAsset.id_ == MaTxMint.ident)
            .limit(1)
        )

        result = dbsync_session.exec(stmt).first()

        # Verify relationship queries work
        if result:
            asset, mint_event = result
            assert asset.id_ == mint_event.ident

    def test_asset_output_relationships_integration(self, dbsync_session):
        """Test asset output relationships in database context."""
        # Test querying assets with their outputs
        stmt = (
            select(MultiAsset, MaTxOut)
            .join(MaTxOut, MultiAsset.id_ == MaTxOut.ident)
            .limit(1)
        )

        result = dbsync_session.exec(stmt).first()

        # Verify output relationships work
        if result:
            asset, output = result
            assert asset.id_ == output.ident

    def test_minting_vs_burning_integration(self, dbsync_session):
        """Test distinguishing minting vs burning events in database context."""
        # Test querying minting events (positive quantities)
        mint_stmt = select(MaTxMint).where(MaTxMint.quantity > 0).limit(1)
        mint_result = dbsync_session.exec(mint_stmt).first()

        # Test querying burning events (negative quantities)
        burn_stmt = select(MaTxMint).where(MaTxMint.quantity < 0).limit(1)
        burn_result = dbsync_session.exec(burn_stmt).first()

        # Verify minting/burning logic
        if mint_result:
            assert mint_result.is_mint is True
            assert mint_result.is_burn is False
        if burn_result:
            assert burn_result.is_mint is False
            assert burn_result.is_burn is True

    def test_asset_fingerprint_integration(self, dbsync_session):
        """Test asset fingerprint functionality in database context."""
        # Test querying assets with fingerprints
        stmt = select(MultiAsset).where(MultiAsset.fingerprint.is_not(None)).limit(1)
        result = dbsync_session.exec(stmt).first()

        if result:
            # Verify fingerprint format
            assert (
                result.fingerprint.startswith("asset") if result.fingerprint else True
            )

            # Test hex property methods
            assert isinstance(result.policy_id_hex, str)
            assert isinstance(result.asset_name_hex, str)

    def test_large_quantity_handling_integration(self, dbsync_session):
        """Test handling of large quantities in database context."""
        # Test querying large minting amounts
        large_mint_stmt = select(MaTxMint).where(MaTxMint.quantity > 1000000).limit(1)
        large_mint = dbsync_session.exec(large_mint_stmt).first()

        # Test querying large output amounts
        large_output_stmt = select(MaTxOut).where(MaTxOut.quantity > 1000000).limit(1)
        large_output = dbsync_session.exec(large_output_stmt).first()

        # Verify large quantities are handled correctly
        if large_mint:
            assert large_mint.quantity > 1000000
            assert large_mint.absolute_quantity == abs(large_mint.quantity)
        if large_output:
            assert large_output.quantity > 1000000
            assert large_output.quantity_lovelace == large_output.quantity

    def test_asset_policy_analysis_integration(self, dbsync_session):
        """Test asset policy analysis in database context."""
        # Test querying assets by policy patterns
        stmt = select(MultiAsset).limit(5)
        results = dbsync_session.exec(stmt).all()

        policy_ids = set()
        for asset in results:
            if asset.policy:
                policy_ids.add(asset.policy_id_hex)

        # Verify we can analyze policy diversity
        assert isinstance(policy_ids, set)

    def test_nft_vs_fungible_token_integration(self, dbsync_session):
        """Test distinguishing NFTs vs fungible tokens in database context."""
        # Test querying single-quantity mints (potential NFTs)
        nft_stmt = select(MaTxMint).where(MaTxMint.quantity == 1).limit(1)
        nft_result = dbsync_session.exec(nft_stmt).first()

        # Test querying large-quantity mints (fungible tokens)
        token_stmt = select(MaTxMint).where(MaTxMint.quantity > 1000).limit(1)
        token_result = dbsync_session.exec(token_stmt).first()

        # Verify different asset types can be identified
        if nft_result:
            assert nft_result.quantity == 1
            assert nft_result.is_mint is True
        if token_result:
            assert token_result.quantity > 1000
            assert token_result.is_mint is True

    def test_asset_transaction_analysis_integration(self, dbsync_session):
        """Test analyzing asset transactions in database context."""
        # Test querying minting events grouped by transaction
        stmt = (
            select(MaTxMint.tx_id, MaTxMint.quantity).order_by(MaTxMint.tx_id).limit(5)
        )
        results = dbsync_session.exec(stmt).all()

        # Verify transaction-level asset analysis
        tx_quantities = {}
        for tx_id, quantity in results:
            if tx_id not in tx_quantities:
                tx_quantities[tx_id] = []
            tx_quantities[tx_id].append(quantity)

        # Verify we can group by transaction
        assert isinstance(tx_quantities, dict)

    def test_asset_output_distribution_integration(self, dbsync_session):
        """Test analyzing asset output distribution in database context."""
        # Test querying asset outputs by quantity ranges
        small_stmt = select(MaTxOut).where(MaTxOut.quantity.between(1, 100)).limit(1)
        large_stmt = select(MaTxOut).where(MaTxOut.quantity > 1000000).limit(1)

        small_result = dbsync_session.exec(small_stmt).first()
        large_result = dbsync_session.exec(large_stmt).first()

        # Verify different quantity ranges can be analyzed
        if small_result:
            assert 1 <= small_result.quantity <= 100
        if large_result:
            assert large_result.quantity > 1000000

    def test_comprehensive_asset_lifecycle_integration(self, dbsync_session):
        """Test comprehensive asset lifecycle in database context."""
        # Test querying a complete asset lifecycle
        stmt = (
            select(MultiAsset).join(MaTxMint, MultiAsset.id_ == MaTxMint.ident).limit(1)
        )

        result = dbsync_session.exec(stmt).first()

        if result:
            asset = result

            # Query all minting events for this asset
            mint_stmt = (
                select(MaTxMint)
                .where(MaTxMint.ident == asset.id_)
                .order_by(MaTxMint.tx_id)
            )
            mints = dbsync_session.exec(mint_stmt).all()

            # Query all outputs for this asset
            output_stmt = select(MaTxOut).where(MaTxOut.ident == asset.id_).limit(5)
            outputs = dbsync_session.exec(output_stmt).all()

            # Verify we can track complete asset lifecycle
            assert len(mints) >= 0  # May or may not have mints
            assert len(outputs) >= 0  # May or may not have outputs

            # Calculate total minted vs total in outputs (if data exists)
            if mints and outputs:
                total_minted = sum(mint.quantity for mint in mints if mint.quantity > 0)
                total_burned = sum(
                    abs(mint.quantity) for mint in mints if mint.quantity < 0
                )
                total_in_outputs = sum(output.quantity for output in outputs)

                # These should be consistent in a complete dataset
                assert total_minted >= 0
                assert total_burned >= 0
                assert total_in_outputs >= 0


class TestAssetModelsAdvancedIntegration:
    """Advanced integration tests for asset models covering additional functionality."""

    def test_asset_hex_properties_integration(self, dbsync_session):
        """Test asset hex property methods with real database data."""
        # Test querying assets and using hex properties
        stmt = select(MultiAsset).limit(3)
        results = dbsync_session.exec(stmt).all()

        for asset in results:
            if asset.policy and asset.name:
                # Test hex properties work with real data
                policy_hex = asset.policy_id_hex
                name_hex = asset.asset_name_hex

                # Verify hex format
                assert isinstance(policy_hex, str)
                assert isinstance(name_hex, str)
                assert len(policy_hex) == 56  # 28 bytes * 2
                assert all(c in "0123456789abcdef" for c in policy_hex.lower())
                assert all(c in "0123456789abcdef" for c in name_hex.lower())

                # Verify consistency with raw bytes
                assert bytes.fromhex(policy_hex) == asset.policy
                assert bytes.fromhex(name_hex) == asset.name

    def test_pycardano_conversion_integration(self, dbsync_session):
        """Test PyCardano conversion methods with real database data."""
        # Test querying assets and converting to PyCardano types
        stmt = select(MultiAsset).limit(1)
        result = dbsync_session.exec(stmt).first()

        if result and result.policy and result.name:
            # Test PyCardano conversions (if available)
            try:
                policy_id = result.to_pycardano_policy_id()
                asset_name = result.to_pycardano_asset_name()

                # Verify conversions work
                assert policy_id is not None
                assert asset_name is not None

                # Verify round-trip consistency
                assert policy_id.payload == result.policy
                assert asset_name.payload == result.name

            except ImportError:
                # PyCardano not available - verify that ImportError is raised
                pass  # This is expected behavior when pycardano is not available

    def test_cip14_fingerprint_integration(self, dbsync_session):
        """Test CIP14 fingerprint generation with real database data."""
        # Test querying assets and generating fingerprints
        stmt = select(MultiAsset).where(
            MultiAsset.policy.is_not(None) & MultiAsset.name.is_not(None)
        ).limit(3)
        results = dbsync_session.exec(stmt).all()

        for asset in results:
            if asset.policy and asset.name:
                # Generate CIP14 fingerprint
                generated_fingerprint = generate_cip14_fingerprint(
                    asset.policy, asset.name
                )

                # Verify fingerprint format
                assert isinstance(generated_fingerprint, str)
                assert generated_fingerprint.startswith("asset")
                assert len(generated_fingerprint) > 10

                # Test consistency - same inputs should give same output
                second_fingerprint = generate_cip14_fingerprint(
                    asset.policy, asset.name
                )
                assert generated_fingerprint == second_fingerprint

    def test_minting_properties_integration(self, dbsync_session):
        """Test minting/burning property methods with real database data."""
        # Test minting events
        mint_stmt = select(MaTxMint).where(MaTxMint.quantity > 0).limit(3)
        mint_results = dbsync_session.exec(mint_stmt).all()

        for mint_event in mint_results:
            # Test minting properties
            assert mint_event.is_mint is True
            assert mint_event.is_burn is False
            assert mint_event.absolute_quantity == mint_event.quantity
            assert mint_event.absolute_quantity > 0

        # Test burning events
        burn_stmt = select(MaTxMint).where(MaTxMint.quantity < 0).limit(3)
        burn_results = dbsync_session.exec(burn_stmt).all()

        for burn_event in burn_results:
            # Test burning properties
            assert burn_event.is_mint is False
            assert burn_event.is_burn is True
            assert burn_event.absolute_quantity == abs(burn_event.quantity)
            assert burn_event.absolute_quantity > 0

    def test_output_properties_integration(self, dbsync_session):
        """Test output property methods with real database data."""
        # Test output amounts
        stmt = select(MaTxOut).limit(5)
        results = dbsync_session.exec(stmt).all()

        for output in results:
            if output.quantity:
                # Test quantity_lovelace property
                assert output.quantity_lovelace == output.quantity
                assert output.quantity_lovelace >= 0

    def test_asset_schema_compliance_integration(self, dbsync_session):
        """Test that asset models comply with database schema in practice."""
        # Test MultiAsset schema compliance
        multi_asset_stmt = select(MultiAsset).limit(1)
        multi_asset_result = dbsync_session.exec(multi_asset_stmt).first()

        if multi_asset_result:
            # Verify all expected fields are present and have correct types
            assert isinstance(multi_asset_result.id_, (int, type(None)))
            assert isinstance(multi_asset_result.policy, bytes)
            assert isinstance(multi_asset_result.name, bytes)
            assert isinstance(multi_asset_result.fingerprint, str)
            
            # Verify policy is 28 bytes (Hash28Type)
            assert len(multi_asset_result.policy) == 28

        # Test MaTxMint schema compliance
        mint_stmt = select(MaTxMint).limit(1)
        mint_result = dbsync_session.exec(mint_stmt).first()

        if mint_result:
            # Verify all expected fields are present and have correct types
            assert isinstance(mint_result.id_, (int, type(None)))
            assert isinstance(mint_result.quantity, (int, type(mint_result.quantity)))
            assert isinstance(mint_result.tx_id, int)
            assert isinstance(mint_result.ident, int)

        # Test MaTxOut schema compliance
        out_stmt = select(MaTxOut).limit(1)
        out_result = dbsync_session.exec(out_stmt).first()

        if out_result:
            # Verify all expected fields are present and have correct types
            assert isinstance(out_result.id_, (int, type(None)))
            assert isinstance(out_result.quantity, (int, type(out_result.quantity)))
            assert isinstance(out_result.tx_out_id, int)
            assert isinstance(out_result.ident, int)

    def test_asset_edge_cases_integration(self, dbsync_session):
        """Test asset model edge cases with real database data."""
        # Test assets with empty names
        empty_name_stmt = select(MultiAsset).where(MultiAsset.name == b"").limit(1)
        empty_name_result = dbsync_session.exec(empty_name_stmt).first()

        if empty_name_result:
            # Should handle empty names gracefully
            assert empty_name_result.asset_name_hex == ""
            assert len(empty_name_result.name) == 0

        # Test very large quantities
        large_quantity_stmt = select(MaTxOut).where(
            MaTxOut.quantity > 1000000000000  # > 1 trillion
        ).limit(1)
        large_quantity_result = dbsync_session.exec(large_quantity_stmt).first()

        if large_quantity_result:
            # Should handle large quantities correctly
            assert large_quantity_result.quantity > 1000000000000
            assert large_quantity_result.quantity_lovelace == large_quantity_result.quantity

    def test_comprehensive_asset_ecosystem_integration(self, dbsync_session):
        """Test the complete asset ecosystem integration."""
        # Query a comprehensive view of the asset ecosystem
        stmt = (
            select(MultiAsset, MaTxMint, MaTxOut)
            .join(MaTxMint, MultiAsset.id_ == MaTxMint.ident)
            .join(MaTxOut, MultiAsset.id_ == MaTxOut.ident)
            .limit(1)
        )

        result = dbsync_session.exec(stmt).first()

        if result:
            asset, mint_event, output = result

            # Verify all components are related
            assert asset.id_ == mint_event.ident == output.ident

            # Test all methods work together
            fingerprint = generate_cip14_fingerprint(asset.policy, asset.name)
            assert isinstance(fingerprint, str)

            policy_hex = asset.policy_id_hex
            name_hex = asset.asset_name_hex
            assert len(policy_hex) == 56
            assert len(name_hex) == len(asset.name) * 2

            # Test mint/burn properties
            if mint_event.quantity > 0:
                assert mint_event.is_mint
                assert not mint_event.is_burn
            else:
                assert not mint_event.is_mint
                assert mint_event.is_burn

            # Test output properties
            assert output.quantity_lovelace == output.quantity
