"""Unit tests for Conway era governance models.

Tests all Conway era governance functionality including DReps, Constitutional Committee,
Governance Actions, Voting, and offchain metadata models.
"""

import pytest

from dbsync.models.governance import (
    Committee,
    CommitteeDeRegistration,
    CommitteeHash,
    CommitteeMember,
    CommitteeRegistration,
    Constitution,
    DrepDistr,
    DrepHash,
    DrepRegistration,
    EpochState,
    GovActionProposal,
    GovActionType,
    OffChainVoteAuthor,
    OffChainVoteData,
    OffChainVoteDrepData,
    OffChainVoteExternalUpdate,
    OffChainVoteGovActionData,
    OffChainVoteReference,
    TreasuryWithdrawal,
    VoteType,
    VotingAnchor,
    VotingProcedure,
)

# DRep Model Tests


class TestDrepHash:
    """Test DrepHash model functionality."""

    def test_drep_hash_creation(self):
        """Test DrepHash model instantiation."""
        drep_hash = DrepHash(
            id_=1,
            raw=b"1234567890123456789012345678",  # 28 bytes
            view="drep1abcdefghijklmnopqrstuvwxyz",
            has_script=False,
        )

        assert drep_hash.id_ == 1
        assert drep_hash.raw == b"1234567890123456789012345678"
        assert drep_hash.view == "drep1abcdefghijklmnopqrstuvwxyz"
        assert drep_hash.has_script is False

    def test_drep_hash_table_name(self):
        """Test DrepHash has correct table name."""
        assert DrepHash.__tablename__ == "drep_hash"

    def test_drep_hash_script_credential(self):
        """Test DrepHash with script credential."""
        script_drep = DrepHash(
            raw=b"9876543210987654321098765432",
            view="drep_script1zyxwvutsrqponmlkjihgfedcba",
            has_script=True,
        )

        assert script_drep.has_script is True
        assert script_drep.view.startswith("drep_script")


class TestDrepRegistration:
    """Test DrepRegistration model functionality."""

    def test_drep_registration_creation(self):
        """Test DrepRegistration model instantiation."""
        registration = DrepRegistration(
            id_=1,
            tx_id=12345,
            cert_index=0,
            drep_hash_id=100,
            deposit=2000000,  # 2 ADA
            voting_anchor_id=200,
        )

        assert registration.id_ == 1
        assert registration.tx_id == 12345
        assert registration.cert_index == 0
        assert registration.drep_hash_id == 100
        assert registration.deposit == 2000000
        assert registration.voting_anchor_id == 200

    def test_drep_registration_table_name(self):
        """Test DrepRegistration has correct table name."""
        assert DrepRegistration.__tablename__ == "drep_registration"

    def test_drep_registration_without_anchor(self):
        """Test DrepRegistration without voting anchor."""
        registration = DrepRegistration(
            tx_id=12345,
            cert_index=0,
            drep_hash_id=100,
            deposit=2000000,
        )

        assert registration.voting_anchor_id is None


class TestDrepDistr:
    """Test DrepDistr model functionality."""

    def test_drep_distr_creation(self):
        """Test DrepDistr model instantiation."""
        distribution = DrepDistr(
            id_=1,
            hash_id=100,
            amount=50000000000,  # 50K ADA
            epoch_no=250,
            active_until=300,
        )

        assert distribution.id_ == 1
        assert distribution.hash_id == 100
        assert distribution.amount == 50000000000
        assert distribution.epoch_no == 250
        assert distribution.active_until == 300

    def test_drep_distr_table_name(self):
        """Test DrepDistr has correct table name."""
        assert DrepDistr.__tablename__ == "drep_distr"

    def test_drep_distr_voting_power(self):
        """Test DrepDistr represents voting power correctly."""
        large_delegation = DrepDistr(
            hash_id=100,
            amount=1000000000000,  # 1M ADA
            epoch_no=250,
        )

        assert large_delegation.amount == 1000000000000
        # Verify large delegation amounts are supported


# Committee Model Tests


