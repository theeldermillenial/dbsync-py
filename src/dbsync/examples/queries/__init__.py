"""Query pattern examples for dbsync-py.

This package contains example implementations of common query patterns
using the dbsync-py package models. These examples demonstrate how to
convert SQL queries from the Cardano DB Sync documentation into SQLAlchemy
implementations.

Available query examples:
- chain_metadata: Chain fundamentals and metadata queries
- transaction_analysis: Transaction analysis and UTxO operations
- pool_management: Pool management and block production
- staking_delegation: Staking and delegation pattern queries
- smart_contracts: Smart contracts and scripts analysis
- governance: Conway era governance utilities
- multi_asset: Multi-asset and token operations

These are educational examples showing best practices for:
- Using dbsync-py models
- Building SQLAlchemy queries
- Handling edge cases and errors
- Creating reusable query patterns
"""

# Import available examples
from .chain_metadata import ChainMetadataQueries, get_chain_info
from .governance import GovernanceQueries, get_comprehensive_governance_analysis
from .multi_asset import MultiAssetQueries, get_comprehensive_multi_asset_analysis
from .pool_management import PoolManagementQueries, get_comprehensive_pool_analysis
from .smart_contracts import (
    SmartContractsQueries,
    get_comprehensive_smart_contract_analysis,
)
from .staking_delegation import (
    StakingDelegationQueries,
    get_comprehensive_staking_analysis,
)
from .transaction_analysis import (
    TransactionAnalysisQueries,
    get_comprehensive_transaction_analysis,
)

__all__ = [
    "ChainMetadataQueries",
    "GovernanceQueries",
    "MultiAssetQueries",
    "PoolManagementQueries",
    "SmartContractsQueries",
    "StakingDelegationQueries",
    "TransactionAnalysisQueries",
    "get_chain_info",
    "get_comprehensive_governance_analysis",
    "get_comprehensive_multi_asset_analysis",
    "get_comprehensive_pool_analysis",
    "get_comprehensive_smart_contract_analysis",
    "get_comprehensive_staking_analysis",
    "get_comprehensive_transaction_analysis",
]
