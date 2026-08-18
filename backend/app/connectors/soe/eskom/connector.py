import re
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.connectors.base import ConnectorCapabilities, ConnectorHealth, TenderConnector
from app.connectors.html_support import BoundedHtmlClient
from app.ingestion.contracts import DiscoveredItem, DocumentReference, NormalizedTender


class EskomConnector(TenderConnector):
    NAME = "eskom-tender-bulletin"
    VERSION = "1.0.0"
    BASE = "https://tenderbulletin.eskom.co.za"
    capabilities = ConnectorCapabilities(
        supports_documents=True,
        supports_updates=True,
        supports_pagination=True,
        supports_html=True,
        supports_api=True,
    )

    def __init__(self, page_size=10, page_number=1, client=None, resolver=None, max_redirects=5):
        self.page_size = min(page_size, 25)
        self.page_number = page_number
        self.http = BoundedHtmlClient(client=client, resolver=resolver, max_redirects=max_redirects)

    async def discover(self):
        url = f"{self.BASE}/?pageSize={self.page_size}&pageNumber={self.page_number}"
        raw = await self.http.get(url, "listing", self.VERSION)
        soup = BeautifulSoup(raw.payload["html"], "html.parser")
        items = []
        for anchor in soup.find_all("a", href=re.compile(r"^/tender/\d+$")):
            identifier = anchor["href"].rstrip("/").split("/")[-1]
            if identifier not in {x.source_identifier for x in items}:
                items.append(DiscoveredItem(identifier, urljoin(self.BASE, anchor["href"])))
        return items[: self.page_size]

    async def fetch(self, item):
        return await self.http.get(item.url, item.source_identifier, self.VERSION)

    async def parse(self, payload):
        soup = BeautifulSoup(payload.payload["html"], "html.parser")
        text = soup.get_text("\n", strip=True)

        def value(label, next_labels):
            stop = "|".join(re.escape(x) for x in next_labels)
            m = re.search(rf"{re.escape(label)}\s*(.*?)(?={stop}|\Z)", text, re.I | re.S)
            return " ".join(m.group(1).split()) if m else None

        docs = [
            {
                "name": a.get_text(" ", strip=True) or "Tender document",
                "url": urljoin(self.BASE, a["href"]),
            }
            for a in soup.find_all(
                "a", href=re.compile(r"/webapi/api/Files/GetFile\?FileID=\d+", re.I)
            )
        ]
        labels = [
            "Enquiry Number",
            "Closing Date & Time",
            "Tender box address",
            "Target audience",
            "Contract type",
            "Scope details",
            "Description",
            "Supporting documents",
        ]
        return {
            "id": payload.source_identifier,
            "enquiry": value("Enquiry Number", labels[1:]),
            "closing": value("Closing Date & Time", labels[2:]),
            "address": value("Tender box address", labels[3:]),
            "contract_type": value("Contract type", labels[5:]),
            "scope": value("Scope details", labels[6:]),
            "description": value("Description", labels[7:]),
            "documents": docs,
            "url": payload.source_url,
        }

    async def normalize(self, p):
        closing = datetime.strptime(p["closing"], "%Y-%b-%d %H:%M:%S") if p["closing"] else None
        title = p["description"] or p["scope"] or p["enquiry"] or f"Eskom tender {p['id']}"
        province = next(
            (
                x
                for x in [
                    "Gauteng",
                    "Free State",
                    "Limpopo",
                    "Mpumalanga",
                    "North West",
                    "Northern Cape",
                    "Eastern Cape",
                    "Western Cape",
                    "KwaZulu-Natal",
                ]
                if x.lower() in (p["address"] or "").lower()
            ),
            None,
        )
        return NormalizedTender(
            source_reference=p["id"],
            reference_number=p["enquiry"],
            title=title,
            description=p["scope"] or p["description"],
            organisation="Eskom Holdings SOC Ltd",
            province=province,
            tender_type=p["contract_type"],
            closing_date=closing.date() if closing else None,
            closing_time=closing.time() if closing else None,
            source_url=p["url"],
            status="OPEN",
            documents=[DocumentReference(d["name"], d["url"]) for d in p["documents"]],
        )

    async def download_documents(self, tender):
        return tender.documents

    async def health_check(self):
        return ConnectorHealth(True, "Official bounded bulletin listing configured")