class TestCommitteeHash:
    """Test CommitteeHash model functionality."""

    def test_committee_hash_creation(self):
        """Test CommitteeHash model instantiation."""
        committee_hash = CommitteeHash(
            id_=1,
            raw=b"1234567890123456789012345678",  # 28 bytes
            has_script=False,
        )

        assert committee_hash.id_ == 1
        assert committee_hash.raw == b"1234567890123456789012345678"
        assert committee_hash.has_script is False

    def test_committee_hash_table_name(self):
        """Test CommitteeHash has correct table name."""
        assert CommitteeHash.__tablename__ == "committee_hash"

    def test_committee_hash_script_member(self):
        """Test CommitteeHash with script-based member."""
        script_member = CommitteeHash(
            raw=b"9876543210987654321098765432",
            has_script=True,
        )

        assert script_member.has_script is True


class TestCommitteeRegistration:
    """Test CommitteeRegistration model functionality."""

    def test_committee_registration_creation(self):
        """Test CommitteeRegistration model instantiation."""
        registration = CommitteeRegistration(
            id_=1,
            tx_id=12345,
            cert_index=0,
            cold_key_id=100,
            hot_key_id=200,
        )

        assert registration.id_ == 1
        assert registration.tx_id == 12345
        assert registration.cert_index == 0
        assert registration.cold_key_id == 100
        assert registration.hot_key_id == 200

    def test_committee_registration_table_name(self):
        """Test CommitteeRegistration has correct table name."""
        assert CommitteeRegistration.__tablename__ == "committee_registration"

    def test_committee_registration_hot_cold_keys(self):
        """Test CommitteeRegistration hot/cold key setup."""
        registration = CommitteeRegistration(
            tx_id=12345,
            cert_index=0,
            cold_key_id=100,
            hot_key_id=200,
        )

        # Verify hot/cold key separation
        assert registration.cold_key_id != registration.hot_key_id
        assert registration.cold_key_id == 100
        assert registration.hot_key_id == 200


class TestCommitteeDeRegistration:
    """Test CommitteeDeRegistration model functionality."""

    def test_committee_deregistration_creation(self):
        """Test CommitteeDeRegistration model instantiation."""
        deregistration = CommitteeDeRegistration(
            id_=1,
            tx_id=12345,
            cert_index=1,
            cold_key_id=100,
            voting_anchor_id=200,
        )

        assert deregistration.id_ == 1
        assert deregistration.tx_id == 12345
        assert deregistration.cert_index == 1
        assert deregistration.cold_key_id == 100
        assert deregistration.voting_anchor_id == 200

    def test_committee_deregistration_table_name(self):
        """Test CommitteeDeRegistration has correct table name."""
        assert CommitteeDeRegistration.__tablename__ == "committee_de_registration"


class TestCommittee:
    """Test Committee model functionality."""

    def test_committee_creation(self):
        """Test Committee model instantiation."""
        committee = Committee(
            id_=1,
            gov_action_proposal_id=500,
            quorum_numerator=3,
            quorum_denominator=5,  # 3/5 = 60% threshold
        )

        assert committee.id_ == 1
        assert committee.gov_action_proposal_id == 500
        assert committee.quorum_numerator == 3
        assert committee.quorum_denominator == 5

    def test_committee_table_name(self):
        """Test Committee has correct table name."""
        assert Committee.__tablename__ == "committee"

    def test_committee_quorum_calculation(self):
        """Test Committee quorum threshold calculation."""
        committee = Committee(
            gov_action_proposal_id=500,
            quorum_numerator=2,
            quorum_denominator=3,  # 2/3 = ~66.7% threshold
        )

        # Calculate threshold
        threshold = committee.quorum_numerator / committee.quorum_denominator
        assert threshold == pytest.approx(0.6667, rel=1e-3)


class TestCommitteeMember:
    """Test CommitteeMember model functionality."""

    def test_committee_member_creation(self):
        """Test CommitteeMember model instantiation."""
        member = CommitteeMember(
            id_=1,
            committee_id=10,
            committee_hash_id=100,
            expiration_epoch=300,
        )

        assert member.id_ == 1
        assert member.committee_id == 10
        assert member.committee_hash_id == 100
        assert member.expiration_epoch == 300

    def test_committee_member_table_name(self):
        """Test CommitteeMember has correct table name."""
        assert CommitteeMember.__tablename__ == "committee_member"

    def test_committee_member_term_expiration(self):
        """Test CommitteeMember term expiration logic."""
        current_epoch = 250
        member = CommitteeMember(
            committee_id=10,
            committee_hash_id=100,
            expiration_epoch=300,
        )

        # Member should still be active
        assert member.expiration_epoch > current_epoch


