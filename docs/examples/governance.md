# Conway Era Governance Examples

This section provides comprehensive examples for working with Conway era governance features in Cardano, including DReps, constitutional committees, governance actions, and voting procedures.

## DRep (Delegated Representatives) Operations

### DRep Registration and Management

```python
from dbsync.session import create_session
from dbsync.models import (
    DrepHash, DrepRegistration, DrepUpdate, DrepDeregistration,
    VotingAnchor, Transaction, Block
)
from sqlalchemy import desc, and_

def get_drep_info(session, drep_id: str):
    """Get comprehensive DRep information."""

    # Get DRep hash record
    drep = session.query(DrepHash).filter(DrepHash.view == drep_id).first()
    if not drep:
        return {"error": "DRep not found"}

    # Get latest registration
    latest_registration = session.query(DrepRegistration).filter(
        DrepRegistration.drep_hash_id == drep.id_
    ).order_by(desc(DrepRegistration.active_epoch_no)).first()

    # Get latest update (if any)
    latest_update = session.query(DrepUpdate).filter(
        DrepUpdate.drep_hash_id == drep.id_
    ).order_by(desc(DrepUpdate.active_epoch_no)).first()

    # Check for deregistration
    deregistration = session.query(DrepDeregistration).filter(
        DrepDeregistration.drep_hash_id == drep.id_
    ).first()

    # Get voting anchor information
    anchor_info = None
    if latest_update and latest_update.voting_anchor_id:
        anchor = session.query(VotingAnchor).filter(
            VotingAnchor.id_ == latest_update.voting_anchor_id
        ).first()
        if anchor:
            anchor_info = {
                "url": anchor.url,
                "data_hash": anchor.data_hash.hex()
            }
    elif latest_registration and latest_registration.voting_anchor_id:
        anchor = session.query(VotingAnchor).filter(
            VotingAnchor.id_ == latest_registration.voting_anchor_id
        ).first()
        if anchor:
            anchor_info = {
                "url": anchor.url,
                "data_hash": anchor.data_hash.hex()
            }

    return {
        "drep_id": drep_id,
        "drep_hash": drep.raw.hex(),
        "registration": {
            "epoch": latest_registration.active_epoch_no if latest_registration else None,
            "deposit": latest_registration.deposit if latest_registration else None,
            "voting_anchor": anchor_info
        },
        "latest_update_epoch": latest_update.active_epoch_no if latest_update else None,
        "is_active": deregistration is None,
        "deregistration_epoch": deregistration.active_epoch_no if deregistration else None
    }

# Usage
session = create_session()
drep_info = get_drep_info(session, "drep1...")
print(f"DRep registered in epoch {drep_info['registration']['epoch']}")
```

### DRep Voting History

```python
from dbsync.models import VotingProcedure, GovActionProposal

def get_drep_voting_history(session, drep_id: str, limit: int = 50):
    """Get voting history for a DRep."""

    drep = session.query(DrepHash).filter(DrepHash.view == drep_id).first()
    if not drep:
        return []

    # Get voting procedures for this DRep
    votes = session.query(
        VotingProcedure, GovActionProposal, Transaction, Block
    ).join(
        GovActionProposal, VotingProcedure.gov_action_proposal_id == GovActionProposal.id_
    ).join(
        Transaction, VotingProcedure.tx_id == Transaction.id_
    ).join(
        Block, Transaction.block_id == Block.id_
    ).filter(
        VotingProcedure.drep_voter == drep.id_
    ).order_by(desc(Block.time)).limit(limit).all()

    voting_history = []
    for vote, proposal, tx, block in votes:
        voting_history.append({
            "proposal_id": proposal.id_,
            "proposal_type": proposal.type_,
            "vote": vote.vote,
            "epoch": block.epoch_no,
            "timestamp": block.time,
            "tx_hash": tx.hash.hex()
        })

    return voting_history

# Usage
voting_history = get_drep_voting_history(session, "drep1...")
for vote in voting_history:
    print(f"Voted {vote['vote']} on {vote['proposal_type']} proposal in epoch {vote['epoch']}")
```

## Constitutional Committee Operations

### Committee Member Information

