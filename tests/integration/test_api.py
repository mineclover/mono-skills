"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from registry_engine.api.app import app
from registry_engine.api.dependencies import get_session
from registry_engine.database.models import Base


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    return TestingSessionLocal


@pytest.fixture
def client(test_db):
    """Create test client with database override."""

    def override_get_session():
        session = test_db()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "SubAgent Registry API"
        assert "version" in data

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestSubAgentsAPI:
    """Tests for SubAgents API endpoints."""

    def test_create_subagent(self, client):
        """Test creating a subagent."""
        subagent_data = {
            "metadata": {
                "name": "test-agent",
                "version": "1.0.0",
                "description": "Test agent for integration testing",
                "domain": "testing",
                "tags": ["test"],
            }
        }

        response = client.post("/subagents/", json=subagent_data)
        assert response.status_code == 201
        data = response.json()
        assert data["metadata"]["name"] == "test-agent"
        assert "id" in data

    def test_create_duplicate_subagent(self, client):
        """Test creating duplicate subagent fails."""
        subagent_data = {
            "metadata": {
                "name": "duplicate-agent",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            }
        }

        # Create first time
        response1 = client.post("/subagents/", json=subagent_data)
        assert response1.status_code == 201

        # Try to create again
        response2 = client.post("/subagents/", json=subagent_data)
        assert response2.status_code == 409  # Conflict

    def test_get_subagent(self, client):
        """Test retrieving a subagent."""
        # Create subagent first
        subagent_data = {
            "metadata": {
                "name": "get-test-agent",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            }
        }
        client.post("/subagents/", json=subagent_data)

        # Retrieve it
        response = client.get("/subagents/get-test-agent")
        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["name"] == "get-test-agent"

    def test_get_nonexistent_subagent(self, client):
        """Test retrieving non-existent subagent."""
        response = client.get("/subagents/nonexistent")
        assert response.status_code == 404

    def test_list_subagents(self, client):
        """Test listing subagents."""
        # Create multiple subagents
        for i in range(3):
            subagent_data = {
                "metadata": {
                    "name": f"list-agent-{i}",
                    "version": "1.0.0",
                    "description": f"Agent {i}",
                    "domain": "test",
                }
            }
            client.post("/subagents/", json=subagent_data)

        # List them
        response = client.get("/subagents/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_with_domain_filter(self, client):
        """Test listing with domain filter."""
        # Create subagents in different domains
        domains = ["research", "coding", "research"]
        for i, domain in enumerate(domains):
            subagent_data = {
                "metadata": {
                    "name": f"domain-agent-{i}",
                    "version": "1.0.0",
                    "description": "Test",
                    "domain": domain,
                }
            }
            client.post("/subagents/", json=subagent_data)

        # Filter by domain
        response = client.get("/subagents/?domain=research")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_delete_subagent(self, client):
        """Test deleting a subagent."""
        # Create subagent
        subagent_data = {
            "metadata": {
                "name": "delete-test",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            }
        }
        client.post("/subagents/", json=subagent_data)

        # Delete it
        response = client.delete("/subagents/delete-test")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get("/subagents/delete-test")
        assert response.status_code == 404


class TestPromptsAPI:
    """Tests for Prompts API endpoints."""

    def test_get_prompts_for_subagent(self, client):
        """Test getting prompts for a subagent."""
        # Create subagent with prompts
        subagent_data = {
            "metadata": {
                "name": "prompt-test-agent",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            },
            "prompts": [
                {
                    "name": "system",
                    "template": "You are a test agent.",
                    "format": "jinja2",
                },
                {
                    "name": "user",
                    "template": "Hello {{ name }}!",
                    "variables": {"name": "User name"},
                    "format": "jinja2",
                },
            ],
        }
        client.post("/subagents/", json=subagent_data)

        # Get prompts
        response = client.get("/prompts/prompt-test-agent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_specific_prompt(self, client):
        """Test getting a specific prompt."""
        # Create subagent with prompt
        subagent_data = {
            "metadata": {
                "name": "specific-prompt-test",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            },
            "prompts": [
                {
                    "name": "system",
                    "template": "Test template",
                }
            ],
        }
        client.post("/subagents/", json=subagent_data)

        # Get specific prompt
        response = client.get("/prompts/specific-prompt-test/system")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "system"
        assert data["template"] == "Test template"

    def test_render_prompt(self, client):
        """Test rendering a prompt with variables."""
        # Create subagent with template
        subagent_data = {
            "metadata": {
                "name": "render-test",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            },
            "prompts": [
                {
                    "name": "greeting",
                    "template": "Hello {{ name }}, you are {{ age }} years old!",
                    "variables": {"name": "User name", "age": "User age"},
                    "format": "jinja2",
                }
            ],
        }
        client.post("/subagents/", json=subagent_data)

        # Render prompt
        render_data = {"variables": {"name": "Alice", "age": "30"}}
        response = client.post("/prompts/render-test/greeting/render", json=render_data)
        assert response.status_code == 200
        data = response.json()
        assert data["rendered"] == "Hello Alice, you are 30 years old!"

    def test_render_prompt_missing_variable(self, client):
        """Test rendering with missing variable fails gracefully."""
        # Create subagent with template
        subagent_data = {
            "metadata": {
                "name": "missing-var-test",
                "version": "1.0.0",
                "description": "Test",
                "domain": "test",
            },
            "prompts": [
                {
                    "name": "template",
                    "template": "Hello {{ name }}!",
                }
            ],
        }
        client.post("/subagents/", json=subagent_data)

        # Try to render without providing variable
        render_data = {"variables": {}}
        response = client.post("/prompts/missing-var-test/template/render", json=render_data)
        # Should return error (400 Bad Request)
        assert response.status_code == 400


class TestAdminAPI:
    """Tests for Admin API endpoints."""

    def test_get_stats(self, client):
        """Test getting registry statistics."""
        # Create some subagents
        for i in range(3):
            subagent_data = {
                "metadata": {
                    "name": f"stats-agent-{i}",
                    "version": "1.0.0",
                    "description": "Test",
                    "domain": "test",
                }
            }
            client.post("/subagents/", json=subagent_data)

        # Get stats
        response = client.get("/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["subagents_count"] == 3
        assert "vector_db_stats" in data
