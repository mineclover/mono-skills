"""SQLite database operations for SubAgent Registry."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from registry_engine.models import (
    Activation,
    Dependency,
    Example,
    Installation,
    InterfaceSpec,
    PromptTemplate,
    SubAgent,
    SubAgentCreate,
    SubAgentMetadata,
    SubAgentResponse,
)
from .models import (
    ActivationModel,
    Base,
    DependencyModel,
    ExampleModel,
    InstallationModel,
    InterfaceModel,
    PromptModel,
    SubAgentModel,
)


class Database:
    """Database connection manager."""

    def __init__(self, db_path: str = "data/registry.db"):
        """Initialize database connection.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def init_db(self) -> None:
        """Initialize database schema."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()


# Global database instance
_db: Optional[Database] = None


def init_db(db_path: str = "data/registry.db") -> None:
    """Initialize the global database instance."""
    global _db
    _db = Database(db_path)
    _db.init_db()


def get_db() -> Database:
    """Get the global database instance."""
    if _db is None:
        init_db()
    return _db


class SubAgentDB:
    """Database operations for SubAgents."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, subagent_data: SubAgentCreate) -> SubAgentModel:
        """Create a new SubAgent.

        Args:
            subagent_data: SubAgent data to create

        Returns:
            Created SubAgent model
        """
        # Create SubAgent
        subagent = SubAgentModel(
            name=subagent_data.metadata.name,
            version=subagent_data.metadata.version,
            description=subagent_data.metadata.description,
            author=subagent_data.metadata.author,
            license=subagent_data.metadata.license,
            domain=subagent_data.metadata.domain,
            priority=subagent_data.metadata.priority,
        )
        subagent.set_tags(subagent_data.metadata.tags)
        subagent.set_capabilities(subagent_data.metadata.capabilities)
        subagent.set_use_cases(subagent_data.metadata.use_cases)

        self.session.add(subagent)
        self.session.flush()

        # Add prompts
        for prompt_data in subagent_data.prompts:
            prompt = PromptModel(
                subagent_id=subagent.id,
                name=prompt_data.get("name"),
                template=prompt_data.get("template"),
                format=prompt_data.get("format", "jinja2"),
                description=prompt_data.get("description"),
            )
            prompt.set_variables(prompt_data.get("variables", {}))
            self.session.add(prompt)

        # Add interface
        if subagent_data.interface:
            interface = InterfaceModel(
                subagent_id=subagent.id,
                protocol=subagent_data.interface.get("protocol"),
            )
            interface.set_tools(subagent_data.interface.get("tools", []))
            interface.set_structured_outputs(subagent_data.interface.get("structured_outputs", []))
            interface.set_capabilities(subagent_data.interface.get("capabilities", []))
            interface.set_metadata(subagent_data.interface.get("metadata", {}))
            self.session.add(interface)

        # Add installations
        for installation in subagent_data.installations:
            install_model = InstallationModel(
                subagent_id=subagent.id,
                method=installation.method,
                repository=installation.repository,
                branch=installation.branch,
                commit=installation.commit,
                package_name=installation.package_name,
                package_version=installation.package_version,
                registry_url=installation.registry_url,
                image=installation.image,
                url=installation.url,
            )
            install_model.set_auth(installation.auth or {})
            install_model.set_post_install_commands(installation.post_install_commands)
            self.session.add(install_model)

        # Add activations
        for activation in subagent_data.activations:
            activation_model = ActivationModel(
                subagent_id=subagent.id,
                activation_type=activation.activation_type,
                command=activation.command,
                working_dir=activation.working_dir,
                protocol=activation.protocol,
                url=activation.url,
            )
            activation_model.set_args(activation.args)
            activation_model.set_env_vars(activation.env_vars)
            activation_model.set_health_check(activation.health_check or {})
            activation_model.set_capabilities(activation.capabilities)
            activation_model.set_auth(activation.auth or {})
            self.session.add(activation_model)

        # Add examples
        for example in subagent_data.examples:
            example_model = ExampleModel(
                subagent_id=subagent.id,
                input=example.input,
                output=example.output,
                description=example.description,
            )
            self.session.add(example_model)

        # Add dependencies
        for dependency in subagent_data.dependencies:
            dependency_model = DependencyModel(
                subagent_id=subagent.id,
                dep_type=dependency.dep_type,
                name=dependency.name,
                version=dependency.version,
                required=dependency.required,
                description=dependency.description,
            )
            self.session.add(dependency_model)

        self.session.commit()
        self.session.refresh(subagent)
        return subagent

    def get_by_name(self, name: str) -> Optional[SubAgentModel]:
        """Get SubAgent by name.

        Args:
            name: SubAgent name

        Returns:
            SubAgent model or None
        """
        stmt = select(SubAgentModel).where(SubAgentModel.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, subagent_id: int) -> Optional[SubAgentModel]:
        """Get SubAgent by ID.

        Args:
            subagent_id: SubAgent ID

        Returns:
            SubAgent model or None
        """
        return self.session.get(SubAgentModel, subagent_id)

    def list(
        self, domain: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[SubAgentModel]:
        """List SubAgents with optional filtering.

        Args:
            domain: Filter by domain
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of SubAgent models
        """
        stmt = select(SubAgentModel)

        if domain:
            stmt = stmt.where(SubAgentModel.domain == domain)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def update(self, name: str, subagent_data: SubAgentCreate) -> Optional[SubAgentModel]:
        """Update SubAgent.

        Args:
            name: SubAgent name
            subagent_data: New SubAgent data

        Returns:
            Updated SubAgent model or None
        """
        subagent = self.get_by_name(name)
        if not subagent:
            return None

        # Update metadata
        subagent.version = subagent_data.metadata.version
        subagent.description = subagent_data.metadata.description
        subagent.author = subagent_data.metadata.author
        subagent.license = subagent_data.metadata.license
        subagent.domain = subagent_data.metadata.domain
        subagent.priority = subagent_data.metadata.priority
        subagent.set_tags(subagent_data.metadata.tags)
        subagent.set_capabilities(subagent_data.metadata.capabilities)
        subagent.set_use_cases(subagent_data.metadata.use_cases)

        # Note: For full implementation, you'd also update related tables
        # This is a simplified version

        self.session.commit()
        self.session.refresh(subagent)
        return subagent

    def delete(self, name: str) -> bool:
        """Delete SubAgent.

        Args:
            name: SubAgent name

        Returns:
            True if deleted, False if not found
        """
        subagent = self.get_by_name(name)
        if not subagent:
            return False

        self.session.delete(subagent)
        self.session.commit()
        return True

    def to_response(self, subagent: SubAgentModel) -> SubAgentResponse:
        """Convert SQLAlchemy model to Pydantic response model.

        Args:
            subagent: SubAgent model

        Returns:
            SubAgent response model
        """
        # Build metadata
        metadata = SubAgentMetadata(
            name=subagent.name,
            version=subagent.version,
            description=subagent.description,
            author=subagent.author,
            license=subagent.license,
            domain=subagent.domain,
            tags=subagent.get_tags(),
            capabilities=subagent.get_capabilities(),
            use_cases=subagent.get_use_cases(),
            priority=subagent.priority,
        )

        # Build prompts
        prompts = [
            PromptTemplate(
                name=p.name,
                template=p.template,
                variables=p.get_variables(),
                format=p.format,
                description=p.description,
            )
            for p in subagent.prompts
        ]

        # Build interface
        interface = None
        if subagent.interfaces:
            i = subagent.interfaces[0]
            interface = InterfaceSpec(
                protocol=i.protocol,
                tools=i.get_tools(),
                structured_outputs=i.get_structured_outputs(),
                capabilities=i.get_capabilities(),
                metadata=i.get_metadata(),
            )

        # Build installations
        installations = [
            Installation(
                method=inst.method,
                repository=inst.repository,
                branch=inst.branch,
                commit=inst.commit,
                package_name=inst.package_name,
                package_version=inst.package_version,
                registry_url=inst.registry_url,
                image=inst.image,
                url=inst.url,
                auth=inst.get_auth(),
                post_install_commands=inst.get_post_install_commands(),
            )
            for inst in subagent.installations
        ]

        # Build activations
        activations = [
            Activation(
                activation_type=act.activation_type,
                command=act.command,
                args=act.get_args(),
                working_dir=act.working_dir,
                env_vars=act.get_env_vars(),
                health_check=act.get_health_check(),
                protocol=act.protocol,
                capabilities=act.get_capabilities(),
                url=act.url,
                auth=act.get_auth(),
            )
            for act in subagent.activations
        ]

        # Build examples
        examples = [
            Example(input=ex.input, output=ex.output, description=ex.description)
            for ex in subagent.examples
        ]

        # Build dependencies
        dependencies = [
            Dependency(
                dep_type=dep.dep_type,
                name=dep.name,
                version=dep.version,
                required=dep.required,
                description=dep.description,
            )
            for dep in subagent.dependencies
        ]

        return SubAgentResponse(
            id=subagent.id,
            metadata=metadata,
            prompts=prompts,
            interface=interface,
            installations=installations,
            activations=activations,
            examples=examples,
            dependencies=dependencies,
            created_at=subagent.created_at,
            updated_at=subagent.updated_at,
        )


class PromptDB:
    """Database operations for Prompts."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_subagent(self, subagent_name: str) -> List[PromptModel]:
        """Get all prompts for a SubAgent.

        Args:
            subagent_name: SubAgent name

        Returns:
            List of Prompt models
        """
        stmt = (
            select(PromptModel)
            .join(SubAgentModel)
            .where(SubAgentModel.name == subagent_name)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_by_name(self, subagent_name: str, prompt_name: str) -> Optional[PromptModel]:
        """Get a specific prompt.

        Args:
            subagent_name: SubAgent name
            prompt_name: Prompt name

        Returns:
            Prompt model or None
        """
        stmt = (
            select(PromptModel)
            .join(SubAgentModel)
            .where(SubAgentModel.name == subagent_name)
            .where(PromptModel.name == prompt_name)
        )
        return self.session.execute(stmt).scalar_one_or_none()


class InterfaceDB:
    """Database operations for Interfaces."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_subagent(self, subagent_name: str) -> Optional[InterfaceModel]:
        """Get interface for a SubAgent.

        Args:
            subagent_name: SubAgent name

        Returns:
            Interface model or None
        """
        stmt = (
            select(InterfaceModel)
            .join(SubAgentModel)
            .where(SubAgentModel.name == subagent_name)
        )
        return self.session.execute(stmt).scalar_one_or_none()