```python
from dbsync.models import (
    CommitteeHash, CommitteeRegistration, CommitteeDeregistration,
    CommitteeMember
)

def get_committee_info(session, committee_hash: str):
    """Get constitutional committee member information."""

    committee = session.query(CommitteeHash).filter(
        CommitteeHash.view == committee_hash
    ).first()

    if not committee:
        return {"error": "Committee member not found"}

    # Get registration info
    registration = session.query(CommitteeRegistration).filter(
        CommitteeRegistration.committee_hash_id == committee.id_
    ).first()

    # Check for deregistration
    deregistration = session.query(CommitteeDeregistration).filter(
        CommitteeDeregistration.committee_hash_id == committee.id_
    ).first()

    # Get current committee membership status
    current_member = session.query(CommitteeMember).filter(
        CommitteeMember.committee_hash_id == committee.id_
    ).first()

    return {
        "committee_hash": committee_hash,
        "raw_hash": committee.raw.hex(),
        "is_registered": registration is not None,
        "registration_epoch": registration.active_epoch_no if registration else None,
        "is_deregistered": deregistration is not None,
        "deregistration_epoch": deregistration.active_epoch_no if deregistration else None,
        "is_current_member": current_member is not None,
        "term_start_epoch": current_member.epoch_no if current_member else None
    }

def get_committee_voting_record(session, committee_hash: str):
    """Get voting record for a committee member."""

    committee = session.query(CommitteeHash).filter(
        CommitteeHash.view == committee_hash
    ).first()

    if not committee:
        return []

    votes = session.query(
        VotingProcedure, GovActionProposal, Block
    ).join(
        GovActionProposal, VotingProcedure.gov_action_proposal_id == GovActionProposal.id_
    ).join(
        Transaction, VotingProcedure.tx_id == Transaction.id_
    ).join(
        Block, Transaction.block_id == Block.id_
    ).filter(
        VotingProcedure.committee_voter == committee.id_
    ).order_by(desc(Block.time)).all()

    return [
        {
            "proposal_id": proposal.id_,
            "proposal_type": proposal.type_,
            "vote": vote.vote,
            "epoch": block.epoch_no,
            "timestamp": block.time
        }
        for vote, proposal, block in votes
    ]
```

## Governance Actions and Proposals

### Active Governance Proposals

```python
from dbsync.models import GovActionProposal, VotingProcedure

def get_active_governance_proposals(session):
    """Get all currently active governance proposals."""

    active_proposals = session.query(GovActionProposal).filter(
        and_(
            GovActionProposal.ratified_epoch.is_(None),
            GovActionProposal.expired_epoch.is_(None),
            GovActionProposal.dropped_epoch.is_(None)
        )
    ).all()

    proposals_with_votes = []

    for proposal in active_proposals:
        # Get vote counts
        vote_counts = session.query(
            VotingProcedure.vote,
            func.count(VotingProcedure.id_).label('count')
        ).filter(
            VotingProcedure.gov_action_proposal_id == proposal.id_
        ).group_by(VotingProcedure.vote).all()

        # Get submission transaction info
        tx = session.query(Transaction).filter(
            Transaction.id_ == proposal.tx_id
        ).first()

        block = session.query(Block).filter(
            Block.id_ == tx.block_id
        ).first() if tx else None

        proposals_with_votes.append({
            "id": proposal.id_,
            "type": proposal.type_,
            "description": proposal.description,
            "deposit": proposal.deposit,
            "return_address": proposal.return_address,
            "expiration": proposal.expiration,
            "submitted_epoch": block.epoch_no if block else None,
            "vote_counts": {vote: count for vote, count in vote_counts},
            "tx_hash": tx.hash.hex() if tx else None
        })

    return proposals_with_votes

# Usage
active_proposals = get_active_governance_proposals(session)
for proposal in active_proposals:
    votes = proposal['vote_counts']
    print(f"{proposal['type']} proposal: {votes.get('Yes', 0)} Yes, {votes.get('No', 0)} No, {votes.get('Abstain', 0)} Abstain")
```

### Proposal Lifecycle Analysis