# Governance Action Model Tests


class TestGovActionProposal:
    """Test GovActionProposal model functionality."""

    def test_gov_action_proposal_creation(self):
        """Test GovActionProposal model instantiation."""
        proposal = GovActionProposal(
            id_=1,
            tx_id=12345,
            index=0,
            deposit=100000000,  # 100 ADA
            return_address=500,
            expiration=350,
            type_=GovActionType.PARAMETER_CHANGE,
            description="Increase block size limit",
        )

        assert proposal.id_ == 1
        assert proposal.tx_id == 12345
        assert proposal.index == 0
        assert proposal.deposit == 100000000
        assert proposal.return_address == 500
        assert proposal.expiration == 350
        assert proposal.type_ == GovActionType.PARAMETER_CHANGE
        assert proposal.description == "Increase block size limit"

    def test_gov_action_proposal_table_name(self):
        """Test GovActionProposal has correct table name."""
        assert GovActionProposal.__tablename__ == "gov_action_proposal"

    def test_gov_action_types(self):
        """Test all governance action types."""
        # Test parameter change
        param_change = GovActionProposal(
            tx_id=12345,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.PARAMETER_CHANGE,
        )
        assert param_change.type_ == GovActionType.PARAMETER_CHANGE

        # Test hard fork initiation
        hard_fork = GovActionProposal(
            tx_id=12346,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.HARD_FORK_INITIATION,
        )
        assert hard_fork.type_ == GovActionType.HARD_FORK_INITIATION

        # Test treasury withdrawal
        treasury = GovActionProposal(
            tx_id=12347,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.TREASURY_WITHDRAWALS,
        )
        assert treasury.type_ == GovActionType.TREASURY_WITHDRAWALS

        # Test no confidence
        no_confidence = GovActionProposal(
            tx_id=12348,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.NO_CONFIDENCE,
        )
        assert no_confidence.type_ == GovActionType.NO_CONFIDENCE

    def test_gov_action_lifecycle(self):
        """Test GovActionProposal lifecycle tracking."""
        proposal = GovActionProposal(
            tx_id=12345,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.UPDATE_COMMITTEE,
            ratified_epoch=250,
            enacted_epoch=251,
        )

        assert proposal.ratified_epoch == 250
        assert proposal.enacted_epoch == 251
        assert proposal.dropped_epoch is None
        assert proposal.expired_epoch is None


class TestTreasuryWithdrawal:
    """Test TreasuryWithdrawal model functionality."""

    def test_treasury_withdrawal_creation(self):
        """Test TreasuryWithdrawal model instantiation."""
        withdrawal = TreasuryWithdrawal(
            id_=1,
            gov_action_proposal_id=100,
            stake_address_id=500,
            amount=1000000000,  # 1000 ADA
        )

        assert withdrawal.id_ == 1
        assert withdrawal.gov_action_proposal_id == 100
        assert withdrawal.stake_address_id == 500
        assert withdrawal.amount == 1000000000

    def test_treasury_withdrawal_table_name(self):
        """Test TreasuryWithdrawal has correct table name."""
        assert TreasuryWithdrawal.__tablename__ == "treasury_withdrawal"

    def test_treasury_withdrawal_large_amounts(self):
        """Test TreasuryWithdrawal can handle large amounts."""
        large_withdrawal = TreasuryWithdrawal(
            gov_action_proposal_id=100,
            stake_address_id=500,
            amount=10000000000000,  # 10M ADA
        )

        assert large_withdrawal.amount == 10000000000000


class TestConstitution:
    """Test Constitution model functionality."""

    def test_constitution_creation(self):
        """Test Constitution model instantiation."""
        constitution = Constitution(
            id_=1,
            gov_action_proposal_id=100,
            voting_anchor_id=200,
            script_hash=b"1234567890123456789012345678",
        )

        assert constitution.id_ == 1
        assert constitution.gov_action_proposal_id == 100
        assert constitution.voting_anchor_id == 200
        assert constitution.script_hash == b"1234567890123456789012345678"

    def test_constitution_table_name(self):
        """Test Constitution has correct table name."""
        assert Constitution.__tablename__ == "constitution"

    def test_constitution_without_guardrails(self):
        """Test Constitution without guardrails script."""
        constitution = Constitution(
            gov_action_proposal_id=100,
            voting_anchor_id=200,
        )

        assert constitution.script_hash is None


