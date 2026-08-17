from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Municipality, MunicipalitySourceCoverage, Source, SourceDiscovery
from app.sources.candidates import CANDIDATES, DECISIONS


def main():
    with SessionLocal() as db:
        for data in CANDIDATES:
            item = db.scalar(select(Source).where(Source.slug == data["slug"]))
            if not item:
                item = Source(
                    name=data["name"],
                    slug=data["slug"],
                    source_type=data["source_type"],
                    organisation=data["organisation"],
                    website_url=data["website_url"],
                    procurement_url=data["procurement_url"],
                    connector_type="UNASSIGNED",
                    status="REVIEW",
                    active=False,
                    priority=5,
                    polling_frequency="daily",
                    polling_interval_minutes=1440,
                )
                db.add(item)
                db.flush()
                db.add(
                    SourceDiscovery(
                        source_id=item.id,
                        discovered_by="Phase 4 research",
                        discovery_method="OFFICIAL_WEBSITE_RESEARCH",
                        evidence_url=data["procurement_url"],
                        notes=f"{data['why']}. {data['access']}",
                        verification_status=DECISIONS[data["slug"]],
                    )
                )
            code = {"ethekwini-municipality": "ETH", "msunduzi-municipality": "KZN225"}.get(
                data["slug"]
            )
            if code:
                municipality = db.scalar(select(Municipality).where(Municipality.code == code))
                if municipality and not db.scalar(
                    select(MunicipalitySourceCoverage).where(
                        MunicipalitySourceCoverage.municipality_id == municipality.id
                    )
                ):
                    db.add(
                        MunicipalitySourceCoverage(
                            municipality_id=municipality.id,
                            source_id=item.id,
                            official_website_url=data["website_url"],
                            source_identified=True,
                            procurement_url=data["procurement_url"],
                            verification_status="REVIEW",
                            source_mechanism=data["mechanism"],
                            connector_required=True,
                            connector_implemented=False,
                        )
                    )
        db.commit()
        print({"candidates": len(CANDIDATES), "active": 0, "status": "REVIEW"})


if __name__ == "__main__":
    main()
