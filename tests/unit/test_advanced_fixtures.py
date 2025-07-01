"""Tests demonstrating advanced fixtures and testing patterns.

This module shows how to use the comprehensive fixture system for
creating sophisticated test scenarios with realistic test data.
"""

import pytest

from tests.fixtures import (
    create_block_sequence,
    create_epoch_sequence,
    create_transaction_batch,
    performance_test_data,
    reproducible_test_data,
)


@pytest.mark.unit
class TestBasicFixtures:
    """Test basic fixture functionality."""

    def test_sample_epoch_fixture(self, sample_epoch):
        """Test that sample_epoch fixture works correctly."""
        assert sample_epoch.no > 0
        assert sample_epoch.start_time < sample_epoch.end_time
        assert sample_epoch.tx_count > 0
        assert sample_epoch.blk_count > 0
        assert sample_epoch.out_sum > 0

    def test_sample_block_fixture(self, sample_block):
        """Test that sample_block fixture works correctly."""
        assert len(sample_block.hash_) == 32
        assert sample_block.epoch_no > 0
        assert sample_block.slot_no > 0
        assert sample_block.block_no > 0
        assert sample_block.size > 0
        assert sample_block.tx_count >= 0

    def test_sample_transaction_fixture(self, sample_transaction):
        """Test that sample_transaction fixture works correctly."""
        assert len(sample_transaction.hash_) == 32
        assert sample_transaction.block_id > 0
        assert sample_transaction.fee > 0
        assert sample_transaction.size > 0
        assert sample_transaction.valid_contract is True

    def test_sample_stake_address_fixture(self, sample_stake_address):
        """Test that sample_stake_address fixture works correctly."""
        assert len(sample_stake_address.hash_raw) == 28
        assert sample_stake_address.view.startswith("stake_test1")
        assert len(sample_stake_address.view) > 20


@pytest.mark.unit
class TestTransactionRelatedFixtures:
    """Test transaction-related fixtures."""

    def test_sample_tx_output_fixture(self, sample_tx_output):
        """Test that sample_tx_output fixture works correctly."""
        assert sample_tx_output.tx_id > 0
        assert sample_tx_output.index >= 0
        assert sample_tx_output.address_id > 0
        assert sample_tx_output.value > 0

    def test_sample_tx_input_fixture(self, sample_tx_input):
        """Test that sample_tx_input fixture works correctly."""
        assert sample_tx_input.tx_in_id > 0
        assert sample_tx_input.tx_out_id > 0
        assert sample_tx_input.tx_out_index >= 0

    def test_complete_transaction_scenario_fixture(self, complete_transaction_scenario):
        """Test complete transaction scenario fixture."""
        scenario = complete_transaction_scenario

        assert "transaction" in scenario
        assert "outputs" in scenario
        assert "inputs" in scenario
        assert "multi_assets" in scenario
        assert "redeemers" in scenario

        # Verify relationships
        tx = scenario["transaction"]
        outputs = scenario["outputs"]
        inputs = scenario["inputs"]

        assert len(outputs) > 0
        assert len(inputs) > 0
        assert outputs[0].tx_id == tx.id_
        assert inputs[0].tx_in_id == tx.id_


@pytest.mark.assets
class TestAssetRelatedFixtures:
    """Test asset-related fixtures."""

    def test_sample_multi_asset_fixture(self, sample_multi_asset):
        """Test that sample_multi_asset fixture works correctly."""
        assert len(sample_multi_asset.policy) == 28
        assert len(sample_multi_asset.name) <= 32
        assert sample_multi_asset.fingerprint.startswith("asset1")

    def test_sample_ma_tx_out_fixture(self, sample_ma_tx_out):
        """Test that sample_ma_tx_out fixture works correctly."""
        assert sample_ma_tx_out.ident > 0  # References multi_asset.id
        assert sample_ma_tx_out.quantity > 0
        assert sample_ma_tx_out.tx_out_id > 0

    def test_sample_ma_tx_mint_fixture(self, sample_ma_tx_mint):
        """Test that sample_ma_tx_mint fixture works correctly."""
        assert sample_ma_tx_mint.ident > 0  # References multi_asset.id
        assert sample_ma_tx_mint.quantity != 0  # Can be positive or negative
        assert sample_ma_tx_mint.tx_id > 0


