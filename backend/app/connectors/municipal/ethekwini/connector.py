import re
from datetime import datetime

from bs4 import BeautifulSoup

from app.connectors.base import ConnectorCapabilities, ConnectorHealth, TenderConnector
from app.connectors.html_support import BoundedHtmlClient
from app.ingestion.contracts import DiscoveredItem, DocumentReference, NormalizedTender


class EThekwiniConnector(TenderConnector):
    NAME = "ethekwini-municipality-procurement"
    VERSION = "1.0.0"
    LIST_URL = "https://www.durban.gov.za/pages/business/procurement"
    capabilities = ConnectorCapabilities(
        supports_documents=True, supports_updates=True, supports_html=True
    )

    def __init__(self, limit=25, client=None, resolver=None, max_redirects=5):
        self.limit = min(limit, 25)
        self.http = BoundedHtmlClient(client=client, resolver=resolver, max_redirects=max_redirects)
        self._listing = None

    async def discover(self):
        self._listing = await self.http.get(self.LIST_URL, "listing", self.VERSION)
        text = BeautifulSoup(self._listing.payload["html"], "html.parser").get_text(
            "\n", strip=True
        )
        refs = []
        for match in re.finditer(
            r"Reference\s*([A-Za-z0-9][A-Za-z0-9 /.-]{2,40}?)\s*Closing", text, re.I
        ):
            ref = " ".join(match.group(1).split())
            if ref not in refs:
                refs.append(ref)
        return [DiscoveredItem(ref, self.LIST_URL) for ref in refs[: self.limit]]

    async def fetch(self, item):
        if self._listing:
            from dataclasses import replace

            return replace(self._listing, source_identifier=item.source_identifier)
        return await self.http.get(self.LIST_URL, item.source_identifier, self.VERSION)

    async def parse(self, payload):
        text = BeautifulSoup(payload.payload["html"], "html.parser").get_text("\n", strip=True)
        ref = re.escape(payload.source_identifier)
        match = re.search(
            rf"(?:Tender\s+)?(?P<title>.+?)\s+(?:General\s*·\s*Tenders\s+)?Reference\s*{ref}\s*Closing\s*(?P<closing>\d{{2}}/\d{{2}}/\d{{4}}\s+\d{{2}}:\d{{2}})(?P<body>.*?)(?=\nTender\n|\Z)",
            text,
            re.I | re.S,
        )
        if not match:
            raise ValueError(f"Tender block not found for {payload.source_identifier}")
        body = match.group("body")

        def field(label):
            found = re.search(rf"{label}\s*\n?([^\n]+)", body, re.I)
            return found.group(1).strip() if found else None

        soup = BeautifulSoup(payload.payload["html"], "html.parser")
        documents = [
            {"name": a.get_text(" ", strip=True), "url": a["href"]}
            for a in soup.find_all("a", href=True)
            if a["href"].startswith("https://www.durban.gov.za/")
            and re.search(r"\.(pdf|docx?|xlsx?)($|\?)", a["href"], re.I)
        ]
        return {
            "reference": payload.source_identifier,
            "title": match.group("title").strip().split("\n")[-1],
            "closing": match.group("closing"),
            "description": field("Summary"),
            "contact": field("Contact Person"),
            "phone": field("Contact Number"),
            "email": field("Email"),
            "documents": documents,
        }

    async def normalize(self, p):
        closing = datetime.strptime(p["closing"], "%m/%d/%Y %H:%M")
        return NormalizedTender(
            source_reference=p["reference"],
            reference_number=p["reference"],
            title=p["title"],
            description=p["description"],
            organisation="eThekwini Metropolitan Municipality",
            province="KwaZulu-Natal",
            municipality="eThekwini Metropolitan Municipality",
            category="General",
            tender_type="Tender",
            closing_date=closing.date(),
            closing_time=closing.time(),
            source_url=self.LIST_URL,
            status="OPEN",
            contact_name=p["contact"],
            contact_email=p["email"],
            contact_phone=p["phone"],
            documents=[
                DocumentReference(d["name"] or "Tender document", d["url"]) for d in p["documents"]
            ],
        )

    async def download_documents(self, tender):
        return tender.documents

    async def health_check(self):
        return ConnectorHealth(True, "Official procurement page configured")
