import asyncio
import hashlib
from datetime import UTC, datetime

import httpx

from app.ingestion.contracts import RawPayload


class BoundedHtmlClient:
    def __init__(self, timeout=30, max_attempts=3, client=None):
        self.timeout = timeout
        self.max_attempts = max_attempts
        self.client = client

    async def get(self, url, source_identifier, version):
        own = self.client is None
        client = self.client or httpx.AsyncClient(
            timeout=self.timeout,
            follow_redirects=True,
            headers={"User-Agent": "TenderHubSA/1.0", "Accept": "text/html"},
        )
        try:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = await client.get(url)
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
