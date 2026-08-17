import json,time
from sqlalchemy import inspect,text
from app.core.database import SessionLocal
REQUIRED_TABLES={"connector_runs","connector_states","raw_ingestions","tenders","tender_source_versions","tender_duplicate_candidates","geography_datasets"}
if __name__=="__main__":
 with SessionLocal() as db:
  if db.bind.dialect.name!="postgresql":raise SystemExit("BLOCKED: verification requires PostgreSQL")
  version=db.scalar(text("SHOW server_version"));tables=set(inspect(db.bind).get_table_names());missing=sorted(REQUIRED_TABLES-tables)
  columns={r[0]:r[1] for r in db.execute(text("SELECT column_name,data_type FROM information_schema.columns WHERE table_name='tenders'"))};indexes={r[0]:r[1] for r in db.execute(text("SELECT indexname,indexdef FROM pg_indexes WHERE tablename='tenders'"))}
  source=db.execute(text("SELECT name,api_url,active FROM sources WHERE connector_type='ETENDERS_OCDS'")).mappings().first();geography=db.execute(text("SELECT (SELECT count(*) FROM provinces) provinces,(SELECT count(*) FROM districts) districts,(SELECT count(*) FROM municipalities) municipalities")).mappings().one()
  started=time.perf_counter();plan=[r[0] for r in db.execute(text("EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) SELECT id FROM tenders WHERE search_vector @@ websearch_to_tsquery('english','construction') ORDER BY ts_rank_cd(search_vector,websearch_to_tsquery('english','construction')) DESC LIMIT 20"))];elapsed=round((time.perf_counter()-started)*1000,2)
  result={"postgresql_version":version,"missing_tables":missing,"search_vector_type":columns.get("search_vector"),"gin_index":indexes.get("ix_tenders_search_vector"),"source":dict(source) if source else None,"geography":dict(geography),"search_elapsed_ms":elapsed,"explain":plan};print(json.dumps(result,indent=2,default=str))
  if missing or columns.get("search_vector")!="tsvector" or "using gin" not in indexes.get("ix_tenders_search_vector","").lower() or not source:raise SystemExit(1)
