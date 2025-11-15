"""Tools API endpoints."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session
from registry_engine.database.tool_db import ToolDB
from registry_engine.models.tool_centric import ToolCreate, ToolResponse

router = APIRouter()


@router.get("/", response_model=List[ToolResponse])
async def list_tools(
    category: Optional[str] = None,
    subagent: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
):
    """List all tools with optional filtering.

    Args:
        category: Filter by category (optional)
        subagent: Filter by SubAgent name (optional)
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records (default: 100)
        session: Database session

    Returns:
        List of Tool responses
    """
    tool_db = ToolDB(session)
    tools = tool_db.list(category=category, subagent_name=subagent, skip=skip, limit=limit)
    return [tool_db.to_response(t) for t in tools]


@router.get("/{tool_name}", response_model=ToolResponse)
async def get_tool(
    tool_name: str,
    session: Session = Depends(get_session),
):
    """Get detailed information about a specific tool.

    Args:
        tool_name: Tool name
        session: Database session

    Returns:
        Tool response

    Raises:
        HTTPException: If tool not found
    """
    tool_db = ToolDB(session)
    tool = tool_db.get_by_name(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    return tool_db.to_response(tool)


@router.post("/", response_model=ToolResponse, status_code=status.HTTP_201_CREATED)
async def create_tool(
    tool_data: ToolCreate,
    session: Session = Depends(get_session),
):
    """Create a new tool.

    Args:
        tool_data: Tool data to create
        session: Database session

    Returns:
        Created Tool response

    Raises:
        HTTPException: If tool already exists or SubAgent not found
    """
    tool_db = ToolDB(session)

    # Check if already exists
    existing = tool_db.get_by_name(tool_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tool '{tool_data.name}' already exists",
        )

    try:
        tool = tool_db.create(tool_data)
        return tool_db.to_response(tool)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{tool_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tool(
    tool_name: str,
    session: Session = Depends(get_session),
):
    """Delete a tool.

    Args:
        tool_name: Tool name
        session: Database session

    Raises:
        HTTPException: If tool not found
    """
    tool_db = ToolDB(session)
    deleted = tool_db.delete(tool_name)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )


@router.get("/{tool_name}/prompts")
async def get_tool_prompts(
    tool_name: str,
    session: Session = Depends(get_session),
):
    """Get all prompts for a tool.

    Args:
        tool_name: Tool name
        session: Database session

    Returns:
        List of prompts
    """
    tool_db = ToolDB(session)
    tool = tool_db.get_by_name(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    prompts = tool_db.get_prompts(tool_name)
    return [
        {
            "name": p.name,
            "description": p.description,
            "template_type": p.template_type,
            "system_message": p.system_message,
            "human_message_template": p.human_message_template,
            "ai_message_prefix": p.ai_message_prefix,
            "examples": p.get_examples(),
            "input_variables": p.get_input_variables(),
            "partial_variables": p.get_partial_variables(),
            "template": p.template,
        }
        for p in prompts
    ]


@router.get("/{tool_name}/prompts/{prompt_name}")
async def get_tool_prompt(
    tool_name: str,
    prompt_name: str,
    session: Session = Depends(get_session),
):
    """Get a specific prompt for a tool.

    Args:
        tool_name: Tool name
        prompt_name: Prompt name
        session: Database session

    Returns:
        Prompt details
    """
    tool_db = ToolDB(session)
    prompt = tool_db.get_prompt_by_name(tool_name, prompt_name)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_name}' not found for tool '{tool_name}'",
        )

    return {
        "name": prompt.name,
        "description": prompt.description,
        "template_type": prompt.template_type,
        "system_message": prompt.system_message,
        "human_message_template": prompt.human_message_template,
        "ai_message_prefix": prompt.ai_message_prefix,
        "examples": prompt.get_examples(),
        "input_variables": prompt.get_input_variables(),
        "partial_variables": prompt.get_partial_variables(),
        "template": prompt.template,
    }


@router.get("/{tool_name}/schema")
async def get_tool_schema(
    tool_name: str,
    session: Session = Depends(get_session),
):
    """Get structured output schema for a tool.

    Args:
        tool_name: Tool name
        session: Database session

    Returns:
        Schema details (JSON Schema, Pydantic code, TypeScript type)
    """
    tool_db = ToolDB(session)
    tool = tool_db.get_by_name(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    if not tool.structured_output:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' does not have a structured output schema",
        )

    output_data = tool.get_structured_output()
    return output_data


@router.get("/{tool_name}/install")
async def get_tool_installation(
    tool_name: str,
    session: Session = Depends(get_session),
):
    """Get installation information for a tool.

    Combines tool info with SubAgent installation methods.

    Args:
        tool_name: Tool name
        session: Database session

    Returns:
        Installation information
    """
    tool_db = ToolDB(session)
    tool = tool_db.get_by_name(tool_name)

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )

    from registry_engine.database.subagent_db_v2 import SubAgentDBV2

    subagent_db = SubAgentDBV2(session)
    subagent = subagent_db.get_by_id(tool.subagent_id)

    if not subagent:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SubAgent not found",
        )

    return {
        "tool_name": tool.name,
        "subagent_name": subagent.name,
        "subagent_version": subagent.version,
        "installations": [
            {
                "method": inst.method,
                "platform_id": inst.platform_id,
                "package_name": inst.package_name,
                "package_version": inst.package_version,
                "registry_url": inst.registry_url,
                "repository": inst.repository,
                "branch": inst.branch,
                "image": inst.image,
                "download_url": inst.download_url,
                "api_endpoint": inst.api_endpoint,
                "requires_install": inst.requires_install,
                "post_install_commands": inst.get_post_install_commands(),
                "platforms": inst.get_platforms(),
                "arch": inst.get_arch(),
            }
            for inst in subagent.installations
        ],
        "activations": [
            {
                "type": act.activation_type,
                "platform_id": act.platform_id,
                "command": act.command,
                "subcommand": act.subcommand,
                "args": act.get_args(),
                "url": act.url,
                "port": act.port,
                "endpoint": act.endpoint,
            }
            for act in (tool.activations if tool.activations else subagent.activations)
        ],
    }
