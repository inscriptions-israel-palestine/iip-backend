# This file's name has a special meaning for pytest:
# https://docs.pytest.org/en/latest/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
# DON'T CHANGE THE FILENAME

import datetime
import os
import pytest

from sqlalchemy import create_engine
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


@pytest.fixture
def db_session():
    Base.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def bibliographic_entries():
    return [
        models.BibliographicEntry(raw_xml="<div>raw1</div>", xml_id="zotero1"),
        models.BibliographicEntry(raw_xml="<div>raw2</div>", xml_id="zotero2"),
    ]


@pytest.fixture
def cities():
    return [
        models.City(placename="City 1"),
        models.City(placename="Another City 2"),
    ]


@pytest.fixture
def figures():
    return [
        models.Figure(name="Figure 1"),
        models.Figure(name="Figure 2"),
    ]


@pytest.fixture
def iip_forms():
    return [
        models.IIPForm(ana="ana1", description="description 1", xml_id="xml_id_1"),
        models.IIPForm(ana="ana2", description="description 2", xml_id="xml_id_2"),
    ]


@pytest.fixture
def iip_genres():
    return [
        models.IIPGenre(description="description 1", xml_id="xml_id_1"),
        models.IIPGenre(description="description 2", xml_id="xml_id_2"),
    ]


@pytest.fixture
def iip_materials():
    return [
        models.IIPMaterial(description="description 1", xml_id="xml_id_1"),
        models.IIPMaterial(description="description 2", xml_id="xml_id_2"),
    ]


@pytest.fixture
def iip_preservations():
    return [
        models.IIPPreservation(xml_id="xml_id_1", description="description 1"),
        models.IIPPreservation(xml_id="xml_id_2", description="description 2"),
    ]


@pytest.fixture
def iip_religions():
    return [
        models.IIPReligion(description="description 1", xml_id="xml_id_1"),
        models.IIPReligion(description="description 2", xml_id="xml_id_2"),
    ]


@pytest.fixture
def iip_writings():
    return [
        models.IIPWriting(description="description 1", xml_id="xml_id_1"),
        models.IIPWriting(description="description 2", xml_id="xml_id_2"),
    ]


@pytest.fixture
def languages():
    return [
        models.Language(label="label 1", short_form="grc"),
        models.Language(label="label 2", short_form="heb"),
    ]


@pytest.fixture
def provenances():
    return [
        models.Provenance(placename="Provenance 1"),
        models.Provenance(placename="Another Provenance 2"),
    ]


@pytest.fixture
def regions():
    return [
        models.Region(label="Region 1", description="description 1"),
        models.Region(label="Another Region 2", description="description 2"),
    ]


@pytest.fixture
def inscriptions(
    bibliographic_entries,
    cities,
    figures,
    iip_forms,
    iip_genres,
    iip_materials,
    iip_preservations,
    iip_religions,
    iip_writings,
    languages,
    provenances,
    regions,
):
    return [
        models.Inscription(
            bibliographic_entries=bibliographic_entries,
            city=cities[0],
            description="Description 1",
            figures=figures,
            filename="filename1.xml",
            iip_forms=iip_forms,
            iip_genres=iip_genres,
            iip_materials=iip_materials,
            iip_preservation=iip_preservations[0],
            iip_religions=iip_religions,
            iip_writings=iip_writings,
            languages=languages,
            location_coordinates=[50.1, 50.1],
            not_after=600,
            not_before=-600,
            parsed_at=datetime.datetime.now(),
            provenance=provenances[0],
            region=regions[0],
            title="Title 1",
        ),
        models.Inscription(
            bibliographic_entries=[bibliographic_entries[1]],
            city=cities[1],
            description="Description 2",
            figures=[figures[1]],
            filename="filename2.xml",
            iip_forms=[iip_forms[1]],
            iip_genres=[iip_genres[1]],
            iip_materials=[iip_materials[1]],
            iip_preservation=iip_preservations[1],
            iip_religions=[iip_religions[1]],
            iip_writings=[iip_writings[1]],
            languages=[languages[1]],
            location_coordinates=[50.1, 50.1],
            not_after=400,
            not_before=-400,
            parsed_at=datetime.datetime.now(),
            provenance=provenances[1],
            region=regions[1],
            title="Title 2",
        ),
    ]


@pytest.fixture
def locations(cities, provenances):
    return cities + provenances
