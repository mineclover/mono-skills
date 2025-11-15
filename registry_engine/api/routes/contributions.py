"""User contribution API for adding tools and subagents."""

import yaml
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session
from registry_engine.database.models_v2 import ToolModel
from registry_engine.database.subagent_db_v2 import SubAgentDBV2
from registry_engine.database.tool_db import ToolDB
from registry_engine.models.tool_centric import (
    SubAgentCreate,
    ToolCreate,
    ToolPrompt,
    ParameterSchema,
    StructuredOutputSchema,
    Activation,
    Installation,
    SubAgentMetadata,
    Dependency,
)
from registry_engine.search.tool_indexer import ToolIndexer
from registry_engine.api.routes.search_v2 import get_qdrant_db

router = APIRouter()


class ContributionStatus(BaseModel):
    """Status of a contribution."""

    success: bool
    message: str
    tool_name: Optional[str] = None
    subagent_name: Optional[str] = None
    errors: Optional[List[str]] = None


class YAMLValidationResult(BaseModel):
    """YAML validation result."""

    valid: bool
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    parsed_data: Optional[Dict[str, Any]] = None


@router.post("/yaml/validate", response_model=YAMLValidationResult)
async def validate_yaml(
    file: UploadFile = File(..., description="YAML file to validate"),
):
    """Validate a YAML file without importing.

    Checks:
    - YAML syntax
    - Schema validation
    - Required fields
    - Data types

    Args:
        file: YAML file to validate

    Returns:
        Validation result
    """
    try:
        # Read file
        content = await file.read()
        data = yaml.safe_load(content)

        errors = []
        warnings = []

        # Check top-level structure
        if "subagent" not in data:
            errors.append("Missing 'subagent' section")
        if "tools" not in data or not data["tools"]:
            errors.append("Missing or empty 'tools' section")

        if errors:
            return YAMLValidationResult(valid=False, errors=errors)

        # Validate SubAgent
        try:
            subagent_data = data["subagent"]
            _validate_subagent(subagent_data, errors, warnings)
        except Exception as e:
            errors.append(f"SubAgent validation error: {str(e)}")

        # Validate Tools
        for i, tool_data in enumerate(data.get("tools", [])):
            try:
                _validate_tool(tool_data, i, errors, warnings)
            except Exception as e:
                errors.append(f"Tool {i} validation error: {str(e)}")

        if errors:
            return YAMLValidationResult(valid=False, errors=errors, warnings=warnings or None)

        return YAMLValidationResult(
            valid=True,
            warnings=warnings or None,
            parsed_data=data,
        )

    except yaml.YAMLError as e:
        return YAMLValidationResult(
            valid=False,
            errors=[f"YAML syntax error: {str(e)}"],
        )
    except Exception as e:
        return YAMLValidationResult(
            valid=False,
            errors=[f"Unexpected error: {str(e)}"],
        )


@router.post("/yaml/import", response_model=ContributionStatus)
async def import_yaml(
    file: UploadFile = File(..., description="YAML file to import"),
    auto_index: bool = True,
    session: Session = Depends(get_session),
):
    """Import a tool package from YAML file.

    Creates SubAgent and Tools, automatically indexes tools for search.

    Args:
        file: YAML file containing subagent and tools
        auto_index: Automatically index tools in search engine
        session: Database session

    Returns:
        Import status
    """
    try:
        # Read and validate
        content = await file.read()
        data = yaml.safe_load(content)

        # Validate first
        validation = await validate_yaml(file)
        if not validation.valid:
            return ContributionStatus(
                success=False,
                message="Validation failed",
                errors=validation.errors,
            )

        # Parse SubAgent
        subagent_data = _parse_subagent(data["subagent"])

        # Create SubAgent
        subagent_db = SubAgentDBV2(session)
        existing_subagent = subagent_db.get_by_name(subagent_data.metadata.name)

        if existing_subagent:
            return ContributionStatus(
                success=False,
                message=f"SubAgent '{subagent_data.metadata.name}' already exists",
                errors=[f"SubAgent '{subagent_data.metadata.name}' is already in the registry"],
            )

        subagent = subagent_db.create(subagent_data)

        # Parse and create Tools
        tool_db = ToolDB(session)
        created_tools = []

        for tool_data_raw in data["tools"]:
            tool_data = _parse_tool(tool_data_raw, subagent_data.metadata.name)

            # Check if tool exists
            existing_tool = tool_db.get_by_name(tool_data.name)
            if existing_tool:
                return ContributionStatus(
                    success=False,
                    message=f"Tool '{tool_data.name}' already exists",
                    errors=[f"Tool '{tool_data.name}' is already in the registry"],
                )

            tool = tool_db.create(tool_data)
            created_tools.append(tool)

        # Auto-index tools
        if auto_index:
            qdrant_db = get_qdrant_db()
            indexer = ToolIndexer(qdrant_db)
            for tool in created_tools:
                indexer.index_tool(tool)

        return ContributionStatus(
            success=True,
            message=f"Successfully imported {len(created_tools)} tool(s)",
            subagent_name=subagent.name,
            tool_name=created_tools[0].name if created_tools else None,
        )

    except yaml.YAMLError as e:
        return ContributionStatus(
            success=False,
            message="YAML parsing error",
            errors=[str(e)],
        )
    except ValidationError as e:
        return ContributionStatus(
            success=False,
            message="Validation error",
            errors=[str(err) for err in e.errors()],
        )
    except Exception as e:
        return ContributionStatus(
            success=False,
            message="Import failed",
            errors=[str(e)],
        )