```python
def analyze_proposal_lifecycle(session, proposal_id: int):
    """Analyze the complete lifecycle of a governance proposal."""

    proposal = session.query(GovActionProposal).filter(
        GovActionProposal.id_ == proposal_id
    ).first()

    if not proposal:
        return {"error": "Proposal not found"}

    # Get submission info
    submission_tx = session.query(Transaction).filter(
        Transaction.id_ == proposal.tx_id
    ).first()

    submission_block = session.query(Block).filter(
        Block.id_ == submission_tx.block_id
    ).first() if submission_tx else None

    # Get all votes
    votes = session.query(VotingProcedure, Block).join(
        Transaction, VotingProcedure.tx_id == Transaction.id_
    ).join(
        Block, Transaction.block_id == Block.id_
    ).filter(
        VotingProcedure.gov_action_proposal_id == proposal_id
    ).order_by(Block.time).all()

    # Analyze voting patterns over time
    voting_timeline = []
    vote_totals = {"Yes": 0, "No": 0, "Abstain": 0}

    for vote_proc, block in votes:
        vote_totals[vote_proc.vote] += 1
        voting_timeline.append({
            "epoch": block.epoch_no,
            "timestamp": block.time,
            "vote": vote_proc.vote,
            "voter_type": "DRep" if vote_proc.drep_voter else
                         "Committee" if vote_proc.committee_voter else
                         "Pool" if vote_proc.pool_voter else "Unknown",
            "cumulative_totals": vote_totals.copy()
        })

    # Determine final status
    status = "Active"
    if proposal.ratified_epoch:
        status = "Ratified"
    elif proposal.expired_epoch:
        status = "Expired"
    elif proposal.dropped_epoch:
        status = "Dropped"

    return {
        "proposal_id": proposal_id,
        "type": proposal.type_,
        "description": proposal.description,
        "deposit": proposal.deposit,
        "submission": {
            "epoch": submission_block.epoch_no if submission_block else None,
            "timestamp": submission_block.time if submission_block else None,
            "tx_hash": submission_tx.hash.hex() if submission_tx else None
        },
        "status": status,
        "final_epoch": proposal.ratified_epoch or proposal.expired_epoch or proposal.dropped_epoch,
        "total_votes": len(votes),
        "vote_breakdown": vote_totals,
        "voting_timeline": voting_timeline
    }
```

### Governance Action Types Analysis

```python
def analyze_governance_action_types(session, epoch_range: tuple):
    """Analyze governance action types in a given epoch range."""

    start_epoch, end_epoch = epoch_range

    proposals = session.query(GovActionProposal).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).all()

    type_analysis = {}

    for proposal in proposals:
        prop_type = proposal.type_

        if prop_type not in type_analysis:
            type_analysis[prop_type] = {
                "count": 0,
                "total_deposit": 0,
                "ratified": 0,
                "expired": 0,
                "dropped": 0,
                "active": 0,
                "avg_deposit": 0
            }

        stats = type_analysis[prop_type]
        stats["count"] += 1
        stats["total_deposit"] += proposal.deposit

        if proposal.ratified_epoch:
            stats["ratified"] += 1
        elif proposal.expired_epoch:
            stats["expired"] += 1
        elif proposal.dropped_epoch:
            stats["dropped"] += 1
        else:
            stats["active"] += 1

    # Calculate averages
    for stats in type_analysis.values():
        if stats["count"] > 0:
            stats["avg_deposit"] = stats["total_deposit"] / stats["count"]

    return {
        "epoch_range": epoch_range,
        "by_type": type_analysis,
        "summary": {
            "total_proposals": sum(stats["count"] for stats in type_analysis.values()),
            "total_deposit": sum(stats["total_deposit"] for stats in type_analysis.values())
        }
    }
```

## Stake Pool Governance Participation

### Pool Voting Behavior

```python
from dbsync.models import PoolHash, PoolRegistration

def analyze_pool_governance_participation(session, pool_bech32: str):
    """Analyze a stake pool's governance participation."""

    pool = session.query(PoolHash).filter(PoolHash.view == pool_bech32).first()
    if not pool:
        return {"error": "Pool not found"}

    # Get pool voting history
    votes = session.query(VotingProcedure, GovActionProposal, Block).join(
        GovActionProposal, VotingProcedure.gov_action_proposal_id == GovActionProposal.id_
    ).join(
        Transaction, VotingProcedure.tx_id == Transaction.id_
    ).join(
        Block, Transaction.block_id == Block.id_
    ).filter(
        VotingProcedure.pool_voter == pool.id_
    ).order_by(desc(Block.time)).all()

    # Analyze voting patterns
    vote_patterns = {
        "total_votes": len(votes),
        "by_outcome": {"Yes": 0, "No": 0, "Abstain": 0},
        "by_proposal_type": {},
        "participation_epochs": set()
    }

    for vote, proposal, block in votes:
        vote_patterns["by_outcome"][vote.vote] += 1
        vote_patterns["participation_epochs"].add(block.epoch_no)

        prop_type = proposal.type_
        if prop_type not in vote_patterns["by_proposal_type"]:
            vote_patterns["by_proposal_type"][prop_type] = {"Yes": 0, "No": 0, "Abstain": 0}
        vote_patterns["by_proposal_type"][prop_type][vote.vote] += 1

    vote_patterns["epochs_participated"] = len(vote_patterns["participation_epochs"])
    del vote_patterns["participation_epochs"]  # Remove set for JSON serialization

    return {
        "pool_id": pool_bech32,
        "voting_patterns": vote_patterns,
        "recent_votes": [
            {
                "proposal_type": proposal.type_,
                "vote": vote.vote,
                "epoch": block.epoch_no,
                "timestamp": block.time
            }
            for vote, proposal, block in votes[:10]  # Last 10 votes
        ]
    }
```

