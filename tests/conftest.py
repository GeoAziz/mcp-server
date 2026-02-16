"""
Pytest configuration and fixtures for MCP Server tests
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Disable rate limiting for tests
os.environ["MCP_RATE_LIMIT"] = "1000000/minute"

# Import models and database utilities
from models import Base
from database import get_db, init_db
from mcp_server import app


# Use in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test function.
    Uses in-memory SQLite for speed and isolation.
    """
    # Create test engine with in-memory SQLite
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Required for in-memory SQLite
    )
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create session
    db = TestingSessionLocal()
    
    try:
        yield db
    finally:
        db.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a TestClient with overridden database dependency.
    Each test gets a fresh client with clean database.
    """
    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # Session cleanup handled by test_db fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Disable authentication for tests (unless specific test needs it)
    os.environ.pop("MCP_API_KEY", None)
    
    # Create test client with raise_server_exceptions=False to prevent rate limit from being raised
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    
    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_with_auth(test_db):
    """
    Create a TestClient with API key authentication enabled.
    """
    # Override the get_db dependency to use test database
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Set test API key
    test_api_key = "test-api-key-12345"
    os.environ["MCP_API_KEY"] = test_api_key
    
    # Create test client with raise_server_exceptions=False
    with TestClient(app, raise_server_exceptions=False) as test_client:
        # Attach the API key to the client for convenience
        test_client.api_key = test_api_key
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()
    os.environ.pop("MCP_API_KEY", None)


@pytest.fixture
def sample_users():
    """Sample user data for tests"""
    return [
        {"username": "alice", "role": "admin"},
        {"username": "bob", "role": "user"},
        {"username": "charlie", "role": "user"},
    ]


@pytest.fixture
def sample_tasks():
    """Sample task data for tests"""
    return [
        {
            "title": "Task 1",
            "description": "First task",
            "priority": "high",
            "status": "pending",
            "assigned_to": "alice"
        },
        {
            "title": "Task 2",
            "description": "Second task",
            "priority": "medium",
            "status": "in_progress",
            "assigned_to": "bob"
        },
        {
            "title": "Task 3",
            "description": "Third task",
            "priority": "low",
            "status": "completed",
            "assigned_to": "charlie"
        },
    ]


@pytest.fixture
def sample_config():
    """Sample config data for tests"""
    return {
        "max_tasks": 100,
        "default_priority": "medium",
        "test_setting": "test_value"
    }
