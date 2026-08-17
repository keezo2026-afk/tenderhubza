"""Push provider boundary. Provider acceptance is submission, not delivery."""

from typing import Protocol

from app.core.config import Settings


class InvalidPushTokenError(RuntimeError):
    """The provider reports that a token is permanently unusable."""


class PushProvider(Protocol):
    async def send(self, token: str, data: dict[str, str]) -> str: ...


class DevelopmentPushProvider:
    async def send(self, token: str, data: dict[str, str]) -> str:
        raise RuntimeError("development push provider does not deliver")


class FirebasePushProvider:
    def __init__(self, settings: Settings):
        if not settings.firebase_credentials_file:
            raise RuntimeError("FIREBASE_CREDENTIALS_FILE is required")
        import firebase_admin
        from firebase_admin import credentials

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(
                credentials.Certificate(settings.firebase_credentials_file)
            )

    async def send(self, token: str, data: dict[str, str]) -> str:
        import asyncio

        from firebase_admin import exceptions, messaging

        message = messaging.Message(
            data=data,
            token=token,
            android=messaging.AndroidConfig(priority="high"),
        )
        try:
            return await asyncio.to_thread(messaging.send, message)
        except (messaging.UnregisteredError, messaging.SenderIdMismatchError) as exc:
            raise InvalidPushTokenError("push token is permanently invalid") from exc
        except exceptions.InvalidArgumentError as exc:
            raise InvalidPushTokenError("push token was rejected") from exc


def push_provider(settings: Settings) -> PushProvider:
    if settings.push_provider == "development":
        return DevelopmentPushProvider()
    if settings.push_provider == "firebase":
        return FirebasePushProvider(settings)
    raise RuntimeError(f"Unsupported PUSH_PROVIDER: {settings.push_provider}")