class TestVotingAnchor:
    """Test VotingAnchor model functionality."""

    def test_voting_anchor_creation(self):
        """Test VotingAnchor model instantiation."""
        anchor = VotingAnchor(
            id_=1,
            url="https://example.com/metadata.json",
            data_hash=b"12345678901234567890123456789012",  # 32 bytes
            type_="governance_action",
        )

        assert anchor.id_ == 1
        assert anchor.url == "https://example.com/metadata.json"
        assert anchor.data_hash == b"12345678901234567890123456789012"
        assert anchor.type_ == "governance_action"

    def test_voting_anchor_table_name(self):
        """Test VotingAnchor has correct table name."""
        assert VotingAnchor.__tablename__ == "voting_anchor"

    def test_voting_anchor_cip100_compliance(self):
        """Test VotingAnchor follows CIP-100 standard."""
        cip100_anchor = VotingAnchor(
            url="https://governance.cardano.org/action/123.json",
            data_hash=b"sha256_hash_32_bytes_long_conten",  # Exactly 32 bytes
            type_="action",
        )

        assert cip100_anchor.url.startswith("https://")
        assert len(cip100_anchor.data_hash) == 32


class TestVotingProcedure:
    """Test VotingProcedure model functionality."""

    def test_voting_procedure_drep_vote(self):
        """Test VotingProcedure for DRep vote."""
        vote = VotingProcedure(
            id_=1,
            tx_id=12345,
            index=0,
            gov_action_proposal_id=100,
            drep_voter=200,
            voter_role="DRep",
            vote=VoteType.YES,
        )

        assert vote.id_ == 1
        assert vote.tx_id == 12345
        assert vote.index == 0
        assert vote.gov_action_proposal_id == 100
        assert vote.drep_voter == 200
        assert vote.voter_role == "DRep"
        assert vote.vote == VoteType.YES
        assert vote.committee_voter is None
        assert vote.pool_voter is None

    def test_voting_procedure_committee_vote(self):
        """Test VotingProcedure for Constitutional Committee vote."""
        vote = VotingProcedure(
            tx_id=12345,
            index=0,
            gov_action_proposal_id=100,
            committee_voter=300,
            voter_role="ConstitutionalCommittee",
            vote=VoteType.NO,
        )

        assert vote.committee_voter == 300
        assert vote.voter_role == "ConstitutionalCommittee"
        assert vote.vote == VoteType.NO
        assert vote.drep_voter is None
        assert vote.pool_voter is None

    def test_voting_procedure_spo_vote(self):
        """Test VotingProcedure for SPO vote."""
        vote = VotingProcedure(
            tx_id=12345,
            index=0,
            gov_action_proposal_id=100,
            pool_voter=400,
            voter_role="SPO",
            vote=VoteType.ABSTAIN,
        )

        assert vote.pool_voter == 400
        assert vote.voter_role == "SPO"
        assert vote.vote == VoteType.ABSTAIN
        assert vote.committee_voter is None
        assert vote.drep_voter is None

    def test_voting_procedure_table_name(self):
        """Test VotingProcedure has correct table name."""
        assert VotingProcedure.__tablename__ == "voting_procedure"

    def test_vote_types(self):
        """Test all vote types."""
        assert VoteType.YES == "Yes"
        assert VoteType.NO == "No"
        assert VoteType.ABSTAIN == "Abstain"


class TestEpochState:
    """Test EpochState model functionality."""

    def test_epoch_state_creation(self):
        """Test EpochState model instantiation."""
        state = EpochState(
            id_=1,
            committee_id=10,
            no_confidence_id=None,  # No active no-confidence proposal
            constitution_id=5,
            epoch_no=250,
        )

        assert state.id_ == 1
        assert state.committee_id == 10
        assert state.no_confidence_id is None
        assert state.constitution_id == 5
        assert state.epoch_no == 250

    def test_epoch_state_table_name(self):
        """Test EpochState has correct table name."""
        assert EpochState.__tablename__ == "epoch_state"

    def test_epoch_state_no_confidence(self):
        """Test EpochState in no confidence state."""
        no_confidence_state = EpochState(
            epoch_no=250,
            no_confidence_id=100,  # References a no-confidence proposal
        )

        assert no_confidence_state.no_confidence_id == 100
        assert no_confidence_state.committee_id is None  # No active committee