@pytest.mark.scripts
class TestScriptRelatedFixtures:
    """Test script-related fixtures."""

    def test_sample_native_script_fixture(self, sample_native_script):
        """Test that sample_native_script fixture works correctly."""
        assert len(sample_native_script.hash_) == 28
        assert sample_native_script.type_ == "native"
        assert sample_native_script.json_ is not None
        assert "type" in sample_native_script.json_
        assert sample_native_script.serialised_size > 0

    def test_sample_plutus_script_fixture(self, sample_plutus_script):
        """Test that sample_plutus_script fixture works correctly."""
        assert len(sample_plutus_script.hash_) == 28
        assert sample_plutus_script.type_ in ["plutusV1", "plutusV2", "plutusV3"]
        assert sample_plutus_script.bytes_ is not None
        assert len(sample_plutus_script.bytes_) > 0
        assert sample_plutus_script.serialised_size > 0

    def test_sample_redeemer_data_fixture(self, sample_redeemer_data):
        """Test that sample_redeemer_data fixture works correctly."""
        assert len(sample_redeemer_data.hash_) == 32
        assert sample_redeemer_data.tx_id > 0
        assert sample_redeemer_data.value is not None
        assert sample_redeemer_data.bytes_ is not None
        assert len(sample_redeemer_data.bytes_) > 0

    def test_sample_redeemer_fixture(self, sample_redeemer):
        """Test that sample_redeemer fixture works correctly."""
        assert sample_redeemer.tx_id > 0
        assert sample_redeemer.unit_mem > 0
        assert sample_redeemer.unit_steps > 0
        assert sample_redeemer.fee > 0
        assert sample_redeemer.purpose in ["spend", "mint", "cert", "reward"]
        assert sample_redeemer.index >= 0

    def test_sample_cost_model_fixture(self, sample_cost_model):
        """Test that sample_cost_model fixture works correctly."""
        assert len(sample_cost_model.hash_) == 32
        assert sample_cost_model.costs is not None
        assert len(sample_cost_model.costs) > 0

        # Check that it has realistic cost model parameters
        assert "addInteger-cpu-arguments-intercept" in sample_cost_model.costs
        assert sample_cost_model.costs["addInteger-cpu-arguments-intercept"] > 0


@pytest.mark.staking
class TestStakingRelatedFixtures:
    """Test staking-related fixtures."""

    def test_sample_stake_registration_fixture(self, sample_stake_registration):
        """Test that sample_stake_registration fixture works correctly."""
        assert sample_stake_registration.addr_id > 0
        assert sample_stake_registration.cert_index >= 0
        assert sample_stake_registration.epoch_no > 0
        assert sample_stake_registration.tx_id > 0

    def test_sample_stake_deregistration_fixture(self, sample_stake_deregistration):
        """Test that sample_stake_deregistration fixture works correctly."""
        assert sample_stake_deregistration.addr_id > 0
        assert sample_stake_deregistration.cert_index >= 0
        assert sample_stake_deregistration.epoch_no > 0
        assert sample_stake_deregistration.tx_id > 0

    def test_sample_delegation_fixture(self, sample_delegation):
        """Test that sample_delegation fixture works correctly."""
        assert sample_delegation.addr_id > 0
        assert sample_delegation.cert_index >= 0
        assert sample_delegation.pool_hash_id > 0
        assert sample_delegation.active_epoch_no > 0
        assert sample_delegation.tx_id > 0
        assert sample_delegation.slot_no > 0

    def test_complete_staking_scenario_fixture(self, complete_staking_scenario):
        """Test complete staking scenario fixture."""
        scenario = complete_staking_scenario

        assert "stake_address" in scenario
        assert "registration" in scenario
        assert "delegation" in scenario
        assert "pool" in scenario

        # Verify relationships
        stake_addr = scenario["stake_address"]
        registration = scenario["registration"]
        delegation = scenario["delegation"]

        assert registration.addr_id == stake_addr.id_
        assert delegation.addr_id == stake_addr.id_


