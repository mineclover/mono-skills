"""Unit tests for database layer."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from registry_engine.database.models import Base, SubAgentModel
from registry_engine.database.sqlite import SubAgentDB, PromptDB
from registry_engine.models import (
    SubAgentCreate,
    SubAgentMetadata,
    Installation,
    Activation,
)


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestSubAgentDB:
    """Tests for SubAgentDB class."""

    def test_create_subagent(self, db_session):
        """Test creating a subagent."""
        metadata = SubAgentMetadata(
            name="test-agent",
            version="1.0.0",
            description="Test agent",
            domain="testing",
        )

        subagent_data = SubAgentCreate(metadata=metadata)

        subagent_db = SubAgentDB(db_session)
        subagent = subagent_db.create(subagent_data)

        assert subagent.id is not None
        assert subagent.name == "test-agent"
        assert subagent.version == "1.0.0"

    def test_get_by_name(self, db_session):
        """Test retrieving subagent by name."""
        metadata = SubAgentMetadata(
            name="test-agent",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        subagent_data = SubAgentCreate(metadata=metadata)

        subagent_db = SubAgentDB(db_session)
        created = subagent_db.create(subagent_data)

        retrieved = subagent_db.get_by_name("test-agent")
        assert retrieved is not None
        assert retrieved.id == created.id

    def test_get_nonexistent(self, db_session):
        """Test retrieving non-existent subagent."""
        subagent_db = SubAgentDB(db_session)
        result = subagent_db.get_by_name("nonexistent")

        assert result is None

    def test_list_subagents(self, db_session):
        """Test listing subagents."""
        subagent_db = SubAgentDB(db_session)

        # Create multiple subagents
        for i in range(5):
            metadata = SubAgentMetadata(
                name=f"agent-{i}",
                version="1.0.0",
                description=f"Agent {i}",
                domain="test",
            )
            subagent_data = SubAgentCreate(metadata=metadata)
            subagent_db.create(subagent_data)

        results = subagent_db.list(limit=10)
        assert len(results) == 5

    def test_list_with_domain_filter(self, db_session):
        """Test listing with domain filter."""
        subagent_db = SubAgentDB(db_session)

        # Create subagents in different domains
        for domain in ["research", "coding", "research"]:
            metadata = SubAgentMetadata(
                name=f"agent-{domain}",
                version="1.0.0",
                description="Test",
                domain=domain,
            )
            subagent_data = SubAgentCreate(metadata=metadata)
            subagent_db.create(subagent_data)

        results = subagent_db.list(domain="research")
        assert len(results) == 2

    def test_delete_subagent(self, db_session):
        """Test deleting a subagent."""
        metadata = SubAgentMetadata(
            name="to-delete",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        subagent_data = SubAgentCreate(metadata=metadata)

        subagent_db = SubAgentDB(db_session)
        subagent_db.create(subagent_data)

        deleted = subagent_db.delete("to-delete")
        assert deleted is True

        result = subagent_db.get_by_name("to-delete")
        assert result is None

    def test_create_with_installations(self, db_session):
        """Test creating subagent with installations."""
        metadata = SubAgentMetadata(
            name="agent-with-install",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        installation = Installation(
            method="git",
            repository="https://github.com/test/repo",
        )

        subagent_data = SubAgentCreate(
            metadata=metadata,
            installations=[installation],
        )

        subagent_db = SubAgentDB(db_session)
        subagent = subagent_db.create(subagent_data)

        assert len(subagent.installations) == 1
        assert subagent.installations[0].method == "git"

    def test_create_with_activations(self, db_session):
        """Test creating subagent with activations."""
        metadata = SubAgentMetadata(
            name="agent-with-activation",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        activation = Activation(
            activation_type="stdio",
            command="python",
            args=["script.py"],
        )

        subagent_data = SubAgentCreate(
            metadata=metadata,
            activations=[activation],
        )

        subagent_db = SubAgentDB(db_session)
        subagent = subagent_db.create(subagent_data)

        assert len(subagent.activations) == 1
        assert subagent.activations[0].activation_type == "stdio"

    def test_to_response(self, db_session):
        """Test converting model to response."""
        metadata = SubAgentMetadata(
            name="test-agent",
            version="1.0.0",
            description="Test",
            domain="test",
            tags=["tag1", "tag2"],
        )

        subagent_data = SubAgentCreate(metadata=metadata)

        subagent_db = SubAgentDB(db_session)
        subagent = subagent_db.create(subagent_data)

        response = subagent_db.to_response(subagent)

        assert response.id == subagent.id
        assert response.metadata.name == "test-agent"
        assert len(response.metadata.tags) == 2
        assert response.created_at is not None


class TestPromptDB:
    """Tests for PromptDB class."""

    def test_get_prompts_by_subagent(self, db_session):
        """Test getting prompts by subagent name."""
        # Create subagent with prompts
        metadata = SubAgentMetadata(
            name="agent-with-prompts",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        prompts = [
            {"name": "system", "template": "System prompt"},
            {"name": "user", "template": "User prompt"},
        ]

        subagent_data = SubAgentCreate(metadata=metadata, prompts=prompts)

        subagent_db = SubAgentDB(db_session)
        subagent_db.create(subagent_data)

        # Get prompts
        prompt_db = PromptDB(db_session)
        retrieved_prompts = prompt_db.get_by_subagent("agent-with-prompts")

        assert len(retrieved_prompts) == 2

    def test_get_prompt_by_name(self, db_session):
        """Test getting specific prompt by name."""
        metadata = SubAgentMetadata(
            name="agent-test",
            version="1.0.0",
            description="Test",
            domain="test",
        )

        prompts = [
            {"name": "system", "template": "System prompt"},
        ]

        subagent_data = SubAgentCreate(metadata=metadata, prompts=prompts)

        subagent_db = SubAgentDB(db_session)
        subagent_db.create(subagent_data)

        prompt_db = PromptDB(db_session)
        prompt = prompt_db.get_by_name("agent-test", "system")

        assert prompt is not None
        assert prompt.name == "system"
        assert prompt.template == "System prompt"
