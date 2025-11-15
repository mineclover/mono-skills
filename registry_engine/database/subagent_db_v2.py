"""Database operations for SubAgents - v2."""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from registry_engine.models.tool_centric import (
    SubAgent,
    SubAgentCreate,
    SubAgentResponse,
    SubAgentMetadata,
    Installation,
    Activation,
    Dependency,
    EnvVar,
)
from .models_v2 import (
    SubAgentModel,
    InstallationModel,
    SubAgentActivationModel,
    DependencyModel,
)


class SubAgentDBV2:
    """Database operations for SubAgents - v2."""

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
            category=subagent_data.metadata.category,
            priority=subagent_data.metadata.priority,
        )
        subagent.set_tags(subagent_data.metadata.tags)

        self.session.add(subagent)
        self.session.flush()

        # Add installations
        for install_data in subagent_data.installations:
            install = InstallationModel(
                subagent_id=subagent.id,
                method=install_data.method,
                platform_id=install_data.platform_id,
                package_name=install_data.package_name,
                package_version=install_data.package_version,
                registry_url=str(install_data.registry_url) if install_data.registry_url else None,
                repository=str(install_data.repository) if install_data.repository else None,
                branch=install_data.branch,
                commit=install_data.commit,
                image=install_data.image,
                download_url=str(install_data.download_url) if install_data.download_url else None,
                checksum=install_data.checksum,
                api_endpoint=str(install_data.api_endpoint) if install_data.api_endpoint else None,
                auth_method=install_data.auth_method,
                requires_install=install_data.requires_install,
            )
            install.set_post_install_commands(install_data.post_install_commands)
            if install_data.platforms:
                install.set_platforms(install_data.platforms)
            if install_data.arch:
                install.set_arch(install_data.arch)
            self.session.add(install)

        # Add activations
        for activation_data in subagent_data.activations:
            activation = SubAgentActivationModel(
                subagent_id=subagent.id,
                activation_type=activation_data.type,
                platform_id=activation_data.platform_id,
                command=activation_data.command,
                subcommand=activation_data.subcommand,
                working_dir=activation_data.working_dir,
                host=activation_data.host,
                port=activation_data.port,
                health_check_endpoint=activation_data.health_check_endpoint,
                base_url=str(activation_data.base_url) if activation_data.base_url else None,
                endpoint=activation_data.endpoint,
                method=activation_data.method,
                requires_server=activation_data.requires_server,
                server_command=activation_data.server_command,
                url=str(activation_data.url) if activation_data.url else None,
                event_type=activation_data.event_type,
                timeout=activation_data.timeout,
            )
            activation.set_args(activation_data.args)
            activation.set_env_vars({k: v.model_dump() for k, v in activation_data.env_vars.items()})
            self.session.add(activation)

        # Add dependencies
        for dep_data in subagent_data.dependencies:
            dep = DependencyModel(
                subagent_id=subagent.id,
                dep_type=dep_data.dep_type,
                name=dep_data.name,
                version=dep_data.version,
                required=dep_data.required,
                description=dep_data.description,
            )
            self.session.add(dep)

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
        self,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SubAgentModel]:
        """List SubAgents with optional filtering.

        Args:
            category: Filter by category
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of SubAgent models
        """
        stmt = select(SubAgentModel)

        if category:
            stmt = stmt.where(SubAgentModel.category == category)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

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
        """Convert SQLAlchemy model to Pydantic response.

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
            category=subagent.category,
            tags=subagent.get_tags(),
            priority=subagent.priority,
        )

        # Build installations
        installations = [
            Installation(
                method=inst.method,
                platform_id=inst.platform_id,
                package_name=inst.package_name,
                package_version=inst.package_version,
                registry_url=inst.registry_url,
                repository=inst.repository,
                branch=inst.branch,
                commit=inst.commit,
                image=inst.image,
                download_url=inst.download_url,
                checksum=inst.checksum,
                api_endpoint=inst.api_endpoint,
                auth_method=inst.auth_method,
                requires_install=inst.requires_install,
                post_install_commands=inst.get_post_install_commands(),
                platforms=inst.get_platforms() or None,
                arch=inst.get_arch() or None,
            )
            for inst in subagent.installations
        ]

        # Build activations
        activations = [
            Activation(
                type=act.activation_type,
                platform_id=act.platform_id,
                command=act.command,
                subcommand=act.subcommand,
                args=act.get_args(),
                working_dir=act.working_dir,
                host=act.host,
                port=act.port,
                health_check_endpoint=act.health_check_endpoint,
                base_url=act.base_url,
                endpoint=act.endpoint,
                method=act.method,
                requires_server=act.requires_server,
                server_command=act.server_command,
                url=act.url,
                event_type=act.event_type,
                env_vars={k: EnvVar(**v) for k, v in act.get_env_vars().items()},
                timeout=act.timeout,
            )
            for act in subagent.activations
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

        # Get tool names
        provides_tools = [tool.name for tool in subagent.tools]

        return SubAgentResponse(
            id=subagent.id,
            metadata=metadata,
            installations=installations,
            activations=activations,
            dependencies=dependencies,
            provides_tools=provides_tools,
            created_at=subagent.created_at,
            updated_at=subagent.updated_at,
        )