@pytest.mark.governance
class TestGovernanceRelatedFixtures:
    """Test governance-related fixtures."""

    def test_sample_drep_registration_fixture(self, sample_drep_registration):
        """Test that sample_drep_registration fixture works correctly."""
        assert sample_drep_registration.tx_id > 0
        assert sample_drep_registration.cert_index >= 0
        assert sample_drep_registration.deposit == 500000000  # 500 ADA
        assert sample_drep_registration.drep_hash_id > 0

    def test_sample_voting_procedure_fixture(self, sample_voting_procedure):
        """Test that sample_voting_procedure fixture works correctly."""
        assert sample_voting_procedure.tx_id > 0
        assert sample_voting_procedure.index >= 0
        assert sample_voting_procedure.gov_action_proposal_id > 0
        assert sample_voting_procedure.voter_role in [
            "ConstitutionalCommittee",
            "DRep",
            "SPO",
        ]
        # Check that the appropriate voter field is set based on role
        if sample_voting_procedure.voter_role == "ConstitutionalCommittee":
            assert sample_voting_procedure.committee_voter > 0
        elif sample_voting_procedure.voter_role == "DRep":
            assert sample_voting_procedure.drep_voter > 0
        else:  # SPO
            assert sample_voting_procedure.pool_voter > 0
        assert sample_voting_procedure.vote in ["Yes", "No", "Abstain"]

    def test_sample_gov_action_proposal_fixture(self, sample_gov_action_proposal):
        """Test that sample_gov_action_proposal fixture works correctly."""
        assert sample_gov_action_proposal.tx_id > 0
        assert sample_gov_action_proposal.index >= 0
        assert sample_gov_action_proposal.deposit >= 1000000000  # At least 1000 ADA
        assert sample_gov_action_proposal.return_address > 0
        assert sample_gov_action_proposal.expiration > 0

    def test_complete_governance_scenario_fixture(self, complete_governance_scenario):
        """Test complete governance scenario fixture."""
        scenario = complete_governance_scenario

        assert "drep_registration" in scenario
        assert "voting_procedure" in scenario
        assert "gov_action_proposal" in scenario

        # All components should exist
        assert scenario["drep_registration"] is not None
        assert scenario["voting_procedure"] is not None
        assert scenario["gov_action_proposal"] is not None


@pytest.mark.unit
class TestFactoryFunctions:
    """Test factory functions for bulk data generation."""

    def test_create_epoch_sequence(self):
        """Test create_epoch_sequence function."""
        epochs = create_epoch_sequence(5, start_epoch=100)

        assert len(epochs) == 5
        assert epochs[0].no == 100
        assert epochs[4].no == 104

        # Verify sequential ordering
        for i in range(1, len(epochs)):
            assert epochs[i].no == epochs[i - 1].no + 1
            assert epochs[i].start_time > epochs[i - 1].start_time

    def test_create_block_sequence(self):
        """Test create_block_sequence function."""
        blocks = create_block_sequence(3, epoch_no=200)

        assert len(blocks) == 3
        assert all(block.epoch_no == 200 for block in blocks)

        # Verify sequential block numbers
        for i in range(1, len(blocks)):
            assert blocks[i].block_no > blocks[i - 1].block_no

    def test_create_transaction_batch(self):
        """Test create_transaction_batch function."""
        transactions = create_transaction_batch(4, block_id=1000)

        assert len(transactions) == 4
        assert all(tx.block_id == 1000 for tx in transactions)
        assert all(tx.fee > 0 for tx in transactions)
        assert all(tx.size > 0 for tx in transactions)


@pytest.mark.unit
class TestContextManagers:
    """Test context managers for test setup."""

    def test_reproducible_test_data_context_manager(self):
        """Test reproducible_test_data context manager."""
        # Generate data with same seed twice
        with reproducible_test_data(seed=42):
            epochs1 = create_epoch_sequence(3)
            blocks1 = create_block_sequence(2)

        with reproducible_test_data(seed=42):
            epochs2 = create_epoch_sequence(3)
            blocks2 = create_block_sequence(2)

        # Should be identical
        assert len(epochs1) == len(epochs2)
        assert len(blocks1) == len(blocks2)

        for e1, e2 in zip(epochs1, epochs2, strict=False):
            assert e1.no == e2.no
            assert e1.tx_count == e2.tx_count
            assert e1.blk_count == e2.blk_count

    def test_performance_test_data_context_manager(self):
        """Test performance_test_data context manager."""
        with performance_test_data(scale="small") as data:
            assert "epochs" in data
            assert "blocks" in data
            assert "transactions" in data
            assert "config" in data

            config = data["config"]
            epochs = data["epochs"]
            blocks = data["blocks"]
            transactions = data["transactions"]

            # Verify scale configuration
            assert len(epochs) == config["epochs"]
            assert len(blocks) == config["epochs"] * config["blocks_per_epoch"]
            assert len(transactions) == len(blocks) * config["txs_per_block"]

            # Verify relationships
            assert all(epoch.no > 0 for epoch in epochs)
            assert all(block.epoch_no in [e.no for e in epochs] for block in blocks)
            assert all(
                tx.block_id in [b.id_ or 1 for b in blocks] for tx in transactions
            )


