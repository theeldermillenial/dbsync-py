"""Conway Era Governance Utilities Query Examples.

This example demonstrates how to use the dbsync-py package to implement
Conway era governance queries for Cardano's on-chain governance features.
"""

from typing import Any

from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ...models import (
    Block,
    CommitteeDeRegistration,
    CommitteeHash,
    CommitteeMember,
    CommitteeRegistration,
    DrepDistr,
    DrepHash,
    DrepRegistration,
    GovActionProposal,
    StakeAddress,
    TreasuryWithdrawal,
    VotingAnchor,
    VotingProcedure,
)


class GovernanceQueries:
    """Example Conway era governance query utilities."""

    @staticmethod
    def get_governance_proposal_analysis(
        session: Session | AsyncSession, proposal_id: int | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Analyze governance action proposals and their lifecycle."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Base query for governance proposals
        proposals_stmt = select(
            GovActionProposal.id_,
            GovActionProposal.tx_id,
            GovActionProposal.index,
            GovActionProposal.deposit,
            GovActionProposal.return_address,
            GovActionProposal.ratified_epoch,
            GovActionProposal.enacted_epoch,
            GovActionProposal.dropped_epoch,
            GovActionProposal.expired_epoch,
            GovActionProposal.type_.label("action_type"),
            VotingAnchor.url.label("anchor_url"),
            VotingAnchor.data_hash.label("anchor_hash"),
            Block.time.label("proposal_time"),
            Block.epoch_no.label("proposal_epoch"),
        ).select_from(
            GovActionProposal.__table__.outerjoin(
                VotingAnchor.__table__,
                GovActionProposal.voting_anchor_id == VotingAnchor.id_,
            ).join(Block.__table__, GovActionProposal.tx_id == Block.id_)
        )

        if proposal_id:
            proposals_stmt = proposals_stmt.where(GovActionProposal.id_ == proposal_id)

        proposals_stmt = proposals_stmt.order_by(desc(GovActionProposal.id_)).limit(
            limit
        )

        proposals = session.execute(proposals_stmt).all()

        if proposal_id and not proposals:
            return {
                "found": False,
                "proposal_id": proposal_id,
                "error": "Governance proposal not found",
            }

        # Get proposal status statistics
        status_stats = session.execute(
            select(
                func.count(GovActionProposal.id_).label("total_proposals"),
                func.count(GovActionProposal.ratified_epoch).label("ratified_count"),
                func.count(GovActionProposal.enacted_epoch).label("enacted_count"),
                func.count(GovActionProposal.dropped_epoch).label("dropped_count"),
                func.count(GovActionProposal.expired_epoch).label("expired_count"),
                func.sum(GovActionProposal.deposit).label("total_deposits"),
            )
        ).first()

        # Get proposal type distribution
        type_distribution = session.execute(
            select(
                GovActionProposal.type_,
                func.count(GovActionProposal.id_).label("count"),
            )
            .group_by(GovActionProposal.type_)
            .order_by(desc(func.count(GovActionProposal.id_)))
        ).all()

        # Process proposal data
        proposal_list = []
        for row in proposals:
            # Determine proposal status
            status = "Active"
            if row.enacted_epoch:
                status = "Enacted"
            elif row.ratified_epoch:
                status = "Ratified"
            elif row.dropped_epoch:
                status = "Dropped"
            elif row.expired_epoch:
                status = "Expired"

            proposal_list.append(
                {
                    "id": row.id_,
                    "tx_id": row.tx_id,
                    "index": row.index,
                    "action_type": row.action_type,
                    "status": status,
                    "deposit_lovelace": int(row.deposit or 0),
                    "return_address": row.return_address,
                    "proposal_time": (
                        str(row.proposal_time) if row.proposal_time else None
                    ),
                    "proposal_epoch": row.proposal_epoch,
                    "ratified_epoch": row.ratified_epoch,
                    "enacted_epoch": row.enacted_epoch,
                    "dropped_epoch": row.dropped_epoch,
                    "expired_epoch": row.expired_epoch,
                    "anchor_url": row.anchor_url,
                    "anchor_hash": row.anchor_hash.hex() if row.anchor_hash else None,
                }
            )

        return {
            "found": True,
            "proposal_id": proposal_id,
            "proposals_analyzed": len(proposal_list),
            "proposals": proposal_list,
            "statistics": {
                "total_proposals": int(status_stats.total_proposals or 0),
                "ratified_count": int(status_stats.ratified_count or 0),
                "enacted_count": int(status_stats.enacted_count or 0),
                "dropped_count": int(status_stats.dropped_count or 0),
                "expired_count": int(status_stats.expired_count or 0),
                "total_deposits_lovelace": int(status_stats.total_deposits or 0),
                "ratification_rate": (status_stats.ratified_count or 0)
                / max(status_stats.total_proposals or 1, 1),
                "enactment_rate": (status_stats.enacted_count or 0)
                / max(status_stats.total_proposals or 1, 1),
            },
            "type_distribution": [
                {
                    "action_type": row.type_,
                    "count": int(row.count),
                    "percentage": int(row.count)
                    / max(status_stats.total_proposals or 1, 1)
                    * 100,
                }
                for row in type_distribution
            ],
        }

    @staticmethod
    def get_drep_activity_monitoring(
        session: Session | AsyncSession, drep_id: str | None = None, limit: int = 20
    ) -> dict[str, Any]:
        """Track DRep registrations, delegations, and voting activity."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Base query for DRep registrations
        drep_stmt = select(
            DrepRegistration.id_,
            DrepRegistration.tx_id,
            DrepRegistration.cert_index,
            DrepRegistration.deposit,
            DrepHash.view.label("drep_id"),
            DrepHash.raw.label("drep_hash"),
            VotingAnchor.url.label("anchor_url"),
            VotingAnchor.data_hash.label("anchor_hash"),
            Block.time.label("registration_time"),
            Block.epoch_no.label("registration_epoch"),
        ).select_from(
            DrepRegistration.__table__.join(
                DrepHash.__table__, DrepRegistration.drep_hash_id == DrepHash.id_
            )
            .outerjoin(
                VotingAnchor.__table__,
                DrepRegistration.voting_anchor_id == VotingAnchor.id_,
            )
            .join(Block.__table__, DrepRegistration.tx_id == Block.id_)
        )

        if drep_id:
            drep_stmt = drep_stmt.where(DrepHash.view == drep_id)

        drep_stmt = drep_stmt.order_by(desc(DrepRegistration.id_)).limit(limit)

        drep_registrations = session.execute(drep_stmt).all()

        if drep_id and not drep_registrations:
            return {
                "found": False,
                "drep_id": drep_id,
                "error": "DRep not found",
            }

        # Get DRep statistics
        drep_stats = session.execute(
            select(
                func.count(func.distinct(DrepRegistration.drep_hash_id)).label(
                    "total_dreps"
                ),
                func.sum(DrepRegistration.deposit).label("total_deposits"),
                func.avg(DrepRegistration.deposit).label("avg_deposit"),
            )
        ).first()

        # Get delegation distribution for DReps
        delegation_stats = session.execute(
            select(
                DrepHash.view.label("drep_id"),
                func.count(DrepDistr.hash_id).label("delegator_count"),
                func.sum(DrepDistr.amount).label("total_stake"),
            )
            .select_from(
                DrepDistr.__table__.join(
                    DrepHash.__table__, DrepDistr.hash_id == DrepHash.id_
                )
            )
            .group_by(DrepHash.view)
            .order_by(desc(func.sum(DrepDistr.amount)))
            .limit(10)
        ).all()

        # Get voting activity
        voting_activity = session.execute(
            select(
                DrepHash.view.label("drep_id"),
                func.count(VotingProcedure.id_).label("vote_count"),
                VotingProcedure.vote.label("vote_type"),
            )
            .select_from(
                VotingProcedure.__table__.join(
                    DrepHash.__table__, VotingProcedure.drep_voter == DrepHash.id_
                )
            )
            .group_by(DrepHash.view, VotingProcedure.vote)
            .order_by(desc(func.count(VotingProcedure.id_)))
            .limit(20)
        ).all()

        # Process DRep data
        drep_list = []
        for row in drep_registrations:
            drep_list.append(
                {
                    "id": row.id_,
                    "drep_id": row.drep_id,
                    "drep_hash": row.drep_hash.hex() if row.drep_hash else None,
                    "deposit_lovelace": int(row.deposit or 0),
                    "registration_time": (
                        str(row.registration_time) if row.registration_time else None
                    ),
                    "registration_epoch": row.registration_epoch,
                    "anchor_url": row.anchor_url,
                    "anchor_hash": row.anchor_hash.hex() if row.anchor_hash else None,
                }
            )

        return {
            "found": True,
            "drep_id": drep_id,
            "dreps_analyzed": len(drep_list),
            "drep_registrations": drep_list,
            "statistics": {
                "total_dreps": int(drep_stats.total_dreps or 0),
                "total_deposits_lovelace": int(drep_stats.total_deposits or 0),
                "avg_deposit_lovelace": int(drep_stats.avg_deposit or 0),
            },
            "delegation_leaders": [
                {
                    "drep_id": row.drep_id,
                    "delegator_count": int(row.delegator_count),
                    "total_stake_lovelace": int(row.total_stake or 0),
                }
                for row in delegation_stats
            ],
            "voting_activity": [
                {
                    "drep_id": row.drep_id,
                    "vote_count": int(row.vote_count),
                    "vote_type": row.vote_type,
                }
                for row in voting_activity
            ],
        }

    @staticmethod
    def get_committee_operations_tracking(
        session: Session | AsyncSession,
        committee_member: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Monitor constitutional committee activities and decisions."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get committee registrations
        committee_registrations = session.execute(
            select(
                CommitteeRegistration.id_,
                CommitteeRegistration.tx_id,
                CommitteeRegistration.cert_index,
                CommitteeHash.raw.label("cold_key"),
                Block.time.label("registration_time"),
                Block.epoch_no.label("registration_epoch"),
            )
            .select_from(
                CommitteeRegistration.__table__.join(
                    CommitteeHash.__table__,
                    CommitteeRegistration.cold_key_id == CommitteeHash.id_,
                ).join(Block.__table__, CommitteeRegistration.tx_id == Block.id_)
            )
            .order_by(desc(CommitteeRegistration.id_))
            .limit(limit)
        ).all()

        # Get committee deregistrations
        committee_deregistrations = session.execute(
            select(
                CommitteeDeRegistration.id_,
                CommitteeDeRegistration.tx_id,
                CommitteeDeRegistration.cert_index,
                CommitteeHash.raw.label("cold_key"),
                VotingAnchor.url.label("anchor_url"),
                Block.time.label("deregistration_time"),
                Block.epoch_no.label("deregistration_epoch"),
            )
            .select_from(
                CommitteeDeRegistration.__table__.join(
                    CommitteeHash.__table__,
                    CommitteeDeRegistration.cold_key_id == CommitteeHash.id_,
                )
                .outerjoin(
                    VotingAnchor.__table__,
                    CommitteeDeRegistration.voting_anchor_id == VotingAnchor.id_,
                )
                .join(Block.__table__, CommitteeDeRegistration.tx_id == Block.id_)
            )
            .order_by(desc(CommitteeDeRegistration.id_))
            .limit(limit)
        ).all()

        # Get committee member information
        committee_members = session.execute(
            select(
                CommitteeMember.id_,
                CommitteeHash.raw.label("cold_key"),
                CommitteeMember.expiration_epoch,
            )
            .select_from(
                CommitteeMember.__table__.join(
                    CommitteeHash.__table__,
                    CommitteeMember.committee_hash_id == CommitteeHash.id_,
                )
            )
            .order_by(CommitteeMember.expiration_epoch.desc())
            .limit(limit)
        ).all()

        # Get committee voting activity
        committee_votes = session.execute(
            select(
                CommitteeHash.raw.label("committee_member"),
                func.count(VotingProcedure.id_).label("vote_count"),
                VotingProcedure.vote.label("vote_type"),
            )
            .select_from(
                VotingProcedure.__table__.join(
                    CommitteeHash.__table__,
                    VotingProcedure.committee_voter == CommitteeHash.id_,
                )
            )
            .group_by(CommitteeHash.raw, VotingProcedure.vote)
            .order_by(desc(func.count(VotingProcedure.id_)))
            .limit(20)
        ).all()

        # Get overall committee statistics
        committee_stats = session.execute(
            select(
                func.count(func.distinct(CommitteeMember.committee_hash_id)).label(
                    "total_members"
                ),
                func.count(func.distinct(CommitteeRegistration.cold_key_id)).label(
                    "total_registrations"
                ),
                func.count(func.distinct(CommitteeDeRegistration.cold_key_id)).label(
                    "total_deregistrations"
                ),
            )
        ).first()

        # Filter by specific committee member if requested
        if committee_member:
            # Convert hex string to bytes for comparison
            try:
                committee_member_bytes = bytes.fromhex(committee_member)
                committee_registrations = [
                    r
                    for r in committee_registrations
                    if r.cold_key == committee_member_bytes
                ]
                committee_deregistrations = [
                    r
                    for r in committee_deregistrations
                    if r.cold_key == committee_member_bytes
                ]
                committee_members = [
                    m for m in committee_members if m.cold_key == committee_member_bytes
                ]
                committee_votes = [
                    v
                    for v in committee_votes
                    if v.committee_member == committee_member_bytes
                ]
            except ValueError:
                return {
                    "found": False,
                    "committee_member": committee_member,
                    "error": "Invalid committee member format - expected hex string",
                }

            if not (
                committee_registrations
                or committee_deregistrations
                or committee_members
            ):
                return {
                    "found": False,
                    "committee_member": committee_member,
                    "error": "Committee member not found",
                }

        return {
            "found": True,
            "committee_member": committee_member,
            "statistics": {
                "total_members": int(committee_stats.total_members or 0),
                "total_registrations": int(committee_stats.total_registrations or 0),
                "total_deregistrations": int(
                    committee_stats.total_deregistrations or 0
                ),
                "active_members": max(
                    0,
                    (committee_stats.total_registrations or 0)
                    - (committee_stats.total_deregistrations or 0),
                ),
            },
            "registrations": [
                {
                    "id": row.id_,
                    "cold_key": row.cold_key.hex() if row.cold_key else None,
                    "anchor_url": None,  # CommitteeRegistration doesn't support voting anchors
                    "registration_time": (
                        str(row.registration_time) if row.registration_time else None
                    ),
                    "registration_epoch": row.registration_epoch,
                }
                for row in committee_registrations
            ],
            "deregistrations": [
                {
                    "id": row.id_,
                    "cold_key": row.cold_key.hex() if row.cold_key else None,
                    "anchor_url": row.anchor_url,
                    "deregistration_time": (
                        str(row.deregistration_time)
                        if row.deregistration_time
                        else None
                    ),
                    "deregistration_epoch": row.deregistration_epoch,
                }
                for row in committee_deregistrations
            ],
            "current_members": [
                {
                    "id": row.id_,
                    "cold_key": row.cold_key.hex() if row.cold_key else None,
                    "expiration_epoch": row.expiration_epoch,
                }
                for row in committee_members
            ],
            "voting_activity": [
                {
                    "committee_member": (
                        row.committee_member.hex()
                        if isinstance(row.committee_member, bytes)
                        else str(row.committee_member)
                        if row.committee_member
                        else None
                    ),
                    "vote_count": int(row.vote_count),
                    "vote_type": row.vote_type,
                }
                for row in committee_votes
            ],
        }

    @staticmethod
    def get_treasury_governance_analysis(
        session: Session | AsyncSession, days: int = 90, limit: int = 20
    ) -> dict[str, Any]:
        """Track treasury operations and governance spending."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get latest block for date filtering
        latest_block = session.execute(
            select(Block.time).order_by(desc(Block.time)).limit(1)
        ).scalar()

        if not latest_block:
            return {
                "found": False,
                "error": "No block data available",
            }

        # Calculate date range using slot approximation
        latest_slot = session.execute(select(func.max(Block.slot_no))).scalar() or 0

        slots_per_day = 4320  # Approximate slots per day
        start_slot = latest_slot - (days * slots_per_day)

        # Get treasury withdrawals
        treasury_withdrawals = session.execute(
            select(
                TreasuryWithdrawal.id_,
                TreasuryWithdrawal.gov_action_proposal_id,
                TreasuryWithdrawal.stake_address_id,
                TreasuryWithdrawal.amount,
                StakeAddress.view.label("stake_address"),
                Block.time.label("withdrawal_time"),
                Block.epoch_no.label("withdrawal_epoch"),
                GovActionProposal.index.label("proposal_index"),
            )
            .select_from(
                TreasuryWithdrawal.__table__.join(
                    StakeAddress.__table__,
                    TreasuryWithdrawal.stake_address_id == StakeAddress.id_,
                )
                .join(
                    GovActionProposal.__table__,
                    TreasuryWithdrawal.gov_action_proposal_id == GovActionProposal.id_,
                )
                .join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
            .order_by(desc(TreasuryWithdrawal.id_))
            .limit(limit)
        ).all()

        # Get treasury withdrawal statistics
        withdrawal_stats = session.execute(
            select(
                func.count(TreasuryWithdrawal.id_).label("total_withdrawals"),
                func.sum(TreasuryWithdrawal.amount).label("total_amount"),
                func.avg(TreasuryWithdrawal.amount).label("avg_amount"),
                func.max(TreasuryWithdrawal.amount).label("max_amount"),
                func.count(func.distinct(TreasuryWithdrawal.stake_address_id)).label(
                    "unique_recipients"
                ),
            )
            .select_from(
                TreasuryWithdrawal.__table__.join(
                    GovActionProposal.__table__,
                    TreasuryWithdrawal.gov_action_proposal_id == GovActionProposal.id_,
                ).join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
        ).first()

        # Get treasury proposals by amount
        treasury_proposals = session.execute(
            select(
                GovActionProposal.id_,
                GovActionProposal.index,
                func.sum(TreasuryWithdrawal.amount).label("total_withdrawal"),
                func.count(TreasuryWithdrawal.id_).label("withdrawal_count"),
                Block.time.label("proposal_time"),
                Block.epoch_no.label("proposal_epoch"),
            )
            .select_from(
                GovActionProposal.__table__.join(
                    TreasuryWithdrawal.__table__,
                    GovActionProposal.id_ == TreasuryWithdrawal.gov_action_proposal_id,
                ).join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
            .group_by(
                GovActionProposal.id_,
                GovActionProposal.index,
                Block.time,
                Block.epoch_no,
            )
            .order_by(desc(func.sum(TreasuryWithdrawal.amount)))
            .limit(10)
        ).all()

        return {
            "found": True,
            "analysis_period_days": days,
            "latest_slot": latest_slot,
            "start_slot": start_slot,
            "statistics": {
                "total_withdrawals": int(withdrawal_stats.total_withdrawals or 0),
                "total_amount_lovelace": int(withdrawal_stats.total_amount or 0),
                "avg_amount_lovelace": int(withdrawal_stats.avg_amount or 0),
                "max_amount_lovelace": int(withdrawal_stats.max_amount or 0),
                "unique_recipients": int(withdrawal_stats.unique_recipients or 0),
            },
            "recent_withdrawals": [
                {
                    "id": row.id_,
                    "stake_address": row.stake_address,
                    "amount_lovelace": int(row.amount or 0),
                    "withdrawal_time": (
                        str(row.withdrawal_time) if row.withdrawal_time else None
                    ),
                    "withdrawal_epoch": row.withdrawal_epoch,
                    "proposal_index": row.proposal_index,
                }
                for row in treasury_withdrawals
            ],
            "top_proposals": [
                {
                    "proposal_id": row.id_,
                    "proposal_index": row.index,
                    "total_withdrawal_lovelace": int(row.total_withdrawal or 0),
                    "withdrawal_count": int(row.withdrawal_count),
                    "proposal_time": (
                        str(row.proposal_time) if row.proposal_time else None
                    ),
                    "proposal_epoch": row.proposal_epoch,
                }
                for row in treasury_proposals
            ],
        }

    @staticmethod
    def get_voting_participation_metrics(
        session: Session | AsyncSession, days: int = 30, limit: int = 20
    ) -> dict[str, Any]:
        """Analyze voting participation rates and outcomes."""
        if isinstance(session, AsyncSession):
            raise NotImplementedError("Async version not yet implemented")

        # Get latest block for date filtering
        latest_slot = session.execute(select(func.max(Block.slot_no))).scalar() or 0

        slots_per_day = 4320
        start_slot = latest_slot - (days * slots_per_day)

        # Get voting procedure statistics
        voting_stats = session.execute(
            select(
                func.count(VotingProcedure.id_).label("total_votes"),
                func.count(func.distinct(VotingProcedure.gov_action_proposal_id)).label(
                    "proposals_voted_on"
                ),
                func.count(func.distinct(VotingProcedure.drep_voter)).label(
                    "unique_drep_voters"
                ),
                func.count(func.distinct(VotingProcedure.committee_voter)).label(
                    "unique_committee_voters"
                ),
                func.count(func.distinct(VotingProcedure.pool_voter)).label(
                    "unique_pool_voters"
                ),
            )
            .select_from(
                VotingProcedure.__table__.join(
                    GovActionProposal.__table__,
                    VotingProcedure.gov_action_proposal_id == GovActionProposal.id_,
                ).join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
        ).first()

        # Get vote type distribution
        vote_distribution = session.execute(
            select(
                VotingProcedure.vote.label("vote_type"),
                func.count(VotingProcedure.id_).label("count"),
            )
            .select_from(
                VotingProcedure.__table__.join(
                    GovActionProposal.__table__,
                    VotingProcedure.gov_action_proposal_id == GovActionProposal.id_,
                ).join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
            .group_by(VotingProcedure.vote)
            .order_by(desc(func.count(VotingProcedure.id_)))
        ).all()

        # Get most active voters
        active_drep_voters = session.execute(
            select(
                DrepHash.view.label("drep_id"),
                func.count(VotingProcedure.id_).label("vote_count"),
            )
            .select_from(
                VotingProcedure.__table__.join(
                    DrepHash.__table__, VotingProcedure.drep_voter == DrepHash.id_
                )
                .join(
                    GovActionProposal.__table__,
                    VotingProcedure.gov_action_proposal_id == GovActionProposal.id_,
                )
                .join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
            .group_by(DrepHash.view)
            .order_by(desc(func.count(VotingProcedure.id_)))
            .limit(10)
        ).all()

        # Get proposal voting summary
        proposal_voting = session.execute(
            select(
                GovActionProposal.id_.label("proposal_id"),
                GovActionProposal.index.label("proposal_index"),
                GovActionProposal.type_.label("action_type"),
                func.count(VotingProcedure.id_).label("total_votes"),
                func.count(case((VotingProcedure.vote == "Yes", 1))).label("yes_votes"),
                func.count(case((VotingProcedure.vote == "No", 1))).label("no_votes"),
                func.count(case((VotingProcedure.vote == "Abstain", 1))).label(
                    "abstain_votes"
                ),
            )
            .select_from(
                GovActionProposal.__table__.join(
                    VotingProcedure.__table__,
                    GovActionProposal.id_ == VotingProcedure.gov_action_proposal_id,
                ).join(Block.__table__, GovActionProposal.tx_id == Block.id_)
            )
            .where(Block.slot_no >= start_slot)
            .group_by(
                GovActionProposal.id_, GovActionProposal.index, GovActionProposal.type_
            )
            .order_by(desc(func.count(VotingProcedure.id_)))
            .limit(limit)
        ).all()

        return {
            "found": True,
            "analysis_period_days": days,
            "latest_slot": latest_slot,
            "start_slot": start_slot,
            "overall_statistics": {
                "total_votes": int(voting_stats.total_votes or 0),
                "proposals_voted_on": int(voting_stats.proposals_voted_on or 0),
                "unique_drep_voters": int(voting_stats.unique_drep_voters or 0),
                "unique_committee_voters": int(
                    voting_stats.unique_committee_voters or 0
                ),
                "unique_pool_voters": int(voting_stats.unique_pool_voters or 0),
            },
            "vote_distribution": [
                {
                    "vote_type": row.vote_type,
                    "count": int(row.count),
                    "percentage": int(row.count)
                    / max(voting_stats.total_votes or 1, 1)
                    * 100,
                }
                for row in vote_distribution
            ],
            "most_active_drep_voters": [
                {
                    "drep_id": row.drep_id,
                    "vote_count": int(row.vote_count),
                }
                for row in active_drep_voters
            ],
            "proposal_voting_summary": [
                {
                    "proposal_id": row.proposal_id,
                    "proposal_index": row.proposal_index,
                    "action_type": row.action_type,
                    "total_votes": int(row.total_votes),
                    "yes_votes": int(row.yes_votes or 0),
                    "no_votes": int(row.no_votes or 0),
                    "abstain_votes": int(row.abstain_votes or 0),
                    "yes_percentage": (row.yes_votes or 0)
                    / max(row.total_votes, 1)
                    * 100,
                }
                for row in proposal_voting
            ],
        }


# Convenience function
def get_comprehensive_governance_analysis(
    session: Session | AsyncSession,
    proposal_id: int | None = None,
    drep_id: str | None = None,
    committee_member: str | None = None,
    days: int = 30,
) -> dict[str, Any]:
    """Get comprehensive Conway era governance analysis in a single call."""
    queries = GovernanceQueries()

    try:
        # Get all governance analysis components
        proposal_analysis = queries.get_governance_proposal_analysis(
            session, proposal_id, 10
        )
        drep_activity = queries.get_drep_activity_monitoring(session, drep_id, 10)
        committee_operations = queries.get_committee_operations_tracking(
            session, committee_member, 10
        )
        treasury_analysis = queries.get_treasury_governance_analysis(session, days, 10)
        voting_metrics = queries.get_voting_participation_metrics(session, days, 10)

        return {
            "found": True,
            "analysis_parameters": {
                "proposal_id": proposal_id,
                "drep_id": drep_id,
                "committee_member": committee_member,
                "analysis_period_days": days,
            },
            "summary": {
                "total_proposals": proposal_analysis.get("statistics", {}).get(
                    "total_proposals", 0
                ),
                "total_dreps": drep_activity.get("statistics", {}).get(
                    "total_dreps", 0
                ),
                "active_committee_members": committee_operations.get(
                    "statistics", {}
                ).get("active_members", 0),
                "treasury_withdrawals": treasury_analysis.get("statistics", {}).get(
                    "total_withdrawals", 0
                ),
                "total_votes": voting_metrics.get("overall_statistics", {}).get(
                    "total_votes", 0
                ),
            },
            "proposal_analysis": proposal_analysis,
            "drep_activity": drep_activity,
            "committee_operations": committee_operations,
            "treasury_analysis": treasury_analysis,
            "voting_metrics": voting_metrics,
        }
    except Exception as e:
        return {
            "found": False,
            "error": f"Governance analysis failed: {e!s}",
            "analysis_parameters": {
                "proposal_id": proposal_id,
                "drep_id": drep_id,
                "committee_member": committee_member,
                "analysis_period_days": days,
            },
        }


if __name__ == "__main__":
    """Example usage when run directly."""
    try:
        print("Conway Era Governance Utilities Query Examples")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have a configured database connection.")
