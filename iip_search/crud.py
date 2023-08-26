import unicodedata

from typing import Literal
from urllib import parse

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from iip_search import models
from iip_search import schemas


def get_city(db: Session, city_id: int):
    return db.query(models.City).filter(models.City.id == city_id).one()


def get_inscription(db: Session, slug: str):
    return (
        db.query(models.Inscription)
        .filter(models.Inscription.filename == f"{slug}.xml")
        .one()
    )


def update_inscription(db: Session, slug: str, inscription: schemas.InscriptionPatch):
    to_update = db.query(models.Inscription).filter_by(filename=f"{slug}.xml").one()
    to_update.display_status = inscription.display_status

    db.commit()
    
    return get_inscription(db, slug)

def get_provenance(db: Session, provenance_id: id):
    return (
        db.query(models.Provenance).filter(models.Provenance.id == provenance_id).one()
    )


def get_region(db: Session, region_id: int):
    return db.query(models.Region).filter(models.Region.id == region_id).one()


def list_cities(db: Session):
    return db.query(models.City).all()


# possibly maps to "physical type" in the interface?
def list_forms(db: Session):
    return db.query(models.IIPForm).all()


def list_genres(db: Session):
    return db.query(models.IIPGenre).all()


def list_languages(db: Session):
    return db.query(models.Language).all()


def list_locations(db: Session):
    cities = list_cities(db)
    provenances = list_provenances(db)
    regions = list_regions(db)

    return cities + provenances + regions


def list_materials(db: Session):
    return db.query(models.IIPMaterial).all()


def list_provenances(db: Session):
    return db.query(models.Provenance).all()


def list_regions(db: Session):
    return db.query(models.Region).all()


def list_religions(db: Session):
    return db.query(models.IIPReligion).all()


def list_facets(db: Session):
    cities = list_cities(db)
    genres = list_genres(db)
    languages = list_languages(db)
    materials = list_materials(db)
    physical_types = list_forms(db)
    provenances = list_provenances(db)
    regions = list_regions(db)
    religions = list_religions(db)

    return dict(
        cities=cities,
        genres=genres,
        languages=languages,
        materials=materials,
        physical_types=physical_types,
        provenances=provenances,
        regions=regions,
        religions=religions,
    )


def search_inscriptions(db: Session, input_str: str):
    normalized_string = remove_accents(search)
    stmt = (
        select(models.Inscription)
        .filter(models.Inscription.display_status == models.DisplayStatus.APPROVED)
        .distinct(models.Inscription.id)
        .join(
            models.Inscription.editions.and_(
                models.Edition.searchable_text.match(normalized_string)
            ),
        )
    )

    return db.execute(stmt).scalars()


def list_inscriptions(
    db: Session,
    text_search: str | None = None,
    description_place_id: str | None = None,
    figures: str | None = None,
    not_before: int | None = None,
    not_before_era: Literal["bce"] | Literal["ce"] | None = None,
    not_after: int | None = None,
    not_after_era: Literal["bce"] | Literal["ce"] | None = None,
    cities: list[int] | None = [],
    provenances: list[int] | None = [],
    genres: list[int] | None = [],
    physical_types: list[int] | None = [],
    languages: list[int] | None = [],
    religions: list[int] | None = [],
    materials: list[int] | None = [],
):
    query = (
        db.query(models.Inscription)
        .filter(models.Inscription.display_status == models.DisplayStatus.APPROVED)
        .distinct(models.Inscription.id)
    )

    ands = []
    ors = []

    if text_search is not None:
        cleaned_text_search = remove_accents(parse.unquote(text_search))
        ors.append(
            models.Inscription.editions.any(
                models.Edition.searchable_text.match(cleaned_text_search)
            )
        )

    if description_place_id is not None:
        ors.append(models.Inscription.searchable_text.match(description_place_id))

    if figures is not None:
        ors.append(
            models.Inscription.figures.any(
                models.Figure.searchable_text.match(text_search)
            )
        )

    if not_before is not None and not_before != "":
        if not_before_era == "bce":
            not_before = -int(not_before)
        ands.append(models.Inscription.not_before >= not_before)

    if not_after is not None and not_after != "":
        if not_after_era == "bce":
            not_after = -int(not_after)
        ands.append(models.Inscription.not_after <= not_after)

    if cities is not None and len(cities) > 0:
        ors.append(models.Inscription.city_id.in_(cities))

    if provenances is not None and len(provenances) > 0:
        ors.append(models.Inscription.provenance_id.in_(provenances))

    if genres is not None and len(genres) > 0:
        ors.append(models.Inscription.iip_genres.any(models.IIPGenre.id.in_(genres)))

    if physical_types is not None and len(physical_types) > 0:
        ors.append(
            models.Inscripton.iip_forms.any(models.IIPForm.id.in_(physical_types))
        )

    if languages is not None and len(languages) > 0:
        ors.append(models.Inscription.languages.any(models.Language.id.in_(languages)))

    if religions is not None and len(religions) > 0:
        ors.append(
            models.Inscription.iip_religions.any(models.IIPReligion.id.in_(religions))
        )

    if materials is not None and len(materials) > 0:
        ors.append(
            models.Inscription.iip_materials.any(models.IIPMaterial.id.in_(materials))
        )

    return query.filter(or_(*ors)).filter(and_(*ands))


def remove_accents(input_str):
    nfkd_form = unicodedata.normalize("NFKD", input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
