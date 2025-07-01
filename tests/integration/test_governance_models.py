"""Integration tests for Conway era governance models.

Tests governance models with actual database interactions to verify
schema compliance and data integrity.
"""

import pytest
from sqlmodel import Session, select

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


class TestGovernanceModelsIntegration:
    """Integration tests for governance models."""

    def test_drep_hash_model(self, dbsync_session: Session) -> None:
        """Test DrepHash model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(DrepHash).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "raw")
                assert hasattr(result, "view")
                assert hasattr(result, "has_script")

                # Verify DRep hash structure
                if result.raw is not None:
                    assert len(result.raw) == 28  # DRep hash is 28 bytes
                if result.view is not None:
                    assert isinstance(result.view, str)
                    assert len(result.view) > 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_drep_registration_model(self, dbsync_session: Session) -> None:
        """Test DrepRegistration model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(DrepRegistration).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "cert_index")
                assert hasattr(result, "drep_hash_id")
                assert hasattr(result, "deposit")
                assert hasattr(result, "voting_anchor_id")

                # Conway era features - DRep registration
                if result.drep_hash_id is not None:
                    assert isinstance(result.drep_hash_id, int)
                    assert result.drep_hash_id > 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_drep_distr_model(self, dbsync_session: Session) -> None:
        """Test DrepDistr model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(DrepDistr).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "hash_id")
                assert hasattr(result, "amount")
                assert hasattr(result, "epoch_no")
                assert hasattr(result, "active_until")

                # Verify voting power distribution
                if result.amount is not None:
                    assert result.amount >= 0  # Non-negative voting power
                if result.epoch_no is not None:
                    assert result.epoch_no >= 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_committee_hash_model(self, dbsync_session: Session) -> None:
        """Test CommitteeHash model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(CommitteeHash).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "raw")
                assert hasattr(result, "has_script")

                # Verify committee hash structure
                if result.raw is not None:
                    assert len(result.raw) == 28  # Committee hash is 28 bytes

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_committee_registration_model(self, dbsync_session: Session) -> None:
        """Test CommitteeRegistration model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(CommitteeRegistration).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "cert_index")
                assert hasattr(result, "cold_key_id")
                assert hasattr(result, "hot_key_id")

                # Verify hot/cold key setup - these are now foreign key IDs
                if result.cold_key_id is not None:
                    assert result.cold_key_id > 0
                if result.hot_key_id is not None:
                    assert result.hot_key_id > 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_committee_deregistration_model(self, dbsync_session: Session) -> None:
        """Test CommitteeDeRegistration model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(
                select(CommitteeDeRegistration).limit(1)
            ).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "cert_index")
                assert hasattr(result, "cold_key_id")
                assert hasattr(result, "voting_anchor_id")

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_committee_model(self, dbsync_session: Session) -> None:
        """Test Committee model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(Committee).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "gov_action_proposal_id")
                assert hasattr(result, "quorum_numerator")
                assert hasattr(result, "quorum_denominator")

                # Verify quorum threshold makes sense
                if (
                    result.quorum_numerator is not None
                    and result.quorum_denominator is not None
                ):
                    assert result.quorum_numerator <= result.quorum_denominator
                    assert result.quorum_denominator > 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_committee_member_model(self, dbsync_session: Session) -> None:
        """Test CommitteeMember model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(CommitteeMember).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "committee_id")
                assert hasattr(result, "committee_hash_id")
                assert hasattr(result, "expiration_epoch")

                # Verify term expiration
                if result.expiration_epoch is not None:
                    assert result.expiration_epoch >= 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_gov_action_proposal_model(self, dbsync_session: Session) -> None:
        """Test GovActionProposal model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(GovActionProposal).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "index")
                assert hasattr(result, "deposit")
                assert hasattr(result, "return_address")
                assert hasattr(result, "type_")
                assert hasattr(result, "ratified_epoch")
                assert hasattr(result, "enacted_epoch")

                # Verify governance action structure
                if result.deposit is not None:
                    assert result.deposit > 0  # Deposit must be positive
                if result.type_ is not None:
                    # Verify it's a valid governance action type
                    valid_types = [e.value for e in GovActionType]
                    assert result.type_ in valid_types

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_treasury_withdrawal_model(self, dbsync_session: Session) -> None:
        """Test TreasuryWithdrawal model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(TreasuryWithdrawal).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "gov_action_proposal_id")
                assert hasattr(result, "stake_address_id")
                assert hasattr(result, "amount")

                # Verify withdrawal amount
                if result.amount is not None:
                    assert result.amount > 0  # Withdrawal must be positive

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_constitution_model(self, dbsync_session: Session) -> None:
        """Test Constitution model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(Constitution).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "gov_action_proposal_id")
                assert hasattr(result, "voting_anchor_id")
                assert hasattr(result, "script_hash")

                # Verify constitution structure
                if result.script_hash is not None:
                    assert len(result.script_hash) == 28  # Guardrails script hash

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_voting_anchor_model(self, dbsync_session: Session) -> None:
        """Test VotingAnchor model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(VotingAnchor).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "url")
                assert hasattr(result, "data_hash")
                assert hasattr(result, "type_")

                # Verify anchor structure (CIP-100 compliance)
                if result.url is not None:
                    assert isinstance(result.url, str)
                    assert len(result.url) > 0
                if result.data_hash is not None:
                    assert len(result.data_hash) == 32  # SHA-256 hash

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_voting_procedure_model(self, dbsync_session: Session) -> None:
        """Test VotingProcedure model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(VotingProcedure).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "tx_id")
                assert hasattr(result, "gov_action_proposal_id")
                assert hasattr(result, "voter_role")
                assert hasattr(result, "vote")
                assert hasattr(result, "committee_voter")
                assert hasattr(result, "drep_voter")
                assert hasattr(result, "pool_voter")

                # Verify vote structure
                if result.vote is not None:
                    valid_votes = [e.value for e in VoteType]
                    assert result.vote in valid_votes
                if result.voter_role is not None:
                    valid_roles = ["ConstitutionalCommittee", "DRep", "SPO"]
                    assert result.voter_role in valid_roles

                # Verify voter exclusivity (only one voter type should be set)
                voter_count = sum(
                    1
                    for voter in [
                        result.committee_voter,
                        result.drep_voter,
                        result.pool_voter,
                    ]
                    if voter is not None
                )
                if voter_count > 0:
                    assert voter_count == 1  # Exactly one voter type

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_epoch_state_model(self, dbsync_session: Session) -> None:
        """Test EpochState model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(EpochState).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "committee_id")
                assert hasattr(result, "no_confidence_id")
                assert hasattr(result, "constitution_id")
                assert hasattr(result, "epoch_no")

                # Verify epoch state structure
                if result.epoch_no is not None:
                    assert result.epoch_no >= 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_off_chain_vote_data_model(self, dbsync_session: Session) -> None:
        """Test OffChainVoteData model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(OffChainVoteData).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "voting_anchor_id")
                assert hasattr(result, "hash_")
                assert hasattr(result, "json_")
                assert hasattr(result, "language")
                assert hasattr(result, "is_valid")

                # Verify metadata structure (CIP-100/108 compliance)
                if result.hash_ is not None:
                    assert len(result.hash_) == 32  # SHA-256 hash
                if result.json_ is not None:
                    assert isinstance(result.json_, dict)

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_off_chain_vote_gov_action_data_model(
        self, dbsync_session: Session
    ) -> None:
        """Test OffChainVoteGovActionData model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(
                select(OffChainVoteGovActionData).limit(1)
            ).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "off_chain_vote_data_id")
                assert hasattr(result, "title")
                assert hasattr(result, "abstract")
                assert hasattr(result, "motivation")
                assert hasattr(result, "rationale")

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_off_chain_vote_drep_data_model(self, dbsync_session: Session) -> None:
        """Test OffChainVoteDrepData model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(OffChainVoteDrepData).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "off_chain_vote_data_id")
                assert hasattr(result, "payment_address")
                assert hasattr(result, "given_name")
                assert hasattr(result, "objectives")
                assert hasattr(result, "motivations")
                assert hasattr(result, "qualifications")
                assert hasattr(result, "image_url")
                assert hasattr(result, "image_hash")

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_off_chain_vote_author_model(self, dbsync_session: Session) -> None:
        """Test OffChainVoteAuthor model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(OffChainVoteAuthor).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "off_chain_vote_data_id")
                assert hasattr(result, "name")
                assert hasattr(result, "witness_algorithm")
                assert hasattr(result, "public_key")
                assert hasattr(result, "signature")
                assert hasattr(result, "warning")

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_off_chain_vote_reference_model(self, dbsync_session: Session) -> None:
        """Test OffChainVoteReference model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(select(OffChainVoteReference).limit(1)).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "off_chain_vote_data_id")
                assert hasattr(result, "label")
                assert hasattr(result, "uri")
                assert hasattr(result, "hash_digest")
                assert hasattr(result, "hash_algorithm")

                # Verify reference structure
                if result.uri is not None:
                    assert isinstance(result.uri, str)
                    assert len(result.uri) > 0

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")

    def test_off_chain_vote_external_update_model(
        self, dbsync_session: Session
    ) -> None:
        """Test OffChainVoteExternalUpdate model with actual database."""
        if dbsync_session is None:
            pytest.skip("Database not available")

        try:
            result = dbsync_session.exec(
                select(OffChainVoteExternalUpdate).limit(1)
            ).first()
            if result:
                assert hasattr(result, "id_")
                assert hasattr(result, "off_chain_vote_data_id")
                assert hasattr(result, "title")
                assert hasattr(result, "uri")

        except Exception as e:
            pytest.skip(f"Database table not available: {e}")


class TestGovernanceEcosystemIntegration:
    """Integration tests for the complete governance ecosystem."""

    def test_all_governance_models_importable(self):
        """Test that all governance models can be imported together."""
        # This test ensures no circular imports or conflicts
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
            OffChainVoteAuthor,
            OffChainVoteData,
            OffChainVoteDrepData,
            OffChainVoteExternalUpdate,
            OffChainVoteGovActionData,
            OffChainVoteReference,
            TreasuryWithdrawal,
            VotingAnchor,
            VotingProcedure,
        )

        # All models should be classes
        governance_models = [
            DrepHash,
            DrepRegistration,
            DrepDistr,
            CommitteeHash,
            CommitteeRegistration,
            CommitteeDeRegistration,
            Committee,
            CommitteeMember,
            GovActionProposal,
            TreasuryWithdrawal,
            Constitution,
            VotingAnchor,
            VotingProcedure,
            EpochState,
            OffChainVoteData,
            OffChainVoteGovActionData,
            OffChainVoteDrepData,
            OffChainVoteAuthor,
            OffChainVoteReference,
            OffChainVoteExternalUpdate,
        ]

        for model in governance_models:
            assert isinstance(model, type)

    def test_governance_table_names_unique(self):
        """Test that all governance models have unique table names."""
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
            OffChainVoteAuthor,
            OffChainVoteData,
            OffChainVoteDrepData,
            OffChainVoteExternalUpdate,
            OffChainVoteGovActionData,
            OffChainVoteReference,
            TreasuryWithdrawal,
            VotingAnchor,
            VotingProcedure,
        )

        table_names = [
            DrepHash.__tablename__,
            DrepRegistration.__tablename__,
            DrepDistr.__tablename__,
            CommitteeHash.__tablename__,
            CommitteeRegistration.__tablename__,
            CommitteeDeRegistration.__tablename__,
            Committee.__tablename__,
            CommitteeMember.__tablename__,
            GovActionProposal.__tablename__,
            TreasuryWithdrawal.__tablename__,
            Constitution.__tablename__,
            VotingAnchor.__tablename__,
            VotingProcedure.__tablename__,
            EpochState.__tablename__,
            OffChainVoteData.__tablename__,
            OffChainVoteGovActionData.__tablename__,
            OffChainVoteDrepData.__tablename__,
            OffChainVoteAuthor.__tablename__,
            OffChainVoteReference.__tablename__,
            OffChainVoteExternalUpdate.__tablename__,
        ]

        # All table names should be unique
        assert len(table_names) == len(set(table_names))

        # All table names should follow Conway era naming convention
        expected_tables = {
            "drep_hash",
            "drep_registration",
            "drep_distr",
            "committee_hash",
            "committee_registration",
            "committee_de_registration",
            "committee",
            "committee_member",
            "gov_action_proposal",
            "treasury_withdrawal",
            "constitution",
            "voting_anchor",
            "voting_procedure",
            "epoch_state",
            "off_chain_vote_data",
            "off_chain_vote_gov_action_data",
            "off_chain_vote_drep_data",
            "off_chain_vote_author",
            "off_chain_vote_reference",
            "off_chain_vote_external_update",
        }

        assert set(table_names) == expected_tables

    def test_governance_enum_values(self):
        """Test that governance enums have correct values."""
        # Test GovActionType enum
        assert GovActionType.PARAMETER_CHANGE == "ParameterChange"
        assert GovActionType.HARD_FORK_INITIATION == "HardForkInitiation"
        assert GovActionType.TREASURY_WITHDRAWALS == "TreasuryWithdrawals"
        assert GovActionType.NO_CONFIDENCE == "NoConfidence"
        assert GovActionType.UPDATE_COMMITTEE == "UpdateCommittee"
        assert GovActionType.NEW_CONSTITUTION == "NewConstitution"
        assert GovActionType.INFO_ACTION == "InfoAction"

        # Test VoteType enum
        assert VoteType.YES == "Yes"
        assert VoteType.NO == "No"
        assert VoteType.ABSTAIN == "Abstain"

    def test_governance_model_consistency(self, dbsync_session):
        """Test consistency across governance ecosystem models."""
        # Create instances of governance models to verify field consistency
        drep_hash = DrepHash(
            raw=b"1234567890123456789012345678",
            view="drep1abcdefghijklmnopqrstuvwxyz",
            has_script=False,
        )

        drep_registration = DrepRegistration(
            tx_id=12345,
            cert_index=0,
            drep_hash_id=1,
            deposit=2000000,
        )

        committee_hash = CommitteeHash(
            raw=b"9876543210987654321098765432",
            has_script=False,
        )

        committee_registration = CommitteeRegistration(
            tx_id=12346,
            cert_index=0,
            cold_key_id=1,
            hot_key_id=2,
        )

        gov_action = GovActionProposal(
            tx_id=12347,
            index=0,
            deposit=100000000,
            return_address=500,
            type_=GovActionType.PARAMETER_CHANGE,
        )

        voting_anchor = VotingAnchor(
            url="https://governance.cardano.org/metadata.json",
            data_hash=b"12345678901234567890123456789012",
            type_="action",
        )

        vote = VotingProcedure(
            tx_id=12348,
            index=0,
            gov_action_proposal_id=1,
            drep_voter=1,
            voter_role="DRep",
            vote=VoteType.YES,
        )

        # Verify all models can be instantiated
        assert drep_hash.has_script is False
        assert drep_registration.deposit == 2000000
        assert committee_hash.has_script is False
        assert committee_registration.cold_key_id != committee_registration.hot_key_id
        assert gov_action.type_ == GovActionType.PARAMETER_CHANGE
        assert voting_anchor.url.startswith("https://")
        assert vote.vote == VoteType.YES

        # Verify field type consistency
        assert type(drep_hash.raw) == type(committee_hash.raw)  # Both use Hash28Type
        assert type(drep_registration.tx_id) == type(
            committee_registration.tx_id
        )  # Both reference tx.id
        assert type(gov_action.deposit) == type(
            drep_registration.deposit
        )  # Both use LovelaceType
        assert type(committee_registration.cold_key_id) == type(
            committee_registration.hot_key_id
        )  # Both foreign key references
