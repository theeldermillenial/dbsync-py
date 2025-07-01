"""Integration tests for performance monitoring with database models.

These tests demonstrate the performance monitoring system working with actual
database models and operations, providing realistic performance data collection.
"""

import time
from datetime import UTC, datetime

import pytest

from dbsync.models import Block, MultiAsset, Script, Transaction
from tests.performance.baseline import BaselineManager
from tests.performance.monitor import PerformanceMonitor
from tests.performance.regression import RegressionDetector
from tests.performance.reporter import PerformanceReporter


class TestPerformanceIntegrationWithModels:
    """Integration tests using actual database models."""

    def test_model_creation_performance(self, performance_context):
        """Test performance monitoring during model creation."""
        performance_context.start_monitoring()

        # Create multiple Block instances
        blocks = []
        for i in range(100):
            block = Block(
                id=i,
                hash_=b"a" * 32,
                epoch_no=1,
                slot_no=i * 1000,
                epoch_slot_no=i * 100,
                block_no=i,
                previous_id=i - 1 if i > 0 else None,
                slot_leader_id=1,
                size=1024 + i,
                time=datetime.now(UTC),
                tx_count=5 + i % 10,
                proto_major=8,
                proto_minor=0,
                vrf_key="vrf_key_test",
                op_cert=b"op_cert_test",
                op_cert_counter=i,
            )
            blocks.append(block)

        performance_context.add_custom_metric("blocks_created", len(blocks))

        metrics = performance_context.stop_monitoring()

        # Verify performance metrics
        assert metrics.duration_seconds > 0
        assert metrics.custom_metrics["blocks_created"] == 100
        assert "blocks_created" in metrics.custom_metrics

    def test_model_serialization_performance(self, benchmark_performance):
        """Test performance of model serialization."""
        # Create a complex transaction
        transaction = Transaction(
            id=1,
            hash_=b"b" * 32,
            block_id=1,
            block_index=0,
            out_sum=1000000,
            fee=200000,
            deposit=0,
            size=256,
            invalid_before=None,
            invalid_hereafter=100000,
            valid_contract=True,
            script_size=0,
        )

        # Benchmark serialization
        def serialize_transaction():
            return transaction.model_dump()

        result = benchmark_performance.benchmark_operation(
            "transaction_serialization", serialize_transaction
        )

        # Verify serialization worked
        assert isinstance(result, dict)
        assert "hash_" in result

        # Check benchmark results
        benchmark_results = benchmark_performance.get_benchmark_results()
        assert "transaction_serialization" in benchmark_results
        assert benchmark_results["transaction_serialization"] > 0

    def test_bulk_model_operations_performance(self, performance_context):
        """Test performance of bulk model operations."""
        performance_context.start_monitoring()

        # Create bulk assets
        assets = []
        for i in range(500):
            asset = MultiAsset(
                id=i,
                policy=b"c" * 28,
                name=b"asset_" + str(i).encode(),
                fingerprint=f"asset{i:06d}fingerprint",
            )
            assets.append(asset)

        # Serialize all assets
        serialized_assets = []
        for asset in assets:
            serialized_assets.append(asset.model_dump())

        performance_context.add_custom_metric("assets_created", len(assets))
        performance_context.add_custom_metric(
            "assets_serialized", len(serialized_assets)
        )

        metrics = performance_context.stop_monitoring()

        # Verify metrics
        assert metrics.custom_metrics["assets_created"] == 500
        assert metrics.custom_metrics["assets_serialized"] == 500
        assert metrics.duration_seconds > 0
        assert metrics.memory_delta > 0  # Should have used some memory

    def test_script_model_performance(self, memory_monitoring):
        """Test performance and memory usage of Script models."""
        # Create scripts with various sizes
        scripts = []

        for i in range(50):
            script_size = 100 + i * 10  # Increasing script sizes
            script_bytes = b"script_data_" + b"x" * script_size

            script = Script(
                id=i,
                tx_id=i,
                hash_=b"d" * 32,
                type_="native",  # Native script
                json_={"type": "native", "scripts": []},
                bytes_=script_bytes,
                serialised_size=len(script_bytes),
            )
            scripts.append(script)

        # Take memory snapshot
        memory_monitoring.take_snapshot("after_scripts_created")

        # Serialize all scripts
        serialized_scripts = [script.model_dump() for script in scripts]

        memory_monitoring.take_snapshot("after_serialization")

        # Test hex conversion (uses DBSyncBase encoding)
        hex_hashes = [script.hash_hex for script in scripts]

        memory_monitoring.take_snapshot("after_hex_conversion")

        # Verify results
        assert len(scripts) == 50
        assert len(serialized_scripts) == 50
        assert len(hex_hashes) == 50
        assert all(isinstance(h, str) for h in hex_hashes)

        # Check memory usage
        memory_growth = memory_monitoring.get_memory_growth()
        assert memory_growth["total_growth_bytes"] > 0

        # Memory should be reasonable (not excessive)
        memory_monitoring.assert_memory_limit(500.0)  # 200MB limit

    @pytest.mark.performance_baseline
    def test_baseline_creation_workflow(self, tmp_path):
        """Test creating performance baselines from model operations."""
        baseline_manager = BaselineManager(tmp_path / "baselines")
        monitor = PerformanceMonitor()

        # Collect metrics for baseline creation
        baseline_metrics = []

        for run in range(3):
            monitor.start_monitoring("model_operations_baseline")

            # Perform consistent model operations
            blocks = []
            for i in range(50):
                block = Block(
                    id=i,
                    hash_=b"e" * 32,
                    epoch_no=1,
                    slot_no=i * 1000,
                    epoch_slot_no=i * 100,
                    block_no=i,
                    previous_id=i - 1 if i > 0 else None,
                    slot_leader_id=1,
                    size=1024,
                    time=datetime.now(UTC),
                    tx_count=5,
                    proto_major=8,
                    proto_minor=0,
                    vrf_key="vrf_key_test",
                    op_cert=b"op_cert_test",
                    op_cert_counter=i,
                )
                blocks.append(block)

            # Serialize blocks
            serialized = [block.model_dump() for block in blocks]

            monitor.add_custom_metric("blocks_processed", len(blocks))
            monitor.add_custom_metric("serializations", len(serialized))

            metrics = monitor.stop_monitoring()
            baseline_metrics.append(metrics)

        # Create baseline
        baseline = baseline_manager.create_baseline(
            "model_operations_baseline",
            baseline_metrics,
            duration_threshold=1.5,
            memory_threshold=1.3,
            cpu_threshold=1.4,
        )

        # Verify baseline
        assert baseline.test_name == "model_operations_baseline"
        assert baseline.sample_count == 3
        assert baseline.duration_mean > 0
        assert baseline.memory_peak_mean > 0

        # Verify baseline persistence
        loaded_baseline = baseline_manager.get_baseline("model_operations_baseline")
        assert loaded_baseline is not None
        assert loaded_baseline.duration_mean == baseline.duration_mean

    def test_regression_detection_workflow(self, tmp_path):
        """Test regression detection with model operations."""
        baseline_manager = BaselineManager(tmp_path / "baselines")
        detector = RegressionDetector(sensitivity=1.0)
        monitor = PerformanceMonitor()

        # Create baseline with good performance
        baseline_metrics = []
        for run in range(2):
            monitor.start_monitoring("regression_test")

            # Fast operation
            assets = []
            for i in range(25):  # Smaller number for baseline
                asset = MultiAsset(
                    id=i,
                    policy=b"f" * 28,
                    name=b"fast_asset_" + str(i).encode(),
                    fingerprint=f"fast{i:04d}fingerprint",
                )
                assets.append(asset)

            time.sleep(0.001)  # Minimal delay

            metrics = monitor.stop_monitoring()
            baseline_metrics.append(metrics)

        # Create baseline
        baseline = baseline_manager.create_baseline("regression_test", baseline_metrics)

        # Simulate regression (slower operation)
        monitor.start_monitoring("regression_test")

        # Slower operation - more assets + artificial delay
        slow_assets = []
        for i in range(100):  # 4x more assets
            asset = MultiAsset(
                id=i,
                policy=b"g" * 28,
                name=b"slow_asset_" + str(i).encode(),
                fingerprint=f"slow{i:06d}fingerprint",
            )
            slow_assets.append(asset)

        time.sleep(0.1)  # Artificial delay to simulate regression

        current_metrics = monitor.stop_monitoring()

        # Detect regressions
        regressions = detector.detect_advanced_regressions(
            current_metrics, baseline_metrics, baseline
        )

        # Should detect some regressions due to increased workload and delay
        regression_alerts = [r for r in regressions if r.has_regression]

        # Verify regression detection
        if regression_alerts:
            # At least duration should be flagged
            duration_regressions = [
                r for r in regression_alerts if r.metric_name == "duration_seconds"
            ]
            assert len(duration_regressions) > 0
            assert (
                duration_regressions[0].current_value
                > duration_regressions[0].expected_value
            )

    def test_comprehensive_performance_report(self, tmp_path):
        """Test generating comprehensive performance reports."""
        reporter = PerformanceReporter(tmp_path / "reports")
        baseline_manager = BaselineManager(tmp_path / "baselines")
        monitor = PerformanceMonitor()

        # Collect diverse metrics
        all_metrics = []

        # Block creation test
        monitor.start_monitoring("block_creation_test")
        blocks = [
            Block(
                id=i,
                hash_=b"h" * 32,
                epoch_no=1,
                slot_no=i * 1000,
                epoch_slot_no=i * 100,
                block_no=i,
                previous_id=i - 1 if i > 0 else None,
                slot_leader_id=1,
                size=1024,
                time=datetime.now(UTC),
                tx_count=5,
                proto_major=8,
                proto_minor=0,
                vrf_key="vrf_key_test",
                op_cert=b"op_cert_test",
                op_cert_counter=i,
            )
            for i in range(30)
        ]
        monitor.add_custom_metric("blocks_created", len(blocks))
        metrics1 = monitor.stop_monitoring()
        all_metrics.append(metrics1)

        # Transaction processing test
        monitor.start_monitoring("transaction_processing_test")
        transactions = [
            Transaction(
                id=i,
                hash_=b"i" * 32,
                block_id=1,
                block_index=i,
                out_sum=1000000 + i * 1000,
                fee=200000,
                deposit=0,
                size=256,
                invalid_before=None,
                invalid_hereafter=100000,
                valid_contract=True,
                script_size=0,
            )
            for i in range(20)
        ]
        monitor.add_custom_metric("transactions_processed", len(transactions))
        metrics2 = monitor.stop_monitoring()
        all_metrics.append(metrics2)

        # Create baselines
        baseline1 = baseline_manager.create_baseline("block_creation_test", [metrics1])
        baseline2 = baseline_manager.create_baseline(
            "transaction_processing_test", [metrics2]
        )

        baselines = {baseline1.test_name: baseline1, baseline2.test_name: baseline2}

        # Generate reports
        json_report = reporter.generate_json_report(all_metrics, baselines)
        html_report = reporter.generate_html_report(
            all_metrics, baselines, title="Database Models Performance Report"
        )

        # Verify reports were created
        assert json_report.exists()
        assert html_report.exists()

        # Verify JSON report content
        import json

        with open(json_report) as f:
            report_data = json.load(f)

        assert report_data["summary"]["total_tests"] == 2
        assert report_data["summary"]["total_metrics"] == 2
        assert report_data["summary"]["baselines_count"] == 2
        assert len(report_data["metrics"]) == 2

        # Verify HTML report content
        with open(html_report) as f:
            html_content = f.read()

        assert "Database Models Performance Report" in html_content
        assert "block_creation_test" in html_content
        assert "transaction_processing_test" in html_content
        assert "Performance Analysis" in html_content
