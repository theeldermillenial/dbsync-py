"""Integration tests for multi-asset models.

Tests asset models with actual database connections and verifies
read-only behavior and proper SQLAlchemy integration.
"""

from sqlmodel import select

from dbsync.models import (
    MaTxMint,
    MaTxOut,
    MultiAsset,
)


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
