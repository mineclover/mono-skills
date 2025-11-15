"""Pydantic models for SubAgent Registry."""

from .subagent import (
    SubAgentMetadata,
    Installation,
    Activation,
    SubAgent,
    SubAgentCreate,
    SubAgentResponse,
)
from .prompt import PromptTemplate, PromptCreate, PromptResponse, PromptRenderRequest
from .interface import InterfaceSpec, Tool, StructuredOutput

__all__ = [
    "SubAgentMetadata",
    "Installation",
    "Activation",
    "SubAgent",
    "SubAgentCreate",
    "SubAgentResponse",
    "PromptTemplate",
    "PromptCreate",
    "PromptResponse",
    "PromptRenderRequest",
    "InterfaceSpec",
    "Tool",
    "StructuredOutput",
]
