"""Unit tests for pool management models.

Tests all pool-related models including pool registration, retirement,
metadata, relays, and performance tracking.
"""

from datetime import UTC, datetime

from dbsync.models import (
    DelistedPool,
    OffchainPoolData,
    OffchainPoolFetchError,
    PoolHash,
    PoolMetadataRef,
    PoolOwner,
    PoolRelay,
    PoolRelayType,
    PoolRetire,
    PoolStat,
    PoolUpdate,
    ReservedPoolTicker,
    ReserveUtxo,
)


class TestPoolHash:
    """Tests for the PoolHash model."""

    def test_pool_hash_creation(self):
        """Test basic PoolHash model creation."""
        pool_hash = PoolHash(
            hash_raw=b"1234567890123456789012345678",  # 28 bytes
            view="pool1abcdefghijklmnopqrstuvwxyz",
        )
        assert pool_hash.hash_raw == b"1234567890123456789012345678"
        assert pool_hash.view == "pool1abcdefghijklmnopqrstuvwxyz"

    def test_pool_hash_fields(self):
        """Test PoolHash model fields and types."""
        pool_hash = PoolHash()
        assert hasattr(pool_hash, "id_")
        assert hasattr(pool_hash, "hash_raw")
        assert hasattr(pool_hash, "view")

    def test_pool_hash_with_minimal_data(self):
        """Test PoolHash with minimal required data."""
        pool_hash = PoolHash(hash_raw=b"1234567890123456789012345678")
        assert pool_hash.hash_raw is not None
        assert pool_hash.view is None


class TestPoolUpdate:
    """Tests for the PoolUpdate model."""

    def test_pool_update_creation(self):
        """Test basic PoolUpdate model creation."""
        pool_update = PoolUpdate(
            hash_id=1,
            cert_index=0,
            vrf_key_hash=b"12345678901234567890123456789012",  # 32 bytes
            pledge=100_000_000_000,  # 100k ADA
            reward_addr_id=1,
            active_epoch_no=250,
            meta_id=1,
            margin=0.05,  # 5%
            fixed_cost=340_000_000,  # 340 ADA
            registered_tx_id=1,
        )
        assert pool_update.hash_id == 1
        assert pool_update.cert_index == 0
        assert pool_update.vrf_key_hash == b"12345678901234567890123456789012"
        assert pool_update.pledge == 100_000_000_000
        assert pool_update.reward_addr_id == 1
        assert pool_update.active_epoch_no == 250
        assert pool_update.meta_id == 1
        assert pool_update.margin == 0.05
        assert pool_update.fixed_cost == 340_000_000
        assert pool_update.registered_tx_id == 1

    def test_pool_update_fields(self):
        """Test PoolUpdate model fields and types."""
        pool_update = PoolUpdate()
        assert hasattr(pool_update, "id_")
        assert hasattr(pool_update, "hash_id")
        assert hasattr(pool_update, "cert_index")
        assert hasattr(pool_update, "vrf_key_hash")
        assert hasattr(pool_update, "pledge")
        assert hasattr(pool_update, "reward_addr_id")
        assert hasattr(pool_update, "active_epoch_no")
        assert hasattr(pool_update, "meta_id")
        assert hasattr(pool_update, "margin")
        assert hasattr(pool_update, "fixed_cost")
        assert hasattr(pool_update, "registered_tx_id")

    def test_pool_update_with_minimal_data(self):
        """Test PoolUpdate with minimal required data."""
        pool_update = PoolUpdate(
            hash_id=1,
            cert_index=0,
            active_epoch_no=250,
        )
        assert pool_update.hash_id == 1
        assert pool_update.cert_index == 0
        assert pool_update.active_epoch_no == 250


