import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.database import get_session, seed_users
from app.main import app


@pytest.fixture
def engine():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_users(session)
    yield engine
    engine.dispose()


@pytest.fixture
def make_client(engine):
    def override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override

    def _make(username=None, password="123456"):
        client = TestClient(app)
        if username:
            r = client.post("/api/login", json={"username": username, "password": password})
            assert r.status_code == 200
        return client

    yield _make
    app.dependency_overrides.clear()


@pytest.fixture
def author(make_client):
    return make_client("author1")


@pytest.fixture
def editor(make_client):
    return make_client("editor1")
