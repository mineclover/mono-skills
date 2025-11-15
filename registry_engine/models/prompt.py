"""Pydantic models for Prompt templates."""

from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, Field


class PromptTemplate(BaseModel):
    """Prompt template definition."""

    name: str = Field(..., description="Prompt name (e.g., 'system', 'user_template')")
    template: str = Field(..., description="Jinja2 template string")
    variables: Dict[str, str] = Field(
        default_factory=dict, description="Variable definitions with descriptions"
    )
    format: Literal["jinja2", "f-string"] = Field(
        default="jinja2", description="Template format"
    )
    description: Optional[str] = Field(None, description="Description of this prompt")


class PromptCreate(BaseModel):
    """Request model for creating a prompt."""

    subagent_name: str = Field(..., description="SubAgent name this prompt belongs to")
    name: str = Field(..., description="Prompt name")
    template: str = Field(..., description="Template string")
    variables: Dict[str, str] = Field(default_factory=dict)
    format: Literal["jinja2", "f-string"] = Field(default="jinja2")
    description: Optional[str] = None


class PromptResponse(PromptTemplate):
    """Response model for Prompt with metadata."""

    id: int = Field(..., description="Database ID")
    subagent_name: str = Field(..., description="SubAgent name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class PromptRenderRequest(BaseModel):
    """Request model for rendering a prompt."""

    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Variables to render the template with"
    )


class PromptRenderResponse(BaseModel):
    """Response model for rendered prompt."""

    rendered: str = Field(..., description="Rendered prompt text")
