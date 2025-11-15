"""Pydantic models for SubAgent interfaces."""

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Tool definition in the interface."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Parameter schema (JSON Schema format)"
    )
    required_params: List[str] = Field(
        default_factory=list, description="List of required parameter names"
    )


class StructuredOutput(BaseModel):
    """Structured output schema definition."""

    name: str = Field(..., description="Schema name")
    schema_type: Literal["pydantic", "json_schema", "openai_function"] = Field(
        ..., description="Schema format type"
    )
    schema: Dict[str, Any] = Field(..., description="Schema definition")
    description: Optional[str] = Field(None, description="Schema description")


class InterfaceSpec(BaseModel):
    """Interface specification for a SubAgent."""

    protocol: Literal["langchain", "mcp", "openai_function", "custom"] = Field(
        ..., description="Protocol type"
    )
    tools: List[Tool] = Field(default_factory=list, description="Available tools")
    structured_outputs: List[StructuredOutput] = Field(
        default_factory=list, description="Structured output schemas"
    )
    capabilities: List[str] = Field(
        default_factory=list, description="Protocol-specific capabilities"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional interface metadata"
    )
