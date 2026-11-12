"""Validation shared by MCP tool inputs."""

from typing import Annotated

from pydantic import Field

Text = Annotated[str, Field(min_length=1)]
Limit = Annotated[int, Field(ge=1, le=100)]
Confidence = Annotated[float, Field(ge=0, le=1)]
IDs = Annotated[list[Text], Field(min_length=1, max_length=1000)]
READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}
