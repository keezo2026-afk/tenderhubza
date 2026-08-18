import asyncio
import hashlib
from datetime import UTC, datetime

import httpx

from app.connectors.outbound import OutboundUrlPolicy, SecureRedirectClient
from app.ingestion.contracts import RawPayload


class BoundedHtmlClient:
    def __init__(self, timeout=30, max_attempts=3, client=None, resolver=None, max_redirects=5):
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.client = client
        self.policy = OutboundUrlPolicy(resolver)
        self.max_redirects = max_redirects

    async def get(self, url, source_identifier, version):
        own = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=False,
            headers={"User-Agent": "TenderHubSA/1.0", "Accept": "text/html"},
        )
        try:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = await SecureRedirectClient(
                        client, self.policy, self.max_redirects
                    ).get(url)
                    response.raise_for_status()
                    body = response.text
                    return RawPayload(
                        source_identifier,
                        url,
                        {"html": body},
                        datetime.now(UTC),
                        version,
                        response.status_code,
                        response.headers.get("content-type"),
                        str(response.url),
                        hashlib.sha256(body.encode()).hexdigest(),
                    )
                except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError):
                    if attempt == self.max_attempts:
                        raise
                    await asyncio.sleep(min(2 ** (attempt - 1), 8))
        finally:
            if own:
                await client.aclose()
