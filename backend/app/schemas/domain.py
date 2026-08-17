from datetime import date, datetime, time
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, HttpUrl, Field
class UserOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; email:str; first_name:str; last_name:str; phone:str|None; role:str; status:str; created_at:datetime
class TenderCreate(BaseModel):
    source_id:str; source_reference:str=Field(min_length=1,max_length=255); reference_number:str|None=None; title:str=Field(min_length=1,max_length=500); description:str|None=None; organisation:str=Field(min_length=1,max_length=255); province:str|None=None; municipality:str|None=None; district:str|None=None; category:str|None=None; subcategory:str|None=None; tender_type:str|None=None; issue_date:date|None=None; closing_date:date|None=None; closing_time:time|None=None; estimated_value:Decimal|None=None; currency:str="ZAR"; source_url:str; status:str="OPEN"; contact_name:str|None=None; contact_email:str|None=None; contact_phone:str|None=None
class TenderOut(TenderCreate):
    model_config=ConfigDict(from_attributes=True)
    id:str; created_at:datetime; updated_at:datetime
class SourceCreate(BaseModel):
    name:str=Field(min_length=1,max_length=200); source_type:str; organisation:str; website_url:str; api_url:str|None=None; province:str|None=None; municipality:str|None=None; active:bool=True; connector_type:str; polling_frequency:str="daily"
class SourceOut(SourceCreate):
    model_config=ConfigDict(from_attributes=True)
    id:str; last_successful_run:datetime|None; last_failed_run:datetime|None; last_error:str|None; created_at:datetime; updated_at:datetime
class ProvinceOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; code:str; name:str
class MunicipalityOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:str; province_id:str; district_id:str|None; code:str|None; name:str; municipality_type:str|None; active:bool
