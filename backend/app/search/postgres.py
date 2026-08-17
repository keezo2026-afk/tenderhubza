from sqlalchemy import func, literal_column
from sqlalchemy.sql import Select

from app.models import Tender


class TenderSearch:
    def apply(
        self, query: Select, q: str | None, dialect_name: str
    ) -> tuple[Select, object | None]:
        if not q:
            return query, None
        if dialect_name == "postgresql":
            tsquery = func.websearch_to_tsquery("english", q)
            vector = literal_column("search_vector")
            return query.where(vector.op("@@")(tsquery)), func.ts_rank_cd(vector, tsquery)
        # deterministic non-production fallback used only by SQLite unit tests
        corpus = func.lower(
            func.coalesce(Tender.title, "")
            + " "
            + func.coalesce(Tender.description, "")
            + " "
            + func.coalesce(Tender.reference_number, "")
            + " "
            + func.coalesce(Tender.organisation, "")
            + " "
            + func.coalesce(Tender.municipality, "")
            + " "
            + func.coalesce(Tender.category, "")
        )
        return query.where(func.instr(corpus, q.lower()) > 0), None
