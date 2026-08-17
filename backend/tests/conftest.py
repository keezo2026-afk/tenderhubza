import os
os.environ["DATABASE_URL"]="sqlite+pysqlite:///:memory:"
os.environ["SECRET_KEY"]="test-secret-at-least-thirty-two-characters"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.database import Base,get_db
from app.main import app
from app.models import *  # noqa
engine=create_engine("sqlite+pysqlite:///:memory:",connect_args={"check_same_thread":False},poolclass=StaticPool)
TestingSession=sessionmaker(bind=engine,expire_on_commit=False)
@pytest.fixture(autouse=True)
def database():
    from app.core.rate_limit import limiter
    if hasattr(limiter,"_events"): limiter._events.clear()
    Base.metadata.create_all(engine); yield; Base.metadata.drop_all(engine)
@pytest.fixture
def db():
    with TestingSession() as session: yield session
@pytest.fixture
def client():
    def override():
        with TestingSession() as session: yield session
    app.dependency_overrides[get_db]=override
    with TestClient(app,raise_server_exceptions=True) as c: yield c
    app.dependency_overrides.clear()
@pytest.fixture
def user_payload(): return {"email":"dev@example.co.za","password":"StrongPass123!","first_name":"Thandi","last_name":"Mokoena"}
@pytest.fixture
def auth_headers(client,user_payload):
    client.post("/api/v1/auth/register",json=user_payload)
    token=client.post("/api/v1/auth/login",json={"email":user_payload["email"],"password":user_payload["password"]}).json()["access_token"]
    return {"Authorization":f"Bearer {token}"}
