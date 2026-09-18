"""Version-specific initialization protocol DTOs.

These models define only the wire boundary. They do not send requests, manage
adapter state, or expose protocol fields to domain or REST layers.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WireModel(BaseModel):
    """Base DTO preserving fields added by newer protocol versions."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ClientInfo(WireModel):
    """Client identity required by the initialize request."""

    name: str
    version: str
    title: str | None = None


class InitializeCapabilities(WireModel):
    """Optional capability flags supported by this protocol version."""

    experimental_api: bool = Field(default=False, alias="experimentalApi")
    extensions: dict[str, Any] | None = None
    mcp_server_openai_form_elicitation: bool | None = Field(
        default=None,
        alias="mcpServerOpenaiFormElicitation",
    )
    opt_out_notification_methods: list[str] | None = Field(
        default=None,
        alias="optOutNotificationMethods",
    )
    request_attestation: bool = Field(default=False, alias="requestAttestation")


class InitializeParams(WireModel):
    """Parameters for the initialize request."""

    client_info: ClientInfo = Field(alias="clientInfo")
    capabilities: InitializeCapabilities | None = None


class InitializeResponse(WireModel):
    """Required environment details returned by initialize."""

    codex_home: str = Field(alias="codexHome")
    platform_family: str = Field(alias="platformFamily")
    platform_os: str = Field(alias="platformOs")
    user_agent: str = Field(alias="userAgent")


class InitializedNotification(WireModel):
    """The initialized client notification sent after initialization."""

    method: Literal["initialized"] = "initialized"


def to_wire(model: WireModel) -> dict[str, Any]:
    """Serialize a protocol DTO with wire aliases and no absent optionals."""

    return model.model_dump(by_alias=True, exclude_none=True)