class TestPoolRetire:
    """Tests for the PoolRetire model."""

    def test_pool_retire_creation(self):
        """Test basic PoolRetire model creation."""
        pool_retire = PoolRetire(
            hash_id=1,
            cert_index=0,
            retiring_epoch=300,
            announced_tx_id=1,
        )
        assert pool_retire.hash_id == 1
        assert pool_retire.cert_index == 0
        assert pool_retire.retiring_epoch == 300
        assert pool_retire.announced_tx_id == 1

    def test_pool_retire_fields(self):
        """Test PoolRetire model fields and types."""
        pool_retire = PoolRetire()
        assert hasattr(pool_retire, "id_")
        assert hasattr(pool_retire, "hash_id")
        assert hasattr(pool_retire, "cert_index")
        assert hasattr(pool_retire, "retiring_epoch")
        assert hasattr(pool_retire, "announced_tx_id")

    def test_pool_retire_with_minimal_data(self):
        """Test PoolRetire with minimal required data."""
        pool_retire = PoolRetire(
            hash_id=1,
            retiring_epoch=300,
        )
        assert pool_retire.hash_id == 1
        assert pool_retire.retiring_epoch == 300


class TestPoolOwner:
    """Tests for the PoolOwner model."""

    def test_pool_owner_creation(self):
        """Test basic PoolOwner model creation."""
        pool_owner = PoolOwner(
            addr_id=1,
            pool_update_id=1,
        )
        assert pool_owner.addr_id == 1
        assert pool_owner.pool_update_id == 1

    def test_pool_owner_fields(self):
        """Test PoolOwner model fields and types."""
        pool_owner = PoolOwner()
        assert hasattr(pool_owner, "id_")
        assert hasattr(pool_owner, "addr_id")
        assert hasattr(pool_owner, "pool_update_id")


class TestPoolRelay:
    """Tests for the PoolRelay model."""

    def test_pool_relay_single_host_addr_ipv4(self):
        """Test PoolRelay for single host address with IPv4."""
        pool_relay = PoolRelay(
            update_id=1,
            ipv4="192.168.1.100",
            port=3001,
        )
        assert pool_relay.update_id == 1
        assert pool_relay.ipv4 == "192.168.1.100"
        assert pool_relay.port == 3001
        assert pool_relay.ipv6 is None
        assert pool_relay.dns_name is None

    def test_pool_relay_single_host_addr_ipv6(self):
        """Test PoolRelay for single host address with IPv6."""
        pool_relay = PoolRelay(
            update_id=1,
            ipv6="2001:db8::1",
            port=3001,
        )
        assert pool_relay.update_id == 1
        assert pool_relay.ipv6 == "2001:db8::1"
        assert pool_relay.port == 3001
        assert pool_relay.ipv4 is None
        assert pool_relay.dns_name is None

    def test_pool_relay_single_host_name(self):
        """Test PoolRelay for single host name."""
        pool_relay = PoolRelay(
            update_id=1,
            dns_name="relay.cardanopool.com",
            port=3001,
        )
        assert pool_relay.update_id == 1
        assert pool_relay.dns_name == "relay.cardanopool.com"
        assert pool_relay.port == 3001
        assert pool_relay.ipv4 is None
        assert pool_relay.ipv6 is None

    def test_pool_relay_multi_host_name(self):
        """Test PoolRelay for multi host name."""
        pool_relay = PoolRelay(
            update_id=1,
            dns_srv_name="_cardano._tcp.cardanopool.com",
        )
        assert pool_relay.update_id == 1
        assert pool_relay.dns_srv_name == "_cardano._tcp.cardanopool.com"
        assert pool_relay.port is None

    def test_pool_relay_fields(self):
        """Test PoolRelay model fields and types."""
        pool_relay = PoolRelay()
        assert hasattr(pool_relay, "id_")
        assert hasattr(pool_relay, "update_id")
        assert hasattr(pool_relay, "ipv4")
        assert hasattr(pool_relay, "ipv6")
        assert hasattr(pool_relay, "dns_name")
        assert hasattr(pool_relay, "dns_srv_name")
        assert hasattr(pool_relay, "port")


