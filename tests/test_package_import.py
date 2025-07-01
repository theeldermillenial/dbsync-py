"""
Basic package import tests for dbsync-py.

This module tests that the package can be imported correctly and basic
functionality is available.
"""

from importlib import import_module

import pytest

import dbsync


@pytest.mark.unit
def test_package_import() -> None:
    """Test that the main package can be imported."""
    assert dbsync is not None
    assert hasattr(dbsync, "__version__")


@pytest.mark.unit
def test_submodule_imports() -> None:
    """Test that all submodules can be imported."""
    submodules = [
        "dbsync.config",
        "dbsync.session",
        "dbsync.models",
        "dbsync.queries",
        "dbsync.utils",
    ]

    for module_name in submodules:
        try:
            module = import_module(module_name)
            assert module is not None
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


@pytest.mark.unit
def test_session_imports() -> None:
    """Test that session modules can be imported."""
    from dbsync.session import async_, sync, unified

    # Test basic attributes exist
    assert hasattr(sync, "get_session_context")
    assert hasattr(async_, "get_async_session_context")
    assert hasattr(unified, "dbsync")
    assert hasattr(unified, "DBSyncSession")


@pytest.mark.unit
def test_config_imports() -> None:
    """Test that config module can be imported and has required functions."""
    from dbsync import config

    # Test basic functions exist
    assert hasattr(config, "get_database_url")
    assert hasattr(config, "get_async_database_url")
    assert hasattr(config, "validate_database_url")
    assert hasattr(config, "DatabaseConfig")


@pytest.mark.unit
def test_utils_imports() -> None:
    """Test that utils module can be imported."""
    from dbsync.utils import connection_test

    # Test basic functions exist
    assert hasattr(connection_test, "check_sync_connection")
    assert hasattr(connection_test, "check_async_connection_wrapper")
    assert hasattr(connection_test, "quick_connection_check")


@pytest.mark.unit
def test_package_version() -> None:
    """Test that package version is defined and valid."""
    version = dbsync.__version__
    assert isinstance(version, str)
    assert len(version) > 0

    # Test semantic versioning format (basic check)
    parts = version.split(".")
    assert len(parts) >= 2, (
        f"Version should have at least major.minor format: {version}"
    )

    # Test parts are numeric
    for i, part in enumerate(parts[:2]):  # Check first two parts
        assert part.isdigit(), f"Version part {i} should be numeric: {part}"
