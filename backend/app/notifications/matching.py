from datetime import date
from decimal import Decimal,InvalidOperation
from app.models import SavedSearch,Tender
def _date(value):
 try:return date.fromisoformat(value) if value else None
 except ValueError:return None
def matches(t:Tender,s:SavedSearch)->bool:
 f=s.filters or {};corpus=" ".join(filter(None,[t.title,t.description,t.reference_number,t.organisation,t.municipality,t.category])).lower()
 if s.query and not all(word in corpus for word in s.query.lower().split()):return False
 for key,actual in [("provinceId",t.province_id),("districtId",t.district_id),("municipalityId",t.municipality_id),("category",t.category),("tenderType",t.tender_type),("organisation",t.organisation),("status",t.status)]:
  expected=f.get(key)
  if expected and str(actual or "").lower()!=str(expected).lower():return False
 for key,actual,minimum in [("issueFrom",t.issue_date,True),("issueTo",t.issue_date,False),("closingFrom",t.closing_date,True),("closingTo",t.closing_date,False)]:
  expected=_date(f.get(key))
  if expected and (actual is None or (actual<expected if minimum else actual>expected)):return False
 try:
  if f.get("minValue") and (t.estimated_value is None or t.estimated_value<Decimal(str(f["minValue"]))):return False
  if f.get("maxValue") and (t.estimated_value is None or t.estimated_value>Decimal(str(f["maxValue"]))):return False
 except InvalidOperation:return False
 return True
