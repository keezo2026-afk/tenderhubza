import csv
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import District,GeographyDataset,Municipality,Province
SOURCE="Statistics South Africa Census 2022 (independently extracted by afrith)"
SOURCE_URL="https://census.statssa.gov.za/assets/documents/2022/Provinces_at_a_Glance.pdf"
VERSION="Census 2022 municipal boundaries"
def import_census_geography(db:Session,data_dir:Path|None=None)->dict:
 data_dir=data_dir or Path(__file__).parents[2]/"data";existing=db.scalar(select(GeographyDataset).where(GeographyDataset.version==VERSION))
 if existing:return {"dataset_id":existing.id,"districts":0,"municipalities":0,"unchanged":True}
 dataset=GeographyDataset(name="South African administrative geography",source=SOURCE,source_url=SOURCE_URL,version=VERSION);db.add(dataset);db.flush();provinces={p.code:p for p in db.scalars(select(Province))};districts={}
 with open(data_dir/"za_districts_census2022.csv") as f:
  for row in csv.DictReader(f):
   province=provinces.get(row["prov_code"])
   if not province:continue
   district=District(dataset_id=dataset.id,province_id=province.id,code=row["dc_code"],name=row["name"]);db.add(district);db.flush();districts[row["dc_code"]]=district
 count=0
 with open(data_dir/"za_municipalities_census2022.csv") as f:
  for row in csv.DictReader(f):
   province=provinces.get(row["prov_code"])
   if not province:continue
   metro=row["miif_category"]=="METRO";db.add(Municipality(dataset_id=dataset.id,district_id=None if metro else districts.get(row["dc_code"]).id,province_id=province.id,code=row["muni_code"],name=row["name"],municipality_type="METROPOLITAN" if metro else "LOCAL",active=True));count+=1
 db.commit();return {"dataset_id":dataset.id,"districts":len(districts),"municipalities":count,"unchanged":False}
