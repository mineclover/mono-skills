"""Pytest configuration and fixtures."""

import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables."""
    os.environ["OPENAI_API_KEY"] = "test-key-for-testing"
    os.environ["TESTING"] = "true"