@router.post("/tools/submit", response_model=ContributionStatus)
async def submit_tool(
    tool_data: ToolCreate,
    auto_index: bool = True,
    session: Session = Depends(get_session),
):
    """Submit a new tool via JSON.

    The associated SubAgent must already exist.

    Args:
        tool_data: Tool data to submit
        auto_index: Automatically index in search engine
        session: Database session

    Returns:
        Submission status
    """
    tool_db = ToolDB(session)

    # Check if tool exists
    existing = tool_db.get_by_name(tool_data.name)
    if existing:
        return ContributionStatus(
            success=False,
            message=f"Tool '{tool_data.name}' already exists",
            errors=[f"A tool with name '{tool_data.name}' is already in the registry"],
        )

    # Check if SubAgent exists
    subagent_db = SubAgentDBV2(session)
    subagent = subagent_db.get_by_name(tool_data.subagent_name)
    if not subagent:
        return ContributionStatus(
            success=False,
            message=f"SubAgent '{tool_data.subagent_name}' not found",
            errors=[
                f"The SubAgent '{tool_data.subagent_name}' does not exist. Please create it first or use an existing SubAgent."
            ],
        )

    try:
        # Create tool
        tool = tool_db.create(tool_data)

        # Auto-index
        if auto_index:
            qdrant_db = get_qdrant_db()
            indexer = ToolIndexer(qdrant_db)
            indexer.index_tool(tool)

        return ContributionStatus(
            success=True,
            message="Tool submitted successfully",
            tool_name=tool.name,
            subagent_name=subagent.name,
        )

    except Exception as e:
        return ContributionStatus(
            success=False,
            message="Submission failed",
            errors=[str(e)],
        )


@router.post("/subagents/submit", response_model=ContributionStatus)
async def submit_subagent(
    subagent_data: SubAgentCreate,
    session: Session = Depends(get_session),
):
    """Submit a new SubAgent via JSON.

    Args:
        subagent_data: SubAgent data to submit
        session: Database session

    Returns:
        Submission status
    """
    subagent_db = SubAgentDBV2(session)

    # Check if exists
    existing = subagent_db.get_by_name(subagent_data.metadata.name)
    if existing:
        return ContributionStatus(
            success=False,
            message=f"SubAgent '{subagent_data.metadata.name}' already exists",
            errors=[f"A SubAgent with name '{subagent_data.metadata.name}' is already in the registry"],
        )

    try:
        subagent = subagent_db.create(subagent_data)

        return ContributionStatus(
            success=True,
            message="SubAgent submitted successfully",
            subagent_name=subagent.name,
        )

    except Exception as e:
        return ContributionStatus(
            success=False,
            message="Submission failed",
            errors=[str(e)],
        )


# Helper functions

def _validate_subagent(data: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """Validate SubAgent data."""
    required_fields = ["name", "version", "description", "category"]
    for field in required_fields:
        if field not in data:
            errors.append(f"SubAgent: Missing required field '{field}'")

    if "installations" not in data or not data["installations"]:
        warnings.append("SubAgent: No installation methods provided")

    if "activations" not in data or not data["activations"]:
        warnings.append("SubAgent: No activation methods provided")


def _validate_tool(data: Dict[str, Any], index: int, errors: List[str], warnings: List[str]) -> None:
    """Validate Tool data."""
    prefix = f"Tool {index}"

    required_fields = ["name", "display_name", "description", "category", "parameters"]
    for field in required_fields:
        if field not in data:
            errors.append(f"{prefix}: Missing required field '{field}'")

    if "prompts" not in data or not data["prompts"]:
        warnings.append(f"{prefix}: No prompts provided")

    if "subagent_name" not in data:
        errors.append(f"{prefix}: Missing 'subagent_name' field")


def _parse_subagent(data: Dict[str, Any]) -> SubAgentCreate:
    """Parse SubAgent data from YAML."""
    metadata = SubAgentMetadata(**data)

    installations = [Installation(**inst) for inst in data.get("installations", [])]
    activations = [Activation(**act) for act in data.get("activations", [])]
    dependencies = [Dependency(**dep) for dep in data.get("dependencies", [])]

    return SubAgentCreate(
        metadata=metadata,
        installations=installations,
        activations=activations,
        dependencies=dependencies,
    )


def _parse_tool(data: Dict[str, Any], subagent_name: str) -> ToolCreate:
    """Parse Tool data from YAML."""
    prompts = [ToolPrompt(**p) for p in data.get("prompts", [])]
    parameters = ParameterSchema(**data["parameters"])
    structured_output = None
    if "structured_output" in data:
        structured_output = StructuredOutputSchema(**data["structured_output"])

    activations = [Activation(**a) for a in data.get("activations", [])]

    return ToolCreate(
        name=data["name"],
        display_name=data["display_name"],
        description=data["description"],
        category=data["category"],
        tags=data.get("tags", []),
        subagent_name=data.get("subagent_name", subagent_name),
        subagent_version=data.get("subagent_version", "1.0.0"),
        prompts=prompts,
        parameters=parameters,
        structured_output=structured_output,
        activations=activations,
        protocol=data.get("protocol", "langchain"),
        implementation_hint=data.get("implementation_hint"),
    )
