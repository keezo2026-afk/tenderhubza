from datetime import date

from app.core.security import hash_password
from app.models import SavedSearch, Source, Tender, User
from app.notifications.candidates import SavedSearchCandidateRepository
from app.notifications.matching import matches


def test_database_candidate_query_narrows_without_changing_matching_semantics(db):
    user = User(
        email="candidates@example.co.za",
        password_hash=hash_password("StrongPass123!"),
        first_name="Candidate",
        last_name="Owner",
    )
    source = Source(
        name="Candidate source",
        source_type="OTHER",
        organisation="Test",
        website_url="https://example.org",
        connector_type="CANDIDATE_TEST",
        polling_frequency="manual",
    )
    db.add_all([user, source])
    db.flush()
    tender = Tender(
        source_id=source.id,
        source_reference="candidate-tender",
        title="Construction of municipal offices",
        organisation="Public Works",
        category="Construction",
        status="OPEN",
        source_url="https://example.org/tender",
        issue_date=date(2026, 8, 17),
    )
    matching = SavedSearch(
        user_id=user.id,
        name="Matching",
        query="construction",
        filters={"category": "construction", "status": "open"},
        sort="relevance",
        alerts_enabled=True,
    )
    wrong_category = SavedSearch(
        user_id=user.id,
        name="Wrong category",
        query="construction",
        filters={"category": "ICT"},
        sort="relevance",
        alerts_enabled=True,
    )
    broad_nonmatch = SavedSearch(
        user_id=user.id,
        name="Python rejects keyword",
        query="security",
        filters={},
        sort="relevance",
        alerts_enabled=True,
    )
    irrelevant = [
        SavedSearch(
            user_id=user.id,
            name=f"Irrelevant {index}",
            query="construction",
            filters={"category": "ICT"},
            sort="relevance",
            alerts_enabled=True,
        )
        for index in range(100)
    ]
    db.add_all([tender, matching, wrong_category, broad_nonmatch, *irrelevant])
    db.commit()
    candidates = list(SavedSearchCandidateRepository(db).for_tender(tender))
    assert len(candidates) == 2
    assert matching in candidates
    assert wrong_category not in candidates
    assert broad_nonmatch in candidates
    assert [candidate.name for candidate in candidates if matches(tender, candidate)] == [
        "Matching"
    ]
