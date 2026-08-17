"""Password reset delivery boundary. No delivery adapter is configured in Phase 0."""

from typing import Protocol


class PasswordResetDelivery(Protocol):
    async def send_reset_link(self, *, email: str, one_time_token: str) -> None: ...


class PasswordResetNotConfigured(RuntimeError):
    pass
