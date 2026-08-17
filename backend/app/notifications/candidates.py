"""Database candidate narrowing before exact saved-search evaluation."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import NotificationPreference, SavedSearch, Tender


class SavedSearchCandidateRepository:
    """Narrows equality filters in SQL; Python matching remains the semantic authority."""

    EQUALITY_FIELDS = {
        "provinceId": "province_id",
        "districtId": "district_id",
        "municipalityId": "municipality_id",
        "category": "category",
        "tenderType": "tender_type",
        "organisation": "organisation",
        "status": "status",
    }

    def __init__(self, db: Session):
        self.db = db

    def for_tender(self, tender: Tender):
        query = (
            select(SavedSearch)
            .outerjoin(
                NotificationPreference,
                NotificationPreference.user_id == SavedSearch.user_id,
            )
            .where(
                SavedSearch.alerts_enabled.is_(True),
                or_(
                    NotificationPreference.id.is_(None),
                    NotificationPreference.new_tender_matches_enabled.is_(True),
                ),
            )
        )
        for filter_name, tender_attribute in self.EQUALITY_FIELDS.items():
            value = getattr(tender, tender_attribute)
            json_value = SavedSearch.filters[filter_name].as_string()
            query = query.where(
                or_(
                    json_value.is_(None),
                    json_value == "",
                    func.lower(json_value) == str(value or "").lower(),
                )
            )
        return self.db.scalars(query.execution_options(yield_per=250))
