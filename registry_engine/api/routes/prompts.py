"""Prompts API endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from jinja2 import Template, TemplateSyntaxError
from sqlalchemy.orm import Session

from registry_engine.api.dependencies import get_session, get_prompt_db
from registry_engine.database import PromptDB
from registry_engine.models.prompt import PromptRenderRequest, PromptRenderResponse, PromptResponse

router = APIRouter()


@router.get("/{subagent_name}", response_model=List[PromptResponse])
async def list_prompts(
    subagent_name: str,
    session: Session = Depends(get_session),
):
    """List all prompts for a subagent.

    Args:
        subagent_name: SubAgent name
        session: Database session

    Returns:
        List of prompts
    """
    prompt_db = PromptDB(session)
    prompts = prompt_db.get_by_subagent(subagent_name)

    return [
        PromptResponse(
            id=p.id,
            subagent_name=subagent_name,
            name=p.name,
            template=p.template,
            variables=p.get_variables(),
            format=p.format,
            description=p.description,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in prompts
    ]


@router.get("/{subagent_name}/{prompt_name}", response_model=PromptResponse)
async def get_prompt(
    subagent_name: str,
    prompt_name: str,
    session: Session = Depends(get_session),
):
    """Get a specific prompt template.

    Args:
        subagent_name: SubAgent name
        prompt_name: Prompt name
        session: Database session

    Returns:
        Prompt response

    Raises:
        HTTPException: If prompt not found
    """
    prompt_db = PromptDB(session)
    prompt = prompt_db.get_by_name(subagent_name, prompt_name)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_name}' not found for SubAgent '{subagent_name}'",
        )

    return PromptResponse(
        id=prompt.id,
        subagent_name=subagent_name,
        name=prompt.name,
        template=prompt.template,
        variables=prompt.get_variables(),
        format=prompt.format,
        description=prompt.description,
        created_at=prompt.created_at,
        updated_at=prompt.updated_at,
    )


@router.post("/{subagent_name}/{prompt_name}/render", response_model=PromptRenderResponse)
async def render_prompt(
    subagent_name: str,
    prompt_name: str,
    request: PromptRenderRequest,
    session: Session = Depends(get_session),
):
    """Render a prompt with variables.

    Args:
        subagent_name: SubAgent name
        prompt_name: Prompt name
        request: Render request with variables
        session: Database session

    Returns:
        Rendered prompt

    Raises:
        HTTPException: If prompt not found or rendering fails
    """
    prompt_db = PromptDB(session)
    prompt = prompt_db.get_by_name(subagent_name, prompt_name)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prompt '{prompt_name}' not found for SubAgent '{subagent_name}'",
        )

    try:
        if prompt.format == "jinja2":
            template = Template(prompt.template)
            rendered = template.render(**request.variables)
        elif prompt.format == "f-string":
            rendered = prompt.template.format(**request.variables)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported template format: {prompt.format}",
            )

        return PromptRenderResponse(rendered=rendered)

    except (TemplateSyntaxError, KeyError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to render prompt: {str(e)}",
        )
