"""Verified HTTPS requests with DNS and per-redirect SSRF enforcement."""

from __future__ import annotations

import asyncio
import inspect
import ipaddress
import socket
from collections.abc import Callable
from urllib.parse import urljoin, urlparse

import httpx


class OutboundSecurityError(httpx.RequestError):
    """A URL or redirect violated outbound source policy."""

    category = "ACCESS_RESTRICTION"


Resolver = Callable[[str], list[str]]


async def system_resolver(hostname: str) -> list[str]:
    records = await asyncio.to_thread(socket.getaddrinfo, hostname, 443, type=socket.SOCK_STREAM)
    return sorted({record[4][0] for record in records})


class OutboundUrlPolicy:
    def __init__(self, resolver: Resolver | None = None):
        self.resolver = resolver or system_resolver

    async def validate(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise OutboundSecurityError("outbound URL must use HTTPS")
        hostname = parsed.hostname.rstrip(".").casefold()
        if (
            hostname in {"localhost", "localhost.localdomain"}
            or hostname.endswith((".local", ".internal", ".localhost"))
            or "." not in hostname
        ):
            raise OutboundSecurityError("internal hostnames are prohibited")
        try:
            literal = ipaddress.ip_address(hostname)
            addresses = [str(literal)]
        except ValueError:
            resolved = self.resolver(hostname)
            addresses = await resolved if inspect.isawaitable(resolved) else resolved
        if not addresses:
            raise OutboundSecurityError("hostname did not resolve")
        parsed_addresses = [ipaddress.ip_address(address.split("%", 1)[0]) for address in addresses]
        if any(not address.is_global for address in parsed_addresses):
            raise OutboundSecurityError("hostname resolves to a private or special-use address")
        return url


class SecureRedirectClient:
    """Manually follows a maximum of five validated public HTTPS redirects."""

    def __init__(
        self,
        client: httpx.AsyncClient,
        policy: OutboundUrlPolicy | None = None,
        max_redirects: int = 5,
    ):
        self.client = client
        self.policy = policy or OutboundUrlPolicy()
        self.max_redirects = max_redirects

    async def get(self, url: str, **kwargs) -> httpx.Response:
        current = url
        for redirect_count in range(self.max_redirects + 1):
            await self.policy.validate(current)
            response = await self.client.get(
                current, follow_redirects=False, **(kwargs if redirect_count == 0 else {})
            )
            if response.status_code not in {301, 302, 303, 307, 308}:
                return response
            location = response.headers.get("location")
            if not location:
                return response
            if redirect_count >= self.max_redirects:
                raise OutboundSecurityError("redirect limit exceeded", request=response.request)
            current = urljoin(str(response.url), location)
        raise OutboundSecurityError("redirect limit exceeded")
