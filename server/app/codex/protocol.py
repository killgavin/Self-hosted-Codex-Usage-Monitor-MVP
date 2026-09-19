"""Version-specific initialization protocol DTOs.

These models define only the wire boundary. They do not send requests, manage
adapter state, or expose protocol fields to domain or REST layers.
"""

from decimal import Decimal
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


class GetAccountParams(WireModel):
    """Parameters for account/read; refresh is opt-in and defaults off."""

    refresh_token: bool = Field(default=False, alias="refreshToken")


class AccountProtocol(WireModel):
    """Forward-compatible account payload at the protocol boundary."""

    type: str | None = None
    email: str | None = None
    plan_type: str | None = Field(default=None, alias="planType")
    uses_codex_managed_credentials: bool | None = Field(
        default=None,
        alias="usesCodexManagedCredentials",
    )


class GetAccountResponse(WireModel):
    """Account/read response with nullable account data."""

    requires_openai_auth: bool = Field(alias="requiresOpenaiAuth")
    account: AccountProtocol | None = None


class DeviceCodeLoginParams(WireModel):
    """Parameters for the supported device-code login start variant."""

    type: Literal["chatgptDeviceCode"] = "chatgptDeviceCode"


class DeviceCodeLoginResponse(WireModel):
    """Required device-code fields returned by login start."""

    type: Literal["chatgptDeviceCode"]
    login_id: str = Field(alias="loginId")
    user_code: str = Field(alias="userCode")
    verification_url: str = Field(alias="verificationUrl")


class CancelLoginParams(WireModel):
    """Parameters for canceling one pending device-code login."""

    login_id: str = Field(alias="loginId")


class CancelLoginResponse(WireModel):
    """Forward-compatible result from account/login/cancel."""

    status: str


class LogoutAccountResponse(WireModel):
    """Forward-compatible object returned by account/logout."""


class RateLimitWindowProtocol(WireModel):
    """Wire rate window retaining lossless usage and nullable metadata."""

    used_percent: Decimal = Field(alias="usedPercent")
    window_duration_minutes: int | None = Field(default=None, alias="windowDurationMins")
    resets_at: int | None = Field(default=None, alias="resetsAt")


class RateLimitSnapshotProtocol(WireModel):
    """Wire snapshot with nullable generic identities and raw enum strings."""

    limit_id: str | None = Field(default=None, alias="limitId")
    limit_name: str | None = Field(default=None, alias="limitName")
    plan_type: str | None = Field(default=None, alias="planType")
    primary: RateLimitWindowProtocol | None = None
    secondary: RateLimitWindowProtocol | None = None
    rate_limit_reached_type: str | None = Field(default=None, alias="rateLimitReachedType")


class RateLimitResetCreditProtocol(WireModel):
    """Wire reset-credit detail preserving required and optional fields."""

    id: str
    status: str
    granted_at: int = Field(alias="grantedAt")
    reset_type: str = Field(alias="resetType")
    expires_at: int | None = Field(default=None, alias="expiresAt")
    title: str | None = None
    description: str | None = None


class RateLimitResetCreditsProtocol(WireModel):
    """Wire reset-credit summary preserving null versus empty details."""

    available_count: int = Field(alias="availableCount")
    credits: list[RateLimitResetCreditProtocol] | None = None


class GetAccountRateLimitsResponse(WireModel):
    """Verified account/rateLimits response DTO; mapping is a later boundary."""

    rate_limits: RateLimitSnapshotProtocol = Field(alias="rateLimits")
    rate_limits_by_limit_id: dict[str, RateLimitSnapshotProtocol] | None = Field(
        default=None,
        alias="rateLimitsByLimitId",
    )
    rate_limit_reset_credits: RateLimitResetCreditsProtocol | None = Field(
        default=None,
        alias="rateLimitResetCredits",
    )


class AccountLoginCompletedNotification(WireModel):
    """Boundary DTO for the account/login/completed notification params."""

    success: bool
    login_id: str | None = Field(default=None, alias="loginId")
    error: str | None = None


def to_wire(model: WireModel) -> dict[str, Any]:
    """Serialize a protocol DTO with wire aliases and no absent optionals."""

    return model.model_dump(by_alias=True, exclude_none=True)