# Offchain Metadata Model Tests


class TestOffChainVoteData:
    """Test OffChainVoteData model functionality."""

    def test_off_chain_vote_data_creation(self):
        """Test OffChainVoteData model instantiation."""
        metadata = OffChainVoteData(
            id_=1,
            voting_anchor_id=100,
            hash_=b"12345678901234567890123456789012",  # 32 bytes
            json_={"title": "Test Proposal", "abstract": "Test description"},
            language="en",
            is_valid=True,
        )

        assert metadata.id_ == 1
        assert metadata.voting_anchor_id == 100
        assert metadata.hash_ == b"12345678901234567890123456789012"
        assert metadata.json_["title"] == "Test Proposal"
        assert metadata.language == "en"
        assert metadata.is_valid is True

    def test_off_chain_vote_data_table_name(self):
        """Test OffChainVoteData has correct table name."""
        assert OffChainVoteData.__tablename__ == "off_chain_vote_data"

    def test_off_chain_vote_data_cip108_compliance(self):
        """Test OffChainVoteData follows CIP-108 standard."""
        cip108_metadata = OffChainVoteData(
            voting_anchor_id=100,
            hash_=b"sha256_hash_32_bytes_long_content",
            json_={
                "title": "Governance Action",
                "abstract": "Description",
                "motivation": "Rationale",
            },
            language="en",
            is_valid=True,
        )

        # Verify CIP-108 required fields are in JSON
        assert cip108_metadata.json_["title"] == "Governance Action"
        assert cip108_metadata.json_["abstract"] == "Description"
        assert cip108_metadata.json_["motivation"] == "Rationale"


class TestOffChainVoteGovActionData:
    """Test OffChainVoteGovActionData model functionality."""

    def test_off_chain_vote_gov_action_data_creation(self):
        """Test OffChainVoteGovActionData model instantiation."""
        link = OffChainVoteGovActionData(
            id_=1,
            off_chain_vote_data_id=100,
            title="Test Governance Action",
            abstract="Test description",
            motivation="Test motivation",
            rationale="Test rationale",
        )

        assert link.id_ == 1
        assert link.off_chain_vote_data_id == 100
        assert link.title == "Test Governance Action"
        assert link.abstract == "Test description"
        assert link.motivation == "Test motivation"
        assert link.rationale == "Test rationale"

    def test_off_chain_vote_gov_action_data_table_name(self):
        """Test OffChainVoteGovActionData has correct table name."""
        assert (
            OffChainVoteGovActionData.__tablename__ == "off_chain_vote_gov_action_data"
        )


class TestOffChainVoteDrepData:
    """Test OffChainVoteDrepData model functionality."""

    def test_off_chain_vote_drep_data_creation(self):
        """Test OffChainVoteDrepData model instantiation."""
        link = OffChainVoteDrepData(
            id_=1,
            off_chain_vote_data_id=100,
            payment_address="addr1test123",
            given_name="Test DRep",
            objectives="Test objectives",
            motivations="Test motivations",
            qualifications="Test qualifications",
        )

        assert link.id_ == 1
        assert link.off_chain_vote_data_id == 100
        assert link.payment_address == "addr1test123"
        assert link.given_name == "Test DRep"
        assert link.objectives == "Test objectives"
        assert link.motivations == "Test motivations"
        assert link.qualifications == "Test qualifications"

    def test_off_chain_vote_drep_data_table_name(self):
        """Test OffChainVoteDrepData has correct table name."""
        assert OffChainVoteDrepData.__tablename__ == "off_chain_vote_drep_data"