class TestPoolRelayType:
    """Tests for the PoolRelayType enum."""

    def test_pool_relay_type_values(self):
        """Test PoolRelayType enum values."""
        assert PoolRelayType.SINGLE_HOST_ADDR == "single_host_addr"
        assert PoolRelayType.SINGLE_HOST_NAME == "single_host_name"
        assert PoolRelayType.MULTI_HOST_NAME == "multi_host_name"

    def test_pool_relay_type_enum_membership(self):
        """Test PoolRelayType enum membership."""
        assert "single_host_addr" in PoolRelayType
        assert "single_host_name" in PoolRelayType
        assert "multi_host_name" in PoolRelayType
        assert "invalid_type" not in PoolRelayType


class TestPoolMetadataRef:
    """Tests for the PoolMetadataRef model."""

    def test_pool_metadata_ref_creation(self):
        """Test basic PoolMetadataRef model creation."""
        pool_metadata_ref = PoolMetadataRef(
            pool_id=1,
            url="https://cardanopool.com/metadata.json",
            hash_=b"12345678901234567890123456789012",  # 32 bytes
            registered_tx_id=1,
        )
        assert pool_metadata_ref.pool_id == 1
        assert pool_metadata_ref.url == "https://cardanopool.com/metadata.json"
        assert pool_metadata_ref.hash_ == b"12345678901234567890123456789012"
        assert pool_metadata_ref.registered_tx_id == 1

    def test_pool_metadata_ref_fields(self):
        """Test PoolMetadataRef model fields and types."""
        pool_metadata_ref = PoolMetadataRef()
        assert hasattr(pool_metadata_ref, "id_")
        assert hasattr(pool_metadata_ref, "pool_id")
        assert hasattr(pool_metadata_ref, "url")
        assert hasattr(pool_metadata_ref, "hash_")
        assert hasattr(pool_metadata_ref, "registered_tx_id")


class TestOffchainPoolData:
    """Tests for the OffchainPoolData model."""

    def test_offchain_pool_data_creation(self):
        """Test basic OffchainPoolData model creation."""
        offchain_data = OffchainPoolData(
            pool_id=1,
            ticker_name="CSP",
            hash_=b"12345678901234567890123456789012",
            json_={
                "name": "Cardano Stake Pool",
                "description": "A reliable Cardano stake pool",
            },
            bytes_=b"metadata_bytes",
            pmr_id=1,
        )
        assert offchain_data.pool_id == 1
        assert offchain_data.ticker_name == "CSP"
        assert offchain_data.hash_ == b"12345678901234567890123456789012"
        assert offchain_data.json_["name"] == "Cardano Stake Pool"
        assert offchain_data.bytes_ == b"metadata_bytes"
        assert offchain_data.pmr_id == 1

    def test_offchain_pool_data_fields(self):
        """Test OffchainPoolData model fields and types."""
        offchain_data = OffchainPoolData()
        assert hasattr(offchain_data, "id_")
        assert hasattr(offchain_data, "pool_id")
        assert hasattr(offchain_data, "ticker_name")
        assert hasattr(offchain_data, "hash_")
        assert hasattr(offchain_data, "json_")
        assert hasattr(offchain_data, "bytes_")
        assert hasattr(offchain_data, "pmr_id")

    def test_offchain_pool_data_with_minimal_data(self):
        """Test OffchainPoolData with minimal required data."""
        offchain_data = OffchainPoolData(
            pool_id=1,
            pmr_id=1,
        )
        assert offchain_data.pool_id == 1
        assert offchain_data.pmr_id == 1


