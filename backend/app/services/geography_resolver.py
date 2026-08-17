"""Canonical geography resolution shared by all ingestion connectors."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import District, Municipality, Province


class GeographyMatchMethod(str, Enum):
    CODE = "CODE"
    EXACT_NAME = "EXACT_NAME"
    NORMALIZED_NAME = "NORMALIZED_NAME"
    ALIAS = "ALIAS"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class ResolvedGeographyLevel:
    id: str | None
    name: str | None
    confidence: float
    match_method: GeographyMatchMethod

    @property
    def resolved(self) -> bool:
        return self.id is not None


@dataclass(frozen=True)
class GeographyResolution:
    province: ResolvedGeographyLevel
    district: ResolvedGeographyLevel
    municipality: ResolvedGeographyLevel
    issues: tuple[str, ...] = field(default_factory=tuple)

    @property
    def resolved(self) -> bool:
        requested = [self.province, self.district, self.municipality]
        return all(level.resolved for level in requested if level.name is not None)


_UNRESOLVED = ResolvedGeographyLevel(None, None, 0.0, GeographyMatchMethod.UNRESOLVED)
_SUFFIXES = re.compile(
    r"\b(metropolitan|metro|local|district)?\s*municipality\b|\bmunicipal\s+area\b",
    re.IGNORECASE,
)


def normalize_geography_name(value: str | None) -> str:
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(
        character for character in decomposed if not unicodedata.combining(character)
    )
    without_suffix = _SUFFIXES.sub(" ", without_marks)
    alphanumeric = re.sub(r"[^a-zA-Z0-9]+", " ", without_suffix)
    return " ".join(alphanumeric.casefold().split())


class GeographyResolver:
    """Resolves source geography without guessing when relationships conflict."""

    DEFAULT_ALIASES = {
        "kwazulu natal": "KwaZulu-Natal",
        "kzn": "KwaZulu-Natal",
        "ethekwini metropolitan": "eThekwini",
        "city of ethekwini": "eThekwini",
        "umgungundlovu district": "uMgungundlovu",
        "msunduzi": "The Msunduzi",
    }

    def __init__(self, db: Session, aliases: dict[str, str] | None = None):
        self.db = db
        configured = aliases or self.DEFAULT_ALIASES
        self.aliases = {
            normalize_geography_name(source): normalize_geography_name(target)
            for source, target in configured.items()
        }

    def resolve(
        self,
        *,
        province: str | None = None,
        district: str | None = None,
        municipality: str | None = None,
        province_code: str | None = None,
        district_code: str | None = None,
        municipality_code: str | None = None,
    ) -> GeographyResolution:
        issues: list[str] = []
        province_result = self._resolve_level(Province, province, province_code)
        district_result = self._resolve_level(District, district, district_code)
        municipality_result = self._resolve_level(Municipality, municipality, municipality_code)

        district_record = self.db.get(District, district_result.id) if district_result.id else None
        municipality_record = (
            self.db.get(Municipality, municipality_result.id) if municipality_result.id else None
        )
        if (
            district_record
            and province_result.id
            and district_record.province_id != province_result.id
        ):
            issues.append("DISTRICT_PROVINCE_MISMATCH")
            district_result = self._unresolved(district)
        if (
            municipality_record
            and province_result.id
            and municipality_record.province_id != province_result.id
        ):
            issues.append("MUNICIPALITY_PROVINCE_MISMATCH")
            municipality_result = self._unresolved(municipality)
        if municipality_record and district_result.id:
            same_metro = (
                municipality_record.code and municipality_record.code == district_record.code
            )
            if municipality_record.district_id != district_result.id and not same_metro:
                issues.append("MUNICIPALITY_DISTRICT_MISMATCH")
                municipality_result = self._unresolved(municipality)
        for label, raw, result in [
            ("PROVINCE", province or province_code, province_result),
            ("DISTRICT", district or district_code, district_result),
            ("MUNICIPALITY", municipality or municipality_code, municipality_result),
        ]:
            if raw and not result.resolved and not any(label in issue for issue in issues):
                issues.append(f"{label}_UNRESOLVED")
        return GeographyResolution(
            province=province_result,
            district=district_result,
            municipality=municipality_result,
            issues=tuple(issues),
        )

    def _resolve_level(self, model, name: str | None, code: str | None) -> ResolvedGeographyLevel:
        if code:
            record = self.db.scalar(select(model).where(model.code == code.strip()))
            if record:
                return ResolvedGeographyLevel(
                    record.id, record.name, 1.0, GeographyMatchMethod.CODE
                )
        if not name:
            return _UNRESOLVED
        trimmed = name.strip()
        record = self.db.scalar(select(model).where(model.name == trimmed))
        if record:
            return ResolvedGeographyLevel(
                record.id, record.name, 1.0, GeographyMatchMethod.EXACT_NAME
            )
        normalized = normalize_geography_name(trimmed)
        alias_target = self.aliases.get(normalized)
        target = alias_target or normalized
        records = list(self.db.scalars(select(model)))
        matches = [record for record in records if normalize_geography_name(record.name) == target]
        if len(matches) != 1:
            return self._unresolved(name)
        method = (
            GeographyMatchMethod.ALIAS if alias_target else GeographyMatchMethod.NORMALIZED_NAME
        )
        confidence = 0.9 if alias_target else 0.95
        return ResolvedGeographyLevel(matches[0].id, matches[0].name, confidence, method)

    @staticmethod
    def _unresolved(source_name: str | None) -> ResolvedGeographyLevel:
        return ResolvedGeographyLevel(
            id=None,
            name=source_name,
            confidence=0.0,
            match_method=GeographyMatchMethod.UNRESOLVED,
        )
