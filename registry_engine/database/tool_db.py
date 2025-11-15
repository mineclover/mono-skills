"""Database operations for Tools."""

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from registry_engine.models.tool_centric import (
    Tool,
    ToolCreate,
    ToolPrompt,
    ToolResponse,
    ParameterSchema,
    StructuredOutputSchema,
    Activation,
)
from .models_v2 import (
    ToolModel,
    ToolPromptModel,
    ToolActivationModel,
    SubAgentModel,
)


class ToolDB:
    """Database operations for Tools."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, tool_data: ToolCreate) -> ToolModel:
        """Create a new Tool.

        Args:
            tool_data: Tool data to create

        Returns:
            Created Tool model
        """
        # Get SubAgent
        subagent = self.session.query(SubAgentModel).filter(
            SubAgentModel.name == tool_data.subagent_name
        ).first()

        if not subagent:
            raise ValueError(f"SubAgent '{tool_data.subagent_name}' not found")

        # Create Tool
        tool = ToolModel(
            name=tool_data.name,
            display_name=tool_data.display_name,
            description=tool_data.description,
            category=tool_data.category,
            subagent_id=subagent.id,
            subagent_version=tool_data.subagent_version,
            inherit_activation=tool_data.inherit_activation,
            protocol=tool_data.protocol,
            implementation_hint=tool_data.implementation_hint,
        )
        tool.set_tags(tool_data.tags)
        tool.set_parameters(tool_data.parameters.model_dump())
        if tool_data.structured_output:
            tool.set_structured_output(tool_data.structured_output.model_dump())

        self.session.add(tool)
        self.session.flush()

        # Add prompts
        for prompt_data in tool_data.prompts:
            prompt = ToolPromptModel(
                tool_id=tool.id,
                name=prompt_data.name,
                description=prompt_data.description,
                template_type=prompt_data.template_type,
                system_message=prompt_data.system_message,
                human_message_template=prompt_data.human_message_template,
                ai_message_prefix=prompt_data.ai_message_prefix,
                template=prompt_data.template,
            )
            prompt.set_examples(prompt_data.examples)
            prompt.set_input_variables(prompt_data.input_variables)
            prompt.set_partial_variables(prompt_data.partial_variables)
            self.session.add(prompt)

        # Add activations
        for activation_data in tool_data.activations:
            activation = ToolActivationModel(
                tool_id=tool.id,
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

        self.session.commit()
        self.session.refresh(tool)
        return tool

    def get_by_name(self, name: str) -> Optional[ToolModel]:
        """Get Tool by name.

        Args:
            name: Tool name

        Returns:
            Tool model or None
        """
        stmt = select(ToolModel).where(ToolModel.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, tool_id: int) -> Optional[ToolModel]:
        """Get Tool by ID.

        Args:
            tool_id: Tool ID

        Returns:
            Tool model or None
        """
        return self.session.get(ToolModel, tool_id)

    def list(
        self,
        category: Optional[str] = None,
        subagent_name: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ToolModel]:
        """List Tools with optional filtering.

        Args:
            category: Filter by category
            subagent_name: Filter by SubAgent
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of Tool models
        """
        stmt = select(ToolModel)

        if category:
            stmt = stmt.where(ToolModel.category == category)

        if subagent_name:
            stmt = stmt.join(SubAgentModel).where(SubAgentModel.name == subagent_name)

        stmt = stmt.offset(skip).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def delete(self, name: str) -> bool:
        """Delete Tool.

        Args:
            name: Tool name

        Returns:
            True if deleted, False if not found
        """
        tool = self.get_by_name(name)
        if not tool:
            return False

        self.session.delete(tool)
        self.session.commit()
        return True

    def to_response(self, tool: ToolModel) -> ToolResponse:
        """Convert SQLAlchemy model to Pydantic response.

        Args:
            tool: Tool model

        Returns:
            Tool response model
        """
        # Build prompts
        prompts = [
            ToolPrompt(
                name=p.name,
                description=p.description,
                template_type=p.template_type,
                system_message=p.system_message,
                human_message_template=p.human_message_template,
                ai_message_prefix=p.ai_message_prefix,
                examples=p.get_examples(),
                input_variables=p.get_input_variables(),
                partial_variables=p.get_partial_variables(),
                template=p.template,
            )
            for p in tool.prompts
        ]

        # Build activations
        from registry_engine.models.tool_centric import EnvVar

        activations = [
            Activation(
                type=a.activation_type,
                platform_id=a.platform_id,
                command=a.command,
                subcommand=a.subcommand,
                args=a.get_args(),
                working_dir=a.working_dir,
                host=a.host,
                port=a.port,
                health_check_endpoint=a.health_check_endpoint,
                base_url=a.base_url,
                endpoint=a.endpoint,
                method=a.method,
                requires_server=a.requires_server,
                server_command=a.server_command,
                url=a.url,
                event_type=a.event_type,
                env_vars={k: EnvVar(**v) for k, v in a.get_env_vars().items()},
                timeout=a.timeout,
            )
            for a in tool.activations
        ]

        # Build schemas
        parameters = ParameterSchema(**tool.get_parameters())
        structured_output = None
        if tool.structured_output:
            output_data = tool.get_structured_output()
            if output_data:
                structured_output = StructuredOutputSchema(**output_data)

        return ToolResponse(
            id=tool.id,
            name=tool.name,
            display_name=tool.display_name,
            description=tool.description,
            category=tool.category,
            tags=tool.get_tags(),
            subagent_name=tool.subagent.name,
            subagent_version=tool.subagent_version,
            prompts=prompts,
            parameters=parameters,
            structured_output=structured_output,
            activations=activations,
            inherit_activation=tool.inherit_activation,
            protocol=tool.protocol,
            implementation_hint=tool.implementation_hint,
            created_at=tool.created_at,
            updated_at=tool.updated_at,
        )

    def get_prompts(self, tool_name: str) -> List[ToolPromptModel]:
        """Get all prompts for a tool.

        Args:
            tool_name: Tool name

        Returns:
            List of prompt models
        """
        stmt = (
            select(ToolPromptModel)
            .join(ToolModel)
            .where(ToolModel.name == tool_name)
        )
        return list(self.session.execute(stmt).scalars().all())

    def get_prompt_by_name(self, tool_name: str, prompt_name: str) -> Optional[ToolPromptModel]:
        """Get a specific prompt for a tool.

        Args:
            tool_name: Tool name
            prompt_name: Prompt name

        Returns:
            Prompt model or None
        """
        stmt = (
            select(ToolPromptModel)
            .join(ToolModel)
            .where(ToolModel.name == tool_name)
            .where(ToolPromptModel.name == prompt_name)
        )
        return self.session.execute(stmt).scalar_one_or_none()