class TestOffchainPoolFetchError:
    """Tests for the OffchainPoolFetchError model."""

    def test_offchain_pool_fetch_error_creation(self):
        """Test basic OffchainPoolFetchError model creation."""
        fetch_time = datetime.now(UTC)
        fetch_error = OffchainPoolFetchError(
            pool_id=1,
            fetch_time=fetch_time,
            pmr_id=1,
            fetch_error="Connection timeout",
            retry_count=3,
        )
        assert fetch_error.pool_id == 1
        assert fetch_error.fetch_time == fetch_time
        assert fetch_error.pmr_id == 1
        assert fetch_error.fetch_error == "Connection timeout"
        assert fetch_error.retry_count == 3

    def test_offchain_pool_fetch_error_fields(self):
        """Test OffchainPoolFetchError model fields and types."""
        fetch_error = OffchainPoolFetchError()
        assert hasattr(fetch_error, "id_")
        assert hasattr(fetch_error, "pool_id")
        assert hasattr(fetch_error, "fetch_time")
        assert hasattr(fetch_error, "pmr_id")
        assert hasattr(fetch_error, "fetch_error")
        assert hasattr(fetch_error, "retry_count")

    def test_offchain_pool_fetch_error_with_minimal_data(self):
        """Test OffchainPoolFetchError with minimal required data."""
        fetch_error = OffchainPoolFetchError(
            pool_id=1,
            fetch_time=datetime.now(UTC),
            fetch_error="Network error",
        )
        assert fetch_error.pool_id == 1
        assert fetch_error.fetch_time is not None
        assert fetch_error.fetch_error == "Network error"


class TestReserveUtxo:
    """Tests for the ReserveUtxo model."""

    def test_reserve_utxo_creation(self):
        """Test basic ReserveUtxo model creation."""
        reserve_utxo = ReserveUtxo(
            addr_id=1,
            cert_index=0,
            amount=1_000_000_000,  # 1000 ADA
            tx_id=1,
        )
        assert reserve_utxo.addr_id == 1
        assert reserve_utxo.cert_index == 0
        assert reserve_utxo.amount == 1_000_000_000
        assert reserve_utxo.tx_id == 1

    def test_reserve_utxo_fields(self):
        """Test ReserveUtxo model fields and types."""
        reserve_utxo = ReserveUtxo()
        assert hasattr(reserve_utxo, "id_")
        assert hasattr(reserve_utxo, "addr_id")
        assert hasattr(reserve_utxo, "cert_index")
        assert hasattr(reserve_utxo, "amount")
        assert hasattr(reserve_utxo, "tx_id")

    def test_reserve_utxo_with_minimal_data(self):
        """Test ReserveUtxo with minimal required data."""
        reserve_utxo = ReserveUtxo(
            addr_id=1,
            amount=1_000_000_000,
            tx_id=1,
        )
        assert reserve_utxo.addr_id == 1
        assert reserve_utxo.amount == 1_000_000_000
        assert reserve_utxo.tx_id == 1