class TestOffChainVoteAuthor:
    """Test OffChainVoteAuthor model functionality."""

    def test_off_chain_vote_author_creation(self):
        """Test OffChainVoteAuthor model instantiation."""
        author = OffChainVoteAuthor(
            id_=1,
            off_chain_vote_data_id=100,
            name="John Doe",
            witness_algorithm="Ed25519",
            public_key="ed25519_pubkey_test",
            signature="ed25519_signature_test",
            warning="Test warning",
        )

        assert author.id_ == 1
        assert author.off_chain_vote_data_id == 100
        assert author.name == "John Doe"
        assert author.witness_algorithm == "Ed25519"
        assert author.public_key == "ed25519_pubkey_test"
        assert author.signature == "ed25519_signature_test"
        assert author.warning == "Test warning"

    def test_off_chain_vote_author_table_name(self):
        """Test OffChainVoteAuthor has correct table name."""
        assert OffChainVoteAuthor.__tablename__ == "off_chain_vote_author"


class TestOffChainVoteReference:
    """Test OffChainVoteReference model functionality."""

    def test_off_chain_vote_reference_creation(self):
        """Test OffChainVoteReference model instantiation."""
        reference = OffChainVoteReference(
            id_=1,
            off_chain_vote_data_id=100,
            label="CIP-1694 Specification",
            uri="https://cips.cardano.org/cip/CIP-1694",
            hash_digest=b"12345678901234567890123456789012",
            hash_algorithm="blake2b-256",
        )

        assert reference.id_ == 1
        assert reference.off_chain_vote_data_id == 100
        assert reference.label == "CIP-1694 Specification"
        assert reference.uri == "https://cips.cardano.org/cip/CIP-1694"
        assert reference.hash_digest == b"12345678901234567890123456789012"
        assert reference.hash_algorithm == "blake2b-256"

    def test_off_chain_vote_reference_table_name(self):
        """Test OffChainVoteReference has correct table name."""
        assert OffChainVoteReference.__tablename__ == "off_chain_vote_reference"


class TestOffChainVoteExternalUpdate:
    """Test OffChainVoteExternalUpdate model functionality."""

    def test_off_chain_vote_external_update_creation(self):
        """Test OffChainVoteExternalUpdate model instantiation."""
        update = OffChainVoteExternalUpdate(
            id_=1,
            off_chain_vote_data_id=100,
            title="Correction to Proposal",
            uri="https://example.com/correction.json",
        )

        assert update.id_ == 1
        assert update.off_chain_vote_data_id == 100
        assert update.title == "Correction to Proposal"
        assert update.uri == "https://example.com/correction.json"

    def test_off_chain_vote_external_update_table_name(self):
        """Test OffChainVoteExternalUpdate has correct table name."""
        assert (
            OffChainVoteExternalUpdate.__tablename__ == "off_chain_vote_external_update"
        )


# Integration Tests


