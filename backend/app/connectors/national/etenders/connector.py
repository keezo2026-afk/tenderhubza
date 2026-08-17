import asyncio
import hashlib
import json
import mimetypes
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import quote, urlparse

import httpx
import structlog

from app.connectors.base import ConnectorCapabilities, TenderConnector
from app.ingestion.contracts import DiscoveredItem, DocumentReference, NormalizedTender, RawPayload

log = structlog.get_logger()


class PermanentSourceError(ValueError):
    pass


class ETendersConnector(TenderConnector):
    NAME = "national-treasury-etenders-ocds"
    VERSION = "1.0.0"
    capabilities = ConnectorCapabilities(
        supports_incremental=True,
        supports_documents=True,
        supports_updates=True,
        supports_pagination=True,
        supports_date_filtering=True,
        supports_api=True,
    )
    BASE_URL = "https://ocds-api.etenders.gov.za"
    LIST_PATH = "/api/OCDSReleases"

    def __init__(
        self,
        page_number: int = 1,
        page_size: int = 100,
        date_from: date | None = None,
        date_to: date | None = None,
        timeout: float = 30,
        max_attempts: int = 3,
        client: httpx.AsyncClient | None = None,
        max_pages: int = 100,
    ):
        self.page_number = page_number
        self.page_size = min(page_size, 1000)
        self.date_from = date_from
        self.date_to = date_to
        self.timeout = timeout
        self.max_attempts = max_attempts
        self._client = client
        self.max_pages = max_pages

    async def _request(self, url: str, params: dict | None = None) -> httpx.Response:
        own = self._client is None
        client = self._client or httpx.AsyncClient(
            timeout=self.timeout,
            headers={"Accept": "application/json", "User-Agent": "TenderHubSA/1.0"},
        )
        try:
            for attempt in range(1, self.max_attempts + 1):
                try:
                    response = await client.get(url, params=params)
                    if response.status_code in (408, 429) or response.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            "transient upstream response",
                            request=response.request,
                            response=response,
                        )
                    if response.status_code >= 400:
                        raise PermanentSourceError(
                            f"eTender API returned HTTP {response.status_code}"
                        )
                    return response
                except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                    category = _network_category(exc)
                    status = getattr(getattr(exc, "response", None), "status_code", None)
                    log.warning(
                        "connector_request_failed",
                        connector=self.NAME,
                        host=httpx.URL(url).host,
                        attempt=attempt,
                        max_attempts=self.max_attempts,
                        category=category,
                        error_type=type(exc).__name__,
                        http_status=status,
                        retrying=attempt < self.max_attempts,
                    )
                    if attempt == self.max_attempts:
                        raise
                    delay = min(2 ** (attempt - 1), 8)
                    await asyncio.sleep(delay)
        finally:
            if own:
                await client.aclose()

    async def discover(self):
        discovered = []
        for page in range(self.page_number, self.page_number + self.max_pages):
            params = {"PageNumber": page, "PageSize": self.page_size}
            if self.date_from:
                params["dateFrom"] = self.date_from.isoformat()
            if self.date_to:
                params["dateTo"] = self.date_to.isoformat()
            response = await self._request(self.BASE_URL + self.LIST_PATH, params)
            package = response.json()
            releases = package.get("releases") or []
            discovered.extend(
                DiscoveredItem(
                    str(r.get("ocid") or r.get("id") or ""),
                    f"{self.BASE_URL}{self.LIST_PATH}/release/{quote(str(r.get('ocid') or ''))}",
                    r.get("id"),
                )
                for r in releases
                if r.get("ocid") or r.get("id")
            )
            log.info(
                "connector_discovery_page", connector=self.NAME, page=page, records=len(releases)
            )
            if len(releases) < self.page_size:
                break
            if page == self.page_number + self.max_pages - 1:
                raise RuntimeError(
                    "discovery page safety limit reached; high-water mark will not advance"
                )
        return discovered

    async def fetch(self, item: DiscoveredItem) -> RawPayload:
        response = await self._request(item.url)
        payload = response.json()
        encoded = json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        return RawPayload(
            item.source_identifier,
            item.url,
            payload,
            datetime.now(UTC),
            self.VERSION,
            response.status_code,
            response.headers.get("content-type"),
            str(response.request.url),
            hashlib.sha256(encoded).hexdigest(),
            payload.get("id") or item.release_id,
        )

    async def parse(self, payload: RawPayload) -> dict:
        return payload.payload

    async def normalize(self, release: dict) -> NormalizedTender:
        tender = release.get("tender")
        if not isinstance(tender, dict):
            raise PermanentSourceError("release has no tender object")
        ocid = _text(release.get("ocid"))
        source_ref = ocid or _text(tender.get("id"))
        title = _text(tender.get("title"))
        organisation = _text(
            (release.get("buyer") or {}).get("name")
            or (tender.get("procuringEntity") or {}).get("name")
        )
        if not source_ref or not title or not organisation:
            raise PermanentSourceError("release requires ocid/tender id, title and buyer")
        period = tender.get("tenderPeriod") or {}
        start = _datetime(period.get("startDate"))
        end = _datetime(period.get("endDate"))
        contact = tender.get("contactPerson") or {}
        value = tender.get("value") or {}
        classification = tender.get("classification") or {}
        documents = []
        for d in tender.get("documents") or []:
            if isinstance(d, dict) and _safe_external_url(d.get("url")):
                documents.append(
                    DocumentReference(
                        _text(d.get("title")) or _text(d.get("description")) or "Tender document",
                        str(d["url"]),
                        _text(d.get("format")) or mimetypes.guess_type(str(d["url"]))[0],
                        _text(d.get("id")),
                    )
                )
        status = {
            "active": "OPEN",
            "planned": "UPCOMING",
            "complete": "CLOSED",
            "cancelled": "CANCELLED",
            "unsuccessful": "CANCELLED",
        }.get(str(tender.get("status") or "").lower(), str(tender.get("status") or "OPEN").upper())
        amount = None
        try:
            if value.get("amount") is not None:
                amount = Decimal(str(value["amount"]))
        except InvalidOperation:
            pass
        return NormalizedTender(
            source_reference=source_ref,
            title=title,
            organisation=organisation,
            source_url=f"{self.BASE_URL}{self.LIST_PATH}/release/{quote(source_ref)}",
            description=_text(tender.get("description")),
            reference_number=_text(tender.get("id")),
            province=_text(tender.get("province")),
            municipality=_text(tender.get("deliveryLocation")),
            category=_text(
                tender.get("category")
                or tender.get("mainProcurementCategory")
                or classification.get("description")
            ),
            subcategory=_text(classification.get("id")),
            tender_type=_text(
                tender.get("procurementMethodDetails") or tender.get("procurementMethod")
            ),
            issue_date=start.date() if start else None,
            closing_date=end.date() if end else None,
            closing_time=end.time().replace(tzinfo=None) if end else None,
            estimated_value=amount,
            currency=_text(value.get("currency")) or "ZAR",
            status=status,
            contact_name=_text(contact.get("name")),
            contact_email=_text(contact.get("email")),
            contact_phone=_text(contact.get("telephoneNumber")),
            source_release_id=_text(release.get("id")),
            ocds_identifier=ocid,
            documents=documents,
        )

    async def download_documents(self, tender: NormalizedTender):
        return tender.documents


def _text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _safe_external_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.hostname)


def _network_category(exc):
    text = str(exc).lower()
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if "certificate" in text:
        return "certificate_verification"
    if "ssl" in text or "tls" in text:
        return "tls_negotiation"
    if "name or service" in text or "nodename" in text:
        return "dns"
    if isinstance(exc, httpx.HTTPStatusError):
        return "upstream_http"
    return "transport"