class TestPoolLifecycleSimulation:
    """Tests simulating complete pool lifecycle scenarios."""

    def test_pool_registration_lifecycle(self):
        """Test complete pool registration lifecycle."""
        # 1. Create pool hash
        pool_hash = PoolHash(
            hash_raw=b"1234567890123456789012345678",
            view="pool1abcdefghijklmnopqrstuvwxyz",
        )

        # 2. Create metadata reference
        metadata_ref = PoolMetadataRef(
            pool_id=1,  # Would be pool_hash.id in real scenario
            url="https://cardanopool.com/metadata.json",
            hash_=b"12345678901234567890123456789012",
            registered_tx_id=1,
        )

        # 3. Create pool registration
        pool_update = PoolUpdate(
            hash_id=1,  # Would be pool_hash.id
            cert_index=0,
            vrf_key_hash=b"12345678901234567890123456789012",
            pledge=100_000_000_000,  # 100k ADA
            reward_addr_id=1,
            active_epoch_no=250,
            meta_id=1,  # Would be metadata_ref.id
            margin=0.05,  # 5%
            fixed_cost=340_000_000,  # 340 ADA
            registered_tx_id=1,
        )

        # 4. Add pool owners
        pool_owner = PoolOwner(
            addr_id=1,
            pool_update_id=1,  # Would be pool_update.id
        )

        # 5. Add relay configuration
        relay_ipv4 = PoolRelay(
            update_id=1,  # Would be pool_update.id
            ipv4="192.168.1.100",
            port=3001,
        )

        relay_dns = PoolRelay(
            update_id=1,
            dns_name="relay.cardanopool.com",
            port=3001,
        )

        # Verify all components are properly configured
        assert pool_hash.hash_raw is not None
        assert metadata_ref.url is not None
        assert pool_update.pledge == 100_000_000_000
        assert pool_owner.addr_id == 1
        assert relay_ipv4.ipv4 == "192.168.1.100"
        assert relay_dns.dns_name == "relay.cardanopool.com"

    def test_pool_metadata_fetch_lifecycle(self):
        """Test pool metadata fetching lifecycle."""
        fetch_time = datetime.now(UTC)

        # 1. Successful metadata fetch
        successful_fetch = OffchainPoolData(
            pool_id=1,
            pmr_id=1,
            ticker_name="CSP",
            hash_=b"12345678901234567890123456789012",
            json_={
                "name": "Cardano Stake Pool",
                "description": "A reliable Cardano stake pool",
            },
            bytes_=b"metadata_bytes",
        )

        # 2. Failed metadata fetch
        failed_fetch = OffchainPoolFetchError(
            pool_id=1,
            fetch_time=fetch_time,
            pmr_id=1,
            fetch_error="Connection timeout after 30 seconds",
            retry_count=3,
        )

        # Verify both scenarios
        assert successful_fetch.json_["name"] == "Cardano Stake Pool"
        assert successful_fetch.ticker_name == "CSP"
        assert failed_fetch.fetch_error == "Connection timeout after 30 seconds"
        assert failed_fetch.retry_count == 3

    def test_pool_retirement_lifecycle(self):
        """Test pool retirement lifecycle."""
        # 1. Pool retirement announcement
        pool_retire = PoolRetire(
            hash_id=1,
            cert_index=0,
            retiring_epoch=300,
            announced_tx_id=1,
        )

        # 2. Reserve distribution (if applicable)
        reserve_distribution = ReserveUtxo(
            addr_id=1,
            cert_index=1,
            amount=1_000_000_000,  # 1000 ADA
            tx_id=1,
        )

        # Verify retirement process
        assert pool_retire.retiring_epoch == 300
        assert pool_retire.announced_tx_id == 1
        assert reserve_distribution.amount == 1_000_000_000

    def test_pool_update_lifecycle(self):
        """Test pool parameter update lifecycle."""
        # Original registration
        original_update = PoolUpdate(
            hash_id=1,
            cert_index=0,
            pledge=100_000_000_000,  # 100k ADA
            margin=0.05,  # 5%
            fixed_cost=340_000_000,  # 340 ADA
            active_epoch_no=250,
            registered_tx_id=1,
        )

        # Updated parameters
        parameter_update = PoolUpdate(
            hash_id=1,  # Same pool
            cert_index=0,
            pledge=150_000_000_000,  # Increased to 150k ADA
            margin=0.03,  # Reduced to 3%
            fixed_cost=340_000_000,  # Same fixed cost
            active_epoch_no=300,  # Later epoch
            registered_tx_id=2,  # Different transaction
        )

        # Verify parameter changes
        assert original_update.pledge == 100_000_000_000
        assert parameter_update.pledge == 150_000_000_000
        assert original_update.margin == 0.05
        assert parameter_update.margin == 0.03
        assert original_update.active_epoch_no < parameter_update.active_epoch_no


