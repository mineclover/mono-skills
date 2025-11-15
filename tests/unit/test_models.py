"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from registry_engine.models import (
    SubAgentMetadata,
    Installation,
    Activation,
    PromptTemplate,
    InterfaceSpec,
    Tool,
    StructuredOutput,
    SubAgent,
)


class TestSubAgentMetadata:
    """Tests for SubAgentMetadata model."""

    def test_valid_metadata(self):
        """Test creating valid metadata."""
        metadata = SubAgentMetadata(
            name="test-agent",
            version="1.0.0",
            description="Test agent",
            domain="testing",
            tags=["test", "sample"],
            capabilities=["test capability"],
            use_cases=["test use case"],
            priority=10,
        )

        assert metadata.name == "test-agent"
        assert metadata.version == "1.0.0"
        assert metadata.priority == 10
        assert len(metadata.tags) == 2

    def test_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(ValidationError):
            SubAgentMetadata(name="test")

    def test_priority_bounds(self):
        """Test priority is bounded 0-100."""
        with pytest.raises(ValidationError):
            SubAgentMetadata(
                name="test",
                version="1.0.0",
                description="Test",
                domain="test",
                priority=150,  # Invalid
            )

        with pytest.raises(ValidationError):
            SubAgentMetadata(
                name="test",
                version="1.0.0",
                description="Test",
                domain="test",
                priority=-1,  # Invalid
            )


class TestInstallation:
    """Tests for Installation model."""

    def test_git_installation(self):
        """Test Git installation method."""
        install = Installation(
            method="git",
            repository="https://github.com/test/repo",
            branch="main",
        )

        assert install.method == "git"
        assert install.repository == "https://github.com/test/repo"
        assert install.branch == "main"

    def test_npm_installation(self):
        """Test NPM installation method."""
        install = Installation(
            method="npm",
            package_name="@test/package",
            package_version="1.0.0",
        )

        assert install.method == "npm"
        assert install.package_name == "@test/package"

    def test_docker_installation(self):
        """Test Docker installation method."""
        install = Installation(
            method="docker",
            image="test/image:latest",
        )

        assert install.method == "docker"
        assert install.image == "test/image:latest"

    def test_post_install_commands(self):
        """Test post-install commands."""
        install = Installation(
            method="git",
            repository="https://github.com/test/repo",
            post_install_commands=["npm install", "npm build"],
        )

        assert len(install.post_install_commands) == 2


class TestActivation:
    """Tests for Activation model."""

    def test_stdio_activation(self):
        """Test stdio activation type."""
        activation = Activation(
            activation_type="stdio",
            command="python",
            args=["script.py", "--mode=prod"],
            working_dir="/app",
        )

        assert activation.activation_type == "stdio"
        assert activation.command == "python"
        assert len(activation.args) == 2

    def test_http_activation(self):
        """Test HTTP activation type."""
        activation = Activation(
            activation_type="http",
            url="http://localhost:8000",
            health_check={"endpoint": "/health"},
        )

        assert activation.activation_type == "http"
        assert activation.url == "http://localhost:8000"
        assert activation.health_check["endpoint"] == "/health"

    def test_env_vars(self):
        """Test environment variables."""
        activation = Activation(
            activation_type="stdio",
            command="python",
            env_vars={
                "API_KEY": {"required": True, "description": "API key"},
                "DEBUG": {"required": False, "default": "false"},
            },
        )

        assert "API_KEY" in activation.env_vars
        assert activation.env_vars["API_KEY"]["required"] is True


class TestPromptTemplate:
    """Tests for PromptTemplate model."""

    def test_jinja2_template(self):
        """Test Jinja2 template."""
        prompt = PromptTemplate(
            name="system",
            template="Hello {{ name }}!",
            variables={"name": "User name"},
            format="jinja2",
        )

        assert prompt.name == "system"
        assert prompt.format == "jinja2"
        assert "name" in prompt.variables

    def test_default_format(self):
        """Test default format is jinja2."""
        prompt = PromptTemplate(
            name="test",
            template="Test template",
        )

        assert prompt.format == "jinja2"


class TestInterfaceSpec:
    """Tests for InterfaceSpec model."""

    def test_interface_with_tools(self):
        """Test interface with tools."""
        tool = Tool(
            name="test_tool",
            description="Test tool",
            parameters={"arg1": {"type": "string"}},
            required_params=["arg1"],
        )

        interface = InterfaceSpec(
            protocol="langchain",
            tools=[tool],
        )

        assert interface.protocol == "langchain"
        assert len(interface.tools) == 1
        assert interface.tools[0].name == "test_tool"

    def test_structured_outputs(self):
        """Test structured outputs."""
        output = StructuredOutput(
            name="TestOutput",
            schema_type="pydantic",
            schema={
                "properties": {
                    "field1": {"type": "string"},
                }
            },
        )

        interface = InterfaceSpec(
            protocol="langchain",
            structured_outputs=[output],
        )

        assert len(interface.structured_outputs) == 1
        assert interface.structured_outputs[0].name == "TestOutput"


class TestSubAgent:
    """Tests for complete SubAgent model."""

    def test_minimal_subagent(self):
        """Test creating minimal SubAgent."""
        metadata = SubAgentMetadata(
            name="minimal-agent",
            version="1.0.0",
            description="Minimal test agent",
            domain="test",
        )

        subagent = SubAgent(metadata=metadata)

        assert subagent.metadata.name == "minimal-agent"
        assert len(subagent.prompts) == 0
        assert len(subagent.installations) == 0

    def test_complete_subagent(self):
        """Test creating complete SubAgent with all fields."""
        metadata = SubAgentMetadata(
            name="complete-agent",
            version="1.0.0",
            description="Complete test agent",
            domain="test",
            tags=["test"],
        )

        prompt = PromptTemplate(
            name="system",
            template="Test prompt",
        )

        installation = Installation(
            method="git",
            repository="https://github.com/test/repo",
        )

        activation = Activation(
            activation_type="stdio",
            command="python",
            args=["script.py"],
        )

        interface = InterfaceSpec(protocol="langchain")

        subagent = SubAgent(
            metadata=metadata,
            prompts=[prompt],
            installations=[installation],
            activations=[activation],
            interface=interface,
        )

        assert subagent.metadata.name == "complete-agent"
        assert len(subagent.prompts) == 1
        assert len(subagent.installations) == 1
        assert len(subagent.activations) == 1
        assert subagent.interface.protocol == "langchain"
