"""Generic raw-first ingestion engine shared by every connector."""

from __future__ import annotations

import time
from dataclasses import asdict, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Protocol

import structlog
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.connectors.base import TenderConnector
from app.ingestion.contracts import NormalizedTender
from app.models import (
    ConnectorRun,
    ConnectorState,
    GeographyResolutionIssue,
    RawIngestion,
    Source,
    Tender,
    TenderDocument,
    TenderDuplicateCandidate,
    TenderSourceVersion,
)
from app.notifications import NotificationService
from app.services.geography_resolver import GeographyResolution, GeographyResolver

log = structlog.get_logger()


class SearchIndexer(Protocol):
    """Boundary for future external indexes; PostgreSQL currently indexes on persistence."""

    def index(self, tender: Tender) -> None: ...


class DatabaseSearchIndexer:
    def index(self, tender: Tender) -> None:
        return None


class IngestionEngine:
    """Owns source-independent transaction, identity, versioning and failure semantics."""

    def __init__(
        self,
        db: Session,
        connector: TenderConnector,
        geography_resolver: GeographyResolver | None = None,
        search_indexer: SearchIndexer | None = None,
    ):
        self.db = db
        self.connector = connector
        self.geography_resolver = geography_resolver or GeographyResolver(db)
        self.search_indexer = search_indexer or DatabaseSearchIndexer()

    async def run(self, source: Source, high_water_candidate=None) -> ConnectorRun:
        run = ConnectorRun(
            source_id=source.id,
            connector_name=self.connector.NAME,
            connector_version=self.connector.VERSION,
        )
        self.db.add(run)
        self.db.commit()
        started = time.monotonic()
        run_log = log.bind(
            source_id=source.id,
            connector=self.connector.NAME,
            connector_version=self.connector.VERSION,
            run_id=run.id,
        )
        try:
            items = list(await self.connector.discover())
            run.records_discovered = len(items)
            self.db.commit()
        except Exception as exc:
            run_log.warning("connector_discovery_failed", error_type=type(exc).__name__)
            return self._finish(run, "FAILED", exc, started, source, high_water_candidate)
        for item in items:
            raw = None
            try:
                payload = await self.connector.fetch(item)
                run.records_fetched += 1
                raw = self._persist_raw(source, payload)
                parsed = await self.connector.parse(payload)
                run.records_parsed += 1
                normalized = replace(
                    await self.connector.normalize(parsed), payload_hash=payload.checksum
                )
                run.records_normalized += 1
                errors = self._validate(normalized)
                if errors:
                    raise ValueError("; ".join(errors))
                resolution = self.geography_resolver.resolve(
                    province=normalized.province,
                    district=normalized.district,
                    municipality=normalized.municipality,
                    province_code=normalized.province_code,
                    district_code=normalized.district_code,
                    municipality_code=normalized.municipality_code,
                )
                action, tender = self._persist_canonical(source, raw, normalized, resolution)
                if action == "inserted":
                    run.records_inserted += 1
                elif action == "updated":
                    run.records_updated += 1
                else:
                    run.records_skipped += 1
                raw.normalization_status = "SUCCESS"
                raw.processing_status = "PERSISTED"
                raw.document_references = [asdict(document) for document in normalized.documents]
                self.search_indexer.index(tender)
                self.db.commit()
                run_log.info(
                    "ingestion_item_completed",
                    tender_id=tender.id,
                    source_identifier=item.source_identifier,
                    action=action,
                )
            except Exception as exc:
                self.db.rollback()
                run = self.db.get(ConnectorRun, run.id)
                if raw:
                    raw = self.db.get(RawIngestion, raw.id)
                    raw.normalization_status = "FAILED"
                    raw.processing_status = "FAILED"
                    raw.error = str(exc)[:2000]
                run.records_failed += 1
                run.error_count += 1
                run.last_error = str(exc)[:2000]
                self.db.commit()
                run_log.warning(
                    "ingestion_item_failed",
                    source_identifier=item.source_identifier,
                    error_type=type(exc).__name__,
                )
        completed = run.records_inserted + run.records_updated + run.records_skipped
        status = "SUCCESS" if run.records_failed == 0 else ("PARTIAL" if completed else "FAILED")
        return self._finish(run, status, None, started, source, high_water_candidate)

    def _persist_raw(self, source: Source, payload) -> RawIngestion:
        raw = RawIngestion(
            source_id=source.id,
            source_identifier=payload.source_identifier,
            original_source_url=payload.source_url,
            request_url=payload.request_url,
            http_status=payload.http_status,
            response_timestamp=payload.ingested_at,
            content_type=payload.content_type,
            raw_payload=payload.payload,
            ingested_at=payload.ingested_at,
            connector_version=payload.connector_version,
            payload_hash=payload.checksum,
            source_release_id=payload.source_release_id,
            ocds_identifier=payload.source_identifier,
            document_references=[],
            normalization_status="PENDING",
            processing_status="RAW_PERSISTED",
        )
        self.db.add(raw)
        self.db.commit()  # mandatory durability boundary before parse/normalize
        self.db.refresh(raw)
        return raw

    def _persist_canonical(
        self,
        source: Source,
        raw: RawIngestion,
        normalized: NormalizedTender,
        resolution: GeographyResolution,
    ) -> tuple[str, Tender]:
        tender = self.db.scalar(
            select(Tender).where(
                Tender.source_id == source.id,
                Tender.source_reference == normalized.source_reference,
            )
        )
        values = {
            key: value
            for key, value in asdict(normalized).items()
            if key not in {"documents", "province_code", "district_code", "municipality_code"}
        }
        values.update(
            province_id=resolution.province.id,
            district_id=resolution.district.id,
            municipality_id=resolution.municipality.id,
        )
        if resolution.province.resolved:
            values["province"] = resolution.province.name
        if resolution.district.resolved:
            values["district"] = resolution.district.name
        if resolution.municipality.resolved:
            values["municipality"] = resolution.municipality.name
        geography_unchanged = tender and all(
            getattr(tender, key) == values[key]
            for key in ["province_id", "district_id", "municipality_id"]
        )
        if tender and tender.payload_hash == normalized.payload_hash and geography_unchanged:
            return "skipped", tender
        if tender:
            changes = {
                key: {"from": str(getattr(tender, key)), "to": str(value)}
                for key, value in values.items()
                if hasattr(tender, key) and getattr(tender, key) != value
            }
            old_documents = set(
                self.db.scalars(
                    select(TenderDocument.source_url).where(TenderDocument.tender_id == tender.id)
                )
            )
            new_documents = {document.url for document in normalized.documents}
            if old_documents != new_documents:
                changes["documents"] = {
                    "from": sorted(old_documents),
                    "to": sorted(new_documents),
                }
            for key, value in values.items():
                if hasattr(tender, key):
                    setattr(tender, key, value)
            self.db.query(TenderDocument).filter(TenderDocument.tender_id == tender.id).delete()
            action = "updated"
        else:
            tender = Tender(source_id=source.id, **values)
            self.db.add(tender)
            self.db.flush()
            changes = {"created": True}
            action = "inserted"
        for document in normalized.documents:
            self.db.add(
                TenderDocument(
                    tender_id=tender.id,
                    name=document.name,
                    source_url=document.url,
                    mime_type=document.media_type,
                )
            )
        version = TenderSourceVersion(
            tender_id=tender.id,
            raw_ingestion_id=raw.id,
            change_summary=changes,
        )
        self.db.add(version)
        self.db.flush()
        self._record_geography_issues(source, raw, tender, normalized, resolution)
        notifications = NotificationService(self.db)
        if action == "inserted":
            notifications.match_new_tender(tender)
        else:
            notifications.notify_update(tender, version.id, changes)
        if action == "inserted" and tender.reference_number:
            candidate = self.db.scalar(
                select(Tender)
                .where(
                    Tender.source_id != source.id,
                    Tender.reference_number == tender.reference_number,
                    Tender.organisation == tender.organisation,
                )
                .limit(1)
            )
            if candidate:
                self.db.add(
                    TenderDuplicateCandidate(
                        tender_id=tender.id,
                        candidate_tender_id=candidate.id,
                        confidence=Decimal("1.0000"),
                        match_method="EXACT_REFERENCE_ORGANISATION",
                        signals=["REFERENCE_MATCH", "ORGANISATION_MATCH"],
                        reason="same reference number and organisation across sources",
                    )
                )
        self.db.flush()
        return action, tender

    def _record_geography_issues(self, source, raw, tender, normalized, resolution) -> None:
        if not resolution.issues:
            return
        self.db.add(
            GeographyResolutionIssue(
                source_id=source.id,
                raw_ingestion_id=raw.id,
                tender_id=tender.id,
                province_value=normalized.province,
                district_value=normalized.district,
                municipality_value=normalized.municipality,
                reason=resolution.issues[0],
                details={
                    "issues": list(resolution.issues),
                    "province_method": resolution.province.match_method.value,
                    "district_method": resolution.district.match_method.value,
                    "municipality_method": resolution.municipality.match_method.value,
                },
            )
        )

    @staticmethod
    def _validate(tender: NormalizedTender) -> list[str]:
        errors: list[str] = []
        if not tender.source_reference or len(tender.source_reference) > 255:
            errors.append("valid source reference is required")
        if not tender.title or len(tender.title) > 500:
            errors.append("valid title is required")
        if not tender.organisation or len(tender.organisation) > 255:
            errors.append("valid organisation is required")
        if tender.reference_number and len(tender.reference_number) > 255:
            errors.append("reference number is too long")
        if tender.contact_email and len(tender.contact_email) > 320:
            errors.append("contact email is too long")
        if not tender.source_url.startswith("https://") or len(tender.source_url) > 2048:
            errors.append("valid HTTPS source URL is required")
        if tender.estimated_value is not None and tender.estimated_value < 0:
            errors.append("estimated value cannot be negative")
        return errors

    def _finish(self, run, status, error, started, source, high_water_candidate=None):
        run = self.db.get(ConnectorRun, run.id)
        run.status = status
        run.completed_at = datetime.now(UTC)
        run.duration_seconds = Decimal(str(round(time.monotonic() - started, 3)))
        if error:
            run.error_count += 1
            run.last_error = str(error)[:2000]
        if status == "SUCCESS":
            source.last_successful_run = run.completed_at
            source.last_error = None
            if high_water_candidate is not None:
                state = self.db.get(ConnectorState, source.id) or ConnectorState(
                    source_id=source.id
                )
                state.high_water_date = high_water_candidate
                state.last_run_id = run.id
                self.db.add(state)
        elif status in {"FAILED", "PARTIAL"}:
            source.last_failed_run = run.completed_at
            source.last_error = run.last_error
        self.db.commit()
        self.db.refresh(run)
        return run
