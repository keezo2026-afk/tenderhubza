from app.core.database import SessionLocal
from app.services.geography_import import import_census_geography

if __name__ == "__main__":
    with SessionLocal() as db:
        print(import_census_geography(db))