## Governance Analytics

### Voting Power Distribution

```python
def analyze_voting_power_distribution(session, epoch_no: int):
    """Analyze voting power distribution across different voter types."""

    # Get all votes in the specified epoch
    votes_in_epoch = session.query(VotingProcedure).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no == epoch_no
    ).all()

    voting_power = {
        "drep_votes": 0,
        "committee_votes": 0,
        "pool_votes": 0,
        "total_unique_voters": {
            "dreps": set(),
            "committee": set(),
            "pools": set()
        }
    }

    for vote in votes_in_epoch:
        if vote.drep_voter:
            voting_power["drep_votes"] += 1
            voting_power["total_unique_voters"]["dreps"].add(vote.drep_voter)
        elif vote.committee_voter:
            voting_power["committee_votes"] += 1
            voting_power["total_unique_voters"]["committee"].add(vote.committee_voter)
        elif vote.pool_voter:
            voting_power["pool_votes"] += 1
            voting_power["total_unique_voters"]["pools"].add(vote.pool_voter)

    return {
        "epoch": epoch_no,
        "vote_counts": {
            "drep_votes": voting_power["drep_votes"],
            "committee_votes": voting_power["committee_votes"],
            "pool_votes": voting_power["pool_votes"]
        },
        "unique_voters": {
            "dreps": len(voting_power["total_unique_voters"]["dreps"]),
            "committee": len(voting_power["total_unique_voters"]["committee"]),
            "pools": len(voting_power["total_unique_voters"]["pools"])
        },
        "total_votes": sum([
            voting_power["drep_votes"],
            voting_power["committee_votes"],
            voting_power["pool_votes"]
        ])
    }
```

### Proposal Success Rate Analysis

```python
def analyze_proposal_success_rates(session, start_epoch: int, end_epoch: int):
    """Analyze proposal success rates by type over time."""

    proposals = session.query(GovActionProposal).join(
        Transaction
    ).join(Block).filter(
        Block.epoch_no.between(start_epoch, end_epoch)
    ).all()

    success_analysis = {}

    for proposal in proposals:
        prop_type = proposal.type_

        if prop_type not in success_analysis:
            success_analysis[prop_type] = {
                "total": 0,
                "ratified": 0,
                "expired": 0,
                "dropped": 0,
                "still_active": 0,
                "success_rate": 0.0
            }

        stats = success_analysis[prop_type]
        stats["total"] += 1

        if proposal.ratified_epoch:
            stats["ratified"] += 1
        elif proposal.expired_epoch:
            stats["expired"] += 1
        elif proposal.dropped_epoch:
            stats["dropped"] += 1
        else:
            stats["still_active"] += 1

    # Calculate success rates
    for prop_type, stats in success_analysis.items():
        concluded = stats["ratified"] + stats["expired"] + stats["dropped"]
        if concluded > 0:
            stats["success_rate"] = stats["ratified"] / concluded * 100

    return {
        "epoch_range": (start_epoch, end_epoch),
        "by_type": success_analysis,
        "overall": {
            "total_proposals": sum(stats["total"] for stats in success_analysis.values()),
            "total_ratified": sum(stats["ratified"] for stats in success_analysis.values()),
            "overall_success_rate": (
                sum(stats["ratified"] for stats in success_analysis.values()) /
                max(1, sum(stats["ratified"] + stats["expired"] + stats["dropped"]
                          for stats in success_analysis.values())) * 100
            )
        }
    }

# Usage examples
session = create_session()

# Analyze recent governance activity
recent_activity = analyze_governance_action_types(session, (450, 460))
print(f"Found {recent_activity['summary']['total_proposals']} proposals in epochs 450-460")

# Check voting power distribution
voting_power = analyze_voting_power_distribution(session, 455)
print(f"Epoch 455 had {voting_power['total_votes']} total votes from {voting_power['unique_voters']['dreps']} DReps")

# Analyze proposal success rates
success_rates = analyze_proposal_success_rates(session, 400, 500)
print(f"Overall success rate: {success_rates['overall']['overall_success_rate']:.1f}%")
```

This comprehensive governance guide provides practical examples for analyzing all aspects of Conway era governance, from individual DRep activity to ecosystem-wide governance analytics.
