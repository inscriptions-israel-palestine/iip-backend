import os
import pytest

from sqlalchemy import create_engine

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from iip_search import crud
from iip_search import models

from iip_search.db import Base

DB_URL = os.getenv(
    "TEST_DB_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/iip_search_test",
)
engine = create_engine(DB_URL)
Session = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def cities():
    return [
        models.City(placename="City 1"),
        models.City(placename="Another City 2"),
    ]


@pytest.fixture
def provenances():
    return [
        models.Provenance(placename="Provenance 1"),
        models.Provenance(placename="Another Provenance 2"),
    ]


@pytest.fixture
def locations(cities, provenances):
    return cities + provenances


class TestCrud:
    def test_list_locations(self, db_session, locations):
        for location in locations:
            db_session.add(location)

        locs = crud.list_locations(db_session)

        assert len(locs) == 4
