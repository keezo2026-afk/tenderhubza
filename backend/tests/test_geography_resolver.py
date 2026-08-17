from app.models import District, Municipality, Province
from app.services.geography_resolver import GeographyMatchMethod, GeographyResolver


def geography(db):
    kzn = Province(code="KZN", name="KwaZulu-Natal")
    gauteng = Province(code="GP", name="Gauteng")
    db.add_all([kzn, gauteng])
    db.flush()
    umgungundlovu = District(province_id=kzn.id, code="DC22", name="uMgungundlovu")
    sedibeng = District(province_id=gauteng.id, code="DC42", name="Sedibeng")
    db.add_all([umgungundlovu, sedibeng])
    db.flush()
    msunduzi = Municipality(
        province_id=kzn.id,
        district_id=umgungundlovu.id,
        code="KZN225",
        name="Msunduzi",
    )
    ethekwini = Municipality(
        province_id=kzn.id,
        district_id=None,
        code="ETH",
        name="eThekwini",
        municipality_type="METROPOLITAN",
    )
    db.add_all([msunduzi, ethekwini])
    db.commit()
    return kzn, gauteng, umgungundlovu, sedibeng, msunduzi, ethekwini


def test_exact_and_code_resolution(db):
    kzn, _, district, _, municipality, _ = geography(db)
    result = GeographyResolver(db).resolve(
        province="KwaZulu-Natal",
        district_code="DC22",
        municipality="Msunduzi",
    )
    assert result.province.id == kzn.id
    assert result.province.match_method == GeographyMatchMethod.EXACT_NAME
    assert result.district.id == district.id
    assert result.district.match_method == GeographyMatchMethod.CODE
    assert result.municipality.id == municipality.id
    assert result.resolved


def test_case_whitespace_punctuation_and_aliases(db):
    kzn, _, _, _, _, ethekwini = geography(db)
    resolver = GeographyResolver(db)
    normalized = resolver.resolve(province="  kwazulu natal  ")
    formatted = resolver.resolve(municipality="eThekwini Metropolitan Municipality")
    alias = resolver.resolve(province="KZN", municipality="City of eThekwini")
    assert normalized.province.id == kzn.id
    assert normalized.province.match_method in {
        GeographyMatchMethod.NORMALIZED_NAME,
        GeographyMatchMethod.ALIAS,
    }
    assert formatted.municipality.id == ethekwini.id
    assert formatted.municipality.match_method == GeographyMatchMethod.NORMALIZED_NAME
    assert alias.municipality.id == ethekwini.id
    assert alias.municipality.match_method == GeographyMatchMethod.ALIAS
    assert alias.municipality.confidence == 0.9


def test_invalid_and_unresolved_geography_is_not_guessed(db):
    geography(db)
    result = GeographyResolver(db).resolve(
        province="KwaZulu-Natal",
        district="Not a district",
        municipality="Not a municipality",
    )
    assert result.district.id is None
    assert result.municipality.id is None
    assert "DISTRICT_UNRESOLVED" in result.issues
    assert "MUNICIPALITY_UNRESOLVED" in result.issues


def test_municipality_province_mismatch_is_rejected(db):
    _, gauteng, _, _, msunduzi, _ = geography(db)
    result = GeographyResolver(db).resolve(
        province=gauteng.name,
        municipality=msunduzi.name,
    )
    assert result.municipality.id is None
    assert "MUNICIPALITY_PROVINCE_MISMATCH" in result.issues


def test_municipality_district_mismatch_is_rejected(db):
    kzn, _, _, _, msunduzi, _ = geography(db)
    other = District(province_id=kzn.id, code="DC29", name="iLembe")
    db.add(other)
    db.commit()
    result = GeographyResolver(db).resolve(
        province=kzn.name,
        district=other.name,
        municipality=msunduzi.name,
    )
    assert result.district.id == other.id
    assert result.municipality.id is None
    assert "MUNICIPALITY_DISTRICT_MISMATCH" in result.issues
