"""Unit tests for governance queries module."""

from unittest.mock import Mock

import pytest

from src.dbsync.examples.queries.governance import (
    GovernanceQueries,
    get_comprehensive_governance_analysis,
)


class TestGovernanceQueries:
    """Test suite for GovernanceQueries class."""

    def test_get_governance_proposal_analysis_success(self) -> None:
        """Test successful governance proposal analysis."""
        mock_session = Mock()

        # Mock proposal query results
        mock_proposals = [
            Mock(
                id_=1,
                tx_id=100,
                index=0,
                action_type="TreasuryWithdrawals",
                deposit=500000000,
                return_address="addr1test123",
                ratified_epoch=None,
                enacted_epoch=None,
                dropped_epoch=None,
                expired_epoch=None,
                proposal_time="2024-01-01 12:00:00",
                proposal_epoch=450,
                anchor_url="https://example.com/proposal.json",
                anchor_hash=b"hash123",
            ),
        ]

        # Mock statistics
        mock_stats = Mock(
            total_proposals=10,
            ratified_count=3,
            enacted_count=2,
            dropped_count=1,
            expired_count=0,
            total_deposits=5000000000,
        )

        # Mock type distribution
        mock_types = [
            Mock(type_="TreasuryWithdrawals", count=5),
            Mock(type_="ParameterChange", count=3),
            Mock(type_="HardForkInitiation", count=2),
        ]

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_proposals),  # proposals query
            Mock(first=lambda: mock_stats),  # status statistics
            Mock(all=lambda: mock_types),  # type distribution
        ]

        result = GovernanceQueries.get_governance_proposal_analysis(
            mock_session, None, 20
        )

        assert result["found"] is True
        assert result["proposals_analyzed"] == 1
        assert len(result["proposals"]) == 1

        proposal = result["proposals"][0]
        assert proposal["action_type"] == "TreasuryWithdrawals"
        assert proposal["status"] == "Active"
        assert proposal["deposit_lovelace"] == 500000000

        stats = result["statistics"]
        assert stats["total_proposals"] == 10
        assert stats["ratified_count"] == 3
        assert stats["ratification_rate"] == 0.3

    def test_get_governance_proposal_analysis_specific_proposal(self) -> None:
        """Test proposal analysis for specific proposal ID."""
        mock_session = Mock()

        mock_proposals = [
            Mock(
                id_=5,
                tx_id=200,
                index=1,
                action_type="ParameterChange",
                deposit=1000000000,
                return_address="addr1test456",
                ratified_epoch=451,
                enacted_epoch=452,
                dropped_epoch=None,
                expired_epoch=None,
                proposal_time="2024-01-15 14:30:00",
                proposal_epoch=451,
                anchor_url=None,
                anchor_hash=None,
            ),
        ]

        mock_stats = Mock(
            total_proposals=1,
            ratified_count=1,
            enacted_count=1,
            dropped_count=0,
            expired_count=0,
            total_deposits=1000000000,
        )

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_proposals),
            Mock(first=lambda: mock_stats),
            Mock(all=lambda: []),
        ]

        result = GovernanceQueries.get_governance_proposal_analysis(mock_session, 5, 20)

        assert result["found"] is True
        assert result["proposal_id"] == 5
        proposal = result["proposals"][0]
        assert proposal["status"] == "Enacted"
        assert proposal["ratified_epoch"] == 451
        assert proposal["enacted_epoch"] == 452

    def test_get_governance_proposal_analysis_not_found(self) -> None:
        """Test proposal analysis for non-existent proposal."""
        mock_session = Mock()
        mock_session.execute.return_value.all.return_value = []

        result = GovernanceQueries.get_governance_proposal_analysis(
            mock_session, 999, 20
        )

        assert result["found"] is False
        assert result["proposal_id"] == 999
        assert "error" in result

    def test_get_drep_activity_monitoring_success(self) -> None:
        """Test successful DRep activity monitoring."""
        mock_session = Mock()

        # Mock DRep registration data
        mock_drep_registrations = [
            Mock(
                id_=1,
                drep_id="drep1test123",
                drep_hash=b"drep_hash_1",
                deposit=500000000,
                registration_time="2024-01-01 10:00:00",
                registration_epoch=450,
                anchor_url="https://drep.example.com/metadata.json",
                anchor_hash=b"anchor_hash_1",
            ),
        ]

        # Mock statistics
        mock_drep_stats = Mock(
            total_dreps=25,
            total_deposits=12500000000,
            avg_deposit=500000000,
        )

        # Mock delegation stats
        mock_delegation_stats = [
            Mock(
                drep_id="drep1test123",
                delegator_count=150,
                total_stake=50000000000,
            ),
        ]

        # Mock voting activity
        mock_voting_activity = [
            Mock(
                drep_id="drep1test123",
                vote_count=10,
                vote_type="Yes",
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_drep_registrations),
            Mock(first=lambda: mock_drep_stats),
            Mock(all=lambda: mock_delegation_stats),
            Mock(all=lambda: mock_voting_activity),
        ]

        result = GovernanceQueries.get_drep_activity_monitoring(mock_session, None, 20)

        assert result["found"] is True
        assert result["dreps_analyzed"] == 1
        assert len(result["drep_registrations"]) == 1

        drep = result["drep_registrations"][0]
        assert drep["drep_id"] == "drep1test123"
        assert drep["deposit_lovelace"] == 500000000

        stats = result["statistics"]
        assert stats["total_dreps"] == 25
        assert stats["avg_deposit_lovelace"] == 500000000

    def test_get_drep_activity_monitoring_specific_drep(self) -> None:
        """Test DRep monitoring for specific DRep ID."""
        mock_session = Mock()

        mock_drep_registrations = [
            Mock(
                id_=2,
                drep_id="drep2specific",
                drep_hash=b"drep_hash_2",
                deposit=750000000,
                registration_time="2024-01-10 15:30:00",
                registration_epoch=451,
                anchor_url=None,
                anchor_hash=None,
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_drep_registrations),
            Mock(
                first=lambda: Mock(
                    total_dreps=1, total_deposits=750000000, avg_deposit=750000000
                )
            ),
            Mock(all=lambda: []),
            Mock(all=lambda: []),
        ]

        result = GovernanceQueries.get_drep_activity_monitoring(
            mock_session, "drep2specific", 20
        )

        assert result["found"] is True
        assert result["drep_id"] == "drep2specific"
        assert len(result["drep_registrations"]) == 1

    def test_get_drep_activity_monitoring_not_found(self) -> None:
        """Test DRep monitoring for non-existent DRep."""
        mock_session = Mock()
        mock_session.execute.return_value.all.return_value = []

        result = GovernanceQueries.get_drep_activity_monitoring(
            mock_session, "nonexistent_drep", 20
        )

        assert result["found"] is False
        assert result["drep_id"] == "nonexistent_drep"
        assert "error" in result

    def test_get_committee_operations_tracking_success(self) -> None:
        """Test successful committee operations tracking."""
        mock_session = Mock()

        # Mock committee registrations
        mock_registrations = [
            Mock(
                id_=1,
                cold_key=b"committee_cold_key_1",
                cold_key_view="committee1view",
                anchor_url="https://committee.example.com/info.json",
                registration_time="2024-01-01 09:00:00",
                registration_epoch=450,
            ),
        ]

        # Mock committee deregistrations
        mock_deregistrations = []

        # Mock committee members
        mock_members = [
            Mock(
                id_=1,
                cold_key=b"committee_cold_key_1",
                cold_key_view="committee1view",
                expiration_epoch=500,
            ),
        ]

        # Mock voting activity
        mock_votes = [
            Mock(
                committee_member="committee1view",
                vote_count=5,
                vote_type="Yes",
            ),
        ]

        # Mock statistics
        mock_stats = Mock(
            total_members=7,
            total_registrations=8,
            total_deregistrations=1,
        )

        mock_session.execute.side_effect = [
            Mock(all=lambda: mock_registrations),
            Mock(all=lambda: mock_deregistrations),
            Mock(all=lambda: mock_members),
            Mock(all=lambda: mock_votes),
            Mock(first=lambda: mock_stats),
        ]

        result = GovernanceQueries.get_committee_operations_tracking(
            mock_session, None, 20
        )

        assert result["found"] is True
        assert len(result["registrations"]) == 1
        assert len(result["deregistrations"]) == 0
        assert len(result["current_members"]) == 1

        stats = result["statistics"]
        assert stats["total_members"] == 7
        assert stats["active_members"] == 7  # registrations - deregistrations

    def test_get_treasury_governance_analysis_success(self) -> None:
        """Test successful treasury governance analysis."""
        mock_session = Mock()

        # Mock treasury withdrawals
        mock_withdrawals = [
            Mock(
                id_=1,
                stake_address="stake1test123",
                amount=1000000000,
                withdrawal_time="2024-01-01 12:00:00",
                withdrawal_epoch=450,
                proposal_index=0,
            ),
        ]

        # Mock withdrawal statistics
        mock_withdrawal_stats = Mock(
            total_withdrawals=5,
            total_amount=5000000000,
            avg_amount=1000000000,
            max_amount=2000000000,
            unique_recipients=3,
        )

        # Mock treasury proposals
        mock_proposals = [
            Mock(
                id_=100,
                index=0,
                total_withdrawal=1000000000,
                withdrawal_count=1,
                proposal_time="2024-01-01 11:00:00",
                proposal_epoch=450,
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(scalar=lambda: "2024-01-15 12:00:00"),  # latest block
            Mock(scalar=lambda: 100000),  # latest slot
            Mock(all=lambda: mock_withdrawals),  # withdrawals
            Mock(first=lambda: mock_withdrawal_stats),  # withdrawal stats
            Mock(all=lambda: mock_proposals),  # treasury proposals
        ]

        result = GovernanceQueries.get_treasury_governance_analysis(
            mock_session, 90, 20
        )

        assert result["found"] is True
        assert result["analysis_period_days"] == 90

        stats = result["statistics"]
        assert stats["total_withdrawals"] == 5
        assert stats["total_amount_lovelace"] == 5000000000
        assert stats["unique_recipients"] == 3

        assert len(result["recent_withdrawals"]) == 1
        assert len(result["top_proposals"]) == 1

    def test_get_treasury_governance_analysis_no_data(self) -> None:
        """Test treasury analysis with no block data."""
        mock_session = Mock()
        mock_session.execute.return_value.scalar.return_value = None

        result = GovernanceQueries.get_treasury_governance_analysis(
            mock_session, 90, 20
        )

        assert result["found"] is False
        assert "error" in result

    def test_get_voting_participation_metrics_success(self) -> None:
        """Test successful voting participation metrics."""
        mock_session = Mock()

        # Mock voting statistics
        mock_voting_stats = Mock(
            total_votes=150,
            proposals_voted_on=10,
            unique_drep_voters=25,
            unique_committee_voters=7,
            unique_pool_voters=50,
        )

        # Mock vote distribution
        mock_vote_distribution = [
            Mock(vote_type="Yes", count=75),
            Mock(vote_type="No", count=50),
            Mock(vote_type="Abstain", count=25),
        ]

        # Mock active DRep voters
        mock_active_dreps = [
            Mock(drep_id="drep1active", vote_count=10),
            Mock(drep_id="drep2active", vote_count=8),
        ]

        # Mock proposal voting
        mock_proposal_voting = [
            Mock(
                proposal_id=1,
                proposal_index=0,
                action_type="TreasuryWithdrawals",
                total_votes=25,
                yes_votes=15,
                no_votes=8,
                abstain_votes=2,
            ),
        ]

        mock_session.execute.side_effect = [
            Mock(scalar=lambda: 100000),  # latest slot
            Mock(first=lambda: mock_voting_stats),  # voting stats
            Mock(all=lambda: mock_vote_distribution),  # vote distribution
            Mock(all=lambda: mock_active_dreps),  # active DReps
            Mock(all=lambda: mock_proposal_voting),  # proposal voting
        ]

        result = GovernanceQueries.get_voting_participation_metrics(
            mock_session, 30, 20
        )

        assert result["found"] is True
        assert result["analysis_period_days"] == 30

        stats = result["overall_statistics"]
        assert stats["total_votes"] == 150
        assert stats["unique_drep_voters"] == 25

        assert len(result["vote_distribution"]) == 3
        assert len(result["most_active_drep_voters"]) == 2
        assert len(result["proposal_voting_summary"]) == 1

    def test_async_not_implemented(self) -> None:
        """Test that async methods raise NotImplementedError."""
        from sqlalchemy.ext.asyncio import AsyncSession

        mock_async_session = Mock(spec=AsyncSession)

        with pytest.raises(NotImplementedError):
            GovernanceQueries.get_governance_proposal_analysis(mock_async_session)

        with pytest.raises(NotImplementedError):
            GovernanceQueries.get_drep_activity_monitoring(mock_async_session)

        with pytest.raises(NotImplementedError):
            GovernanceQueries.get_committee_operations_tracking(mock_async_session)

        with pytest.raises(NotImplementedError):
            GovernanceQueries.get_treasury_governance_analysis(mock_async_session)

        with pytest.raises(NotImplementedError):
            GovernanceQueries.get_voting_participation_metrics(mock_async_session)


class TestComprehensiveGovernanceAnalysis:
    """Test suite for comprehensive governance analysis function."""

    def test_comprehensive_analysis_success(self) -> None:
        """Test successful comprehensive governance analysis."""
        mock_session = Mock()

        # Create a mock instance of GovernanceQueries
        mock_queries = Mock()

        # Mock the return values for each method
        mock_proposal_analysis = {
            "found": True,
            "statistics": {"total_proposals": 10},
        }

        mock_drep_activity = {
            "found": True,
            "statistics": {"total_dreps": 25},
        }

        mock_committee_operations = {
            "found": True,
            "statistics": {"active_members": 7},
        }

        mock_treasury_analysis = {
            "found": True,
            "statistics": {"total_withdrawals": 5},
        }

        mock_voting_metrics = {
            "found": True,
            "overall_statistics": {"total_votes": 150},
        }

        mock_queries.get_governance_proposal_analysis.return_value = (
            mock_proposal_analysis
        )
        mock_queries.get_drep_activity_monitoring.return_value = mock_drep_activity
        mock_queries.get_committee_operations_tracking.return_value = (
            mock_committee_operations
        )
        mock_queries.get_treasury_governance_analysis.return_value = (
            mock_treasury_analysis
        )
        mock_queries.get_voting_participation_metrics.return_value = mock_voting_metrics

        # Mock the GovernanceQueries class instantiation
        original_queries = GovernanceQueries
        GovernanceQueries.__new__ = lambda cls: mock_queries

        try:
            result = get_comprehensive_governance_analysis(
                mock_session, 1, "drep1test", "committee1", 30
            )

            assert result["found"] is True
            assert result["analysis_parameters"]["proposal_id"] == 1
            assert result["analysis_parameters"]["drep_id"] == "drep1test"
            assert result["analysis_parameters"]["committee_member"] == "committee1"
            assert result["analysis_parameters"]["analysis_period_days"] == 30

            assert "summary" in result
            assert result["summary"]["total_proposals"] == 10
            assert result["summary"]["total_dreps"] == 25
            assert result["summary"]["active_committee_members"] == 7
            assert result["summary"]["treasury_withdrawals"] == 5
            assert result["summary"]["total_votes"] == 150

            assert "proposal_analysis" in result
            assert "drep_activity" in result
            assert "committee_operations" in result
            assert "treasury_analysis" in result
            assert "voting_metrics" in result

        finally:
            # Restore the original class
            GovernanceQueries.__new__ = original_queries.__new__

    def test_comprehensive_analysis_exception(self) -> None:
        """Test comprehensive analysis with exception."""
        mock_session = Mock()

        # Mock an exception during analysis
        mock_queries = Mock()
        mock_queries.get_governance_proposal_analysis.side_effect = Exception(
            "Database error"
        )

        original_queries = GovernanceQueries
        GovernanceQueries.__new__ = lambda cls: mock_queries

        try:
            result = get_comprehensive_governance_analysis(
                mock_session, None, None, None, 30
            )

            assert result["found"] is False
            assert "error" in result
            assert "Database error" in result["error"]
            assert result["analysis_parameters"]["analysis_period_days"] == 30

        finally:
            GovernanceQueries.__new__ = original_queries.__new__


# Additional edge case tests
class TestGovernanceEdgeCases:
    """Test edge cases and error conditions."""

    def test_proposal_status_determination(self) -> None:
        """Test correct proposal status determination logic."""
        mock_session = Mock()

        # Test various proposal states
        test_cases = [
            # (ratified_epoch, enacted_epoch, dropped_epoch, expired_epoch, expected_status)
            (None, None, None, None, "Active"),
            (450, None, None, None, "Ratified"),
            (450, 451, None, None, "Enacted"),
            (None, None, 449, None, "Dropped"),
            (None, None, None, 452, "Expired"),
        ]

        for ratified, enacted, dropped, expired, expected_status in test_cases:
            mock_proposals = [
                Mock(
                    id_=1,
                    tx_id=100,
                    index=0,
                    action_type="TreasuryWithdrawals",
                    deposit=500000000,
                    return_address="addr1test123",
                    ratified_epoch=ratified,
                    enacted_epoch=enacted,
                    dropped_epoch=dropped,
                    expired_epoch=expired,
                    proposal_time="2024-01-01 12:00:00",
                    proposal_epoch=450,
                    anchor_url=None,
                    anchor_hash=None,
                ),
            ]

            mock_session.execute.side_effect = [
                Mock(all=lambda: mock_proposals),
                Mock(
                    first=lambda: Mock(
                        total_proposals=1,
                        ratified_count=0,
                        enacted_count=0,
                        dropped_count=0,
                        expired_count=0,
                        total_deposits=500000000,
                    )
                ),
                Mock(all=lambda: []),
            ]

            result = GovernanceQueries.get_governance_proposal_analysis(
                mock_session, None, 20
            )

            assert result["found"] is True
            assert result["proposals"][0]["status"] == expected_status

    def test_zero_division_protection(self) -> None:
        """Test protection against zero division in percentage calculations."""
        mock_session = Mock()

        # Mock zero totals
        mock_stats = Mock(
            total_proposals=0,
            ratified_count=0,
            enacted_count=0,
            dropped_count=0,
            expired_count=0,
            total_deposits=0,
        )

        mock_session.execute.side_effect = [
            Mock(all=lambda: []),
            Mock(first=lambda: mock_stats),
            Mock(all=lambda: []),
        ]

        result = GovernanceQueries.get_governance_proposal_analysis(
            mock_session, None, 20
        )

        assert result["found"] is True
        assert result["statistics"]["ratification_rate"] == 0.0
        assert result["statistics"]["enactment_rate"] == 0.0