class TestGovernanceModelsIntegration:
    """Integration tests for governance models working together."""

    def test_complete_governance_action_lifecycle(self):
        """Test complete governance action lifecycle with voting."""
        # 1. Create voting anchor for metadata
        anchor = VotingAnchor(
            url="https://governance.cardano.org/action/123.json",
            data_hash=b"12345678901234567890123456789012",
            type_="action",
        )

        # 2. Create governance action proposal
        proposal = GovActionProposal(
            tx_id=12345,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.PARAMETER_CHANGE,
            voting_anchor_id=1,  # Would be anchor.id in real scenario
            description="Increase block size to improve throughput",
        )

        # 3. Create DRep vote
        drep_vote = VotingProcedure(
            tx_id=12346,
            index=0,
            gov_action_proposal_id=1,  # Would be proposal.id
            drep_voter=200,
            voter_role="DRep",
            vote=VoteType.YES,
        )

        # 4. Create Committee vote
        committee_vote = VotingProcedure(
            tx_id=12347,
            index=0,
            gov_action_proposal_id=1,
            committee_voter=300,
            voter_role="ConstitutionalCommittee",
            vote=VoteType.YES,
        )

        # Verify all components are properly configured
        assert anchor.url.startswith("https://")
        assert proposal.type_ == GovActionType.PARAMETER_CHANGE
        assert drep_vote.vote == VoteType.YES
        assert committee_vote.vote == VoteType.YES
        assert drep_vote.gov_action_proposal_id == committee_vote.gov_action_proposal_id

    def test_drep_registration_and_voting(self):
        """Test DRep registration and subsequent voting."""
        # 1. Create DRep hash
        drep_hash = DrepHash(
            raw=b"1234567890123456789012345678",
            view="drep1abcdefghijklmnopqrstuvwxyz",
            has_script=False,
        )

        # 2. Register DRep
        registration = DrepRegistration(
            tx_id=12345,
            cert_index=0,
            drep_hash_id=1,  # Would be drep_hash.id
            deposit=2000000,
        )

        # 3. DRep receives voting power
        distribution = DrepDistr(
            hash_id=1,
            amount=50000000000,  # 50K ADA delegated
            epoch_no=250,
            active_until=300,
        )

        # 4. DRep votes on proposal
        vote = VotingProcedure(
            tx_id=12346,
            index=0,
            gov_action_proposal_id=100,
            drep_voter=1,
            voter_role="DRep",
            vote=VoteType.YES,
        )

        # Verify DRep lifecycle
        assert drep_hash.has_script is False
        assert registration.deposit == 2000000
        assert distribution.amount == 50000000000
        assert vote.vote == VoteType.YES

    def test_committee_management_lifecycle(self):
        """Test Constitutional Committee management lifecycle."""
        # 1. Create committee hash
        committee_hash = CommitteeHash(
            raw=b"1234567890123456789012345678",
            has_script=False,
        )

        # 2. Register committee member
        registration = CommitteeRegistration(
            tx_id=12345,
            cert_index=0,
            cold_key_id=100,
            hot_key_id=200,
        )

        # 3. Create committee via governance action
        committee = Committee(
            gov_action_proposal_id=500,
            quorum_numerator=3,
            quorum_denominator=5,  # 60% threshold
        )

        # 4. Add member to committee
        member = CommitteeMember(
            committee_id=1,  # Would be committee.id
            committee_hash_id=1,  # Would be committee_hash.id
            expiration_epoch=300,
        )

        # 5. Member votes on proposal
        vote = VotingProcedure(
            tx_id=12346,
            index=0,
            gov_action_proposal_id=100,
            committee_voter=1,
            voter_role="ConstitutionalCommittee",
            vote=VoteType.YES,
        )

        # Verify committee lifecycle
        assert committee_hash.has_script is False
        assert registration.cold_key_id != registration.hot_key_id
        assert committee.quorum_numerator / committee.quorum_denominator == 0.6
        assert member.expiration_epoch == 300
        assert vote.voter_role == "ConstitutionalCommittee"

    def test_offchain_metadata_integration(self):
        """Test offchain metadata integration with governance actions."""
        # 1. Create voting anchor
        anchor = VotingAnchor(
            url="https://governance.cardano.org/metadata/123.json",
            data_hash=b"12345678901234567890123456789012",
            type_="action",
        )

        # 2. Create offchain vote data
        metadata = OffChainVoteData(
            voting_anchor_id=1,  # Would be anchor.id
            hash_=b"12345678901234567890123456789012",
            json_={"title": "Test Metadata", "abstract": "Increase block size"},
            language="en",
            is_valid=True,
        )

        # 3. Link to governance action
        action_link = OffChainVoteGovActionData(
            off_chain_vote_data_id=1,  # Would be metadata.id
            title="Test Governance Action",
            abstract="Increase block size proposal",
            motivation="To improve network throughput",
            rationale="Technical analysis shows benefits",
        )

        # 4. Add author information
        author = OffChainVoteAuthor(
            off_chain_vote_data_id=1,
            name="Governance Committee",
            witness_algorithm="Ed25519",
            public_key="ed25519_pubkey_test",
            signature="ed25519_signature_test",
        )

        # 5. Add references
        reference = OffChainVoteReference(
            off_chain_vote_data_id=1,
            label="Technical Analysis",
            uri="https://example.com/analysis.pdf",
            hash_digest=b"87654321098765432109876543210987",
            hash_algorithm="blake2b-256",
        )

        # Verify metadata integration
        assert anchor.url.startswith("https://")
        assert metadata.json_["title"] == "Test Metadata"
        assert action_link.title == "Test Governance Action"
        assert action_link.abstract == "Increase block size proposal"
        assert author.name == "Governance Committee"
        assert reference.label == "Technical Analysis"