class TestPoolStat:
    """Test cases for PoolStat model."""

    def test_pool_stat_creation(self):
        """Test basic PoolStat model creation."""
        pool_stat = PoolStat(
            pool_hash_id=1,
            epoch_no=350,
            number_of_blocks=25,
            number_of_delegators=1500,
            stake=50000000000000,  # 50M ADA
            voting_power=0.025,  # 2.5%
        )

        assert pool_stat.pool_hash_id == 1
        assert pool_stat.epoch_no == 350
        assert pool_stat.number_of_blocks == 25
        assert pool_stat.number_of_delegators == 1500
        assert pool_stat.stake == 50000000000000
        assert pool_stat.voting_power == 0.025

    def test_pool_stat_table_name(self):
        """Test PoolStat table name."""
        assert PoolStat.__tablename__ == "pool_stat"

    def test_pool_stat_fields(self):
        """Test PoolStat field definitions."""
        pool_stat = PoolStat()

        # Check field existence
        assert hasattr(pool_stat, "id_")
        assert hasattr(pool_stat, "pool_hash_id")
        assert hasattr(pool_stat, "epoch_no")
        assert hasattr(pool_stat, "number_of_blocks")
        assert hasattr(pool_stat, "number_of_delegators")
        assert hasattr(pool_stat, "stake")
        assert hasattr(pool_stat, "voting_power")

    def test_pool_stat_with_minimal_data(self):
        """Test PoolStat with minimal required data."""
        pool_stat = PoolStat(
            pool_hash_id=1,
            epoch_no=350,
        )

        assert pool_stat.pool_hash_id == 1
        assert pool_stat.epoch_no == 350
        assert pool_stat.number_of_blocks is None
        assert pool_stat.number_of_delegators is None
        assert pool_stat.stake is None
        assert pool_stat.voting_power is None


class TestReservedPoolTicker:
    """Test cases for ReservedPoolTicker model."""

    def test_reserved_pool_ticker_creation(self):
        """Test basic ReservedPoolTicker model creation."""
        reserved_ticker = ReservedPoolTicker(
            name="IOHK",
            pool_hash=bytes.fromhex("a" * 56),  # 28 bytes
        )

        assert reserved_ticker.name == "IOHK"
        assert reserved_ticker.pool_hash == bytes.fromhex("a" * 56)

    def test_reserved_pool_ticker_table_name(self):
        """Test ReservedPoolTicker table name."""
        assert ReservedPoolTicker.__tablename__ == "reserved_pool_ticker"

    def test_reserved_pool_ticker_fields(self):
        """Test ReservedPoolTicker field definitions."""
        reserved_ticker = ReservedPoolTicker()

        # Check field existence
        assert hasattr(reserved_ticker, "id_")
        assert hasattr(reserved_ticker, "name")
        assert hasattr(reserved_ticker, "pool_hash")

    def test_reserved_pool_ticker_with_minimal_data(self):
        """Test ReservedPoolTicker with minimal required data."""
        reserved_ticker = ReservedPoolTicker(
            name="TEST",
        )

        assert reserved_ticker.name == "TEST"
        assert reserved_ticker.pool_hash is None

    def test_reserved_pool_ticker_max_name_length(self):
        """Test ReservedPoolTicker with maximum name length."""
        # Max length should be 32 characters
        long_name = "A" * 32
        reserved_ticker = ReservedPoolTicker(
            name=long_name,
        )

        assert reserved_ticker.name == long_name
        assert len(reserved_ticker.name) == 32


class TestDelistedPool:
    """Test cases for DelistedPool model."""

    def test_delisted_pool_creation(self):
        """Test basic DelistedPool model creation."""
        delisted_pool = DelistedPool(
            hash_raw=bytes.fromhex("b" * 56),  # 28 bytes
        )

        assert delisted_pool.hash_raw == bytes.fromhex("b" * 56)

    def test_delisted_pool_table_name(self):
        """Test DelistedPool table name."""
        assert DelistedPool.__tablename__ == "delisted_pool"

    def test_delisted_pool_fields(self):
        """Test DelistedPool field definitions."""
        delisted_pool = DelistedPool()

        # Check field existence
        assert hasattr(delisted_pool, "id_")
        assert hasattr(delisted_pool, "hash_raw")

    def test_delisted_pool_with_minimal_data(self):
        """Test DelistedPool with minimal required data."""
        delisted_pool = DelistedPool()

        assert delisted_pool.hash_raw is None

    def test_delisted_pool_hash_uniqueness(self):
        """Test DelistedPool hash should be unique."""
        hash_value = bytes.fromhex("c" * 56)
        delisted_pool = DelistedPool(
            hash_raw=hash_value,
        )

        assert delisted_pool.hash_raw == hash_value
        # In a real database, this would enforce uniqueness
        # Here we just test that the field can hold the value