@pytest.mark.performance
class TestPerformanceScenarios:
    """Test performance scenarios using different scales."""

    def test_small_scale_performance(self):
        """Test small scale performance scenario."""
        with performance_test_data(scale="small") as data:
            config = data["config"]

            # Small scale should be manageable
            assert config["epochs"] == 5
            assert config["blocks_per_epoch"] == 10
            assert config["txs_per_block"] == 5

            # Total data should be reasonable
            total_transactions = len(data["transactions"])
            expected_total = 5 * 10 * 5  # 250 transactions
            assert total_transactions == expected_total

    def test_medium_scale_performance(self):
        """Test medium scale performance scenario."""
        with performance_test_data(scale="medium") as data:
            config = data["config"]

            # Medium scale should be larger
            assert config["epochs"] == 20
            assert config["blocks_per_epoch"] == 50
            assert config["txs_per_block"] == 20

            # Total data should be significant
            total_transactions = len(data["transactions"])
            expected_total = 20 * 50 * 20  # 20,000 transactions
            assert total_transactions == expected_total


@pytest.mark.integration
class TestFixtureIntegration:
    """Test how fixtures work together in integration scenarios."""

    def test_full_blockchain_scenario(
        self, sample_epoch, sample_block, sample_transaction
    ):
        """Test full blockchain scenario integration."""
        # Verify epoch -> block -> transaction hierarchy
        assert sample_block.epoch_no == sample_epoch.no
        assert sample_transaction.block_id == (sample_block.id_ or 1)

        # Verify realistic relationships
        assert sample_epoch.start_time.year >= 2020  # After Cardano mainnet launch
        assert sample_block.slot_no > 0
        assert sample_transaction.fee > 100000  # At least 0.1 ADA fee

    def test_staking_delegation_flow(self, complete_staking_scenario):
        """Test staking delegation flow integration."""
        scenario = complete_staking_scenario

        stake_addr = scenario["stake_address"]
        registration = scenario["registration"]
        delegation = scenario["delegation"]
        pool = scenario["pool"]

        # Verify the flow: address -> registration -> delegation to pool
        assert registration.addr_id == stake_addr.id_
        assert delegation.addr_id == stake_addr.id_
        assert delegation.pool_hash_id == pool.id_

        # Verify realistic values
        assert registration.tx_id > 0  # Valid transaction reference
        assert len(pool.hash_raw) == 28  # Pool hash is 28 bytes
        assert pool.view.startswith("pool1")  # Pool bech32 format

    def test_governance_voting_flow(self, complete_governance_scenario):
        """Test governance voting flow integration."""
        scenario = complete_governance_scenario

        drep_reg = scenario["drep_registration"]
        voting_proc = scenario["voting_procedure"]
        gov_proposal = scenario["gov_action_proposal"]

        # Verify governance flow components
        assert drep_reg.deposit == 500000000  # 500 ADA DRep deposit
        assert voting_proc.vote in ["Yes", "No", "Abstain"]
        assert gov_proposal.deposit >= 1000000000  # At least 1000 ADA proposal deposit

        # Verify realistic governance timeline
        assert gov_proposal.expiration > 0
        if gov_proposal.ratified_epoch:
            assert gov_proposal.ratified_epoch > 0
        if gov_proposal.enacted_epoch:
            assert gov_proposal.enacted_epoch >= (
                gov_proposal.ratified_epoch or gov_proposal.expiration
            )
