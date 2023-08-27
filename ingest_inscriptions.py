#!/usr/bin/env python3

import json
import logging
import os
import requests
import time

from datetime import datetime
from pathlib import Path

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from iip_search import db
from iip_search import models
from iip_search.epidoc_parser import EpidocParser

logging.basicConfig(format="%(levelname)s: %(asctime)s %(message)s", level=logging.INFO)

EPIDOC_FILES_DIR = os.getenv("EPIDOC_FILES_DIR", "epidoc-files")
PLEIADES_CACHE_DIR = "./pleiades_cache"


def get_location_coordinates_from_pleiades(ref):
    # the ref_id should be the integer at the end
    # of the URL, e.g., for https://pleiades.stoa.org/places/687927
    # it is 687927. Unfortunately, encoders sometimes add
    # extra spaces (as happened in khja0001.xml), so we're
    # defensively calling strip() to eliminate them
    # before creating the filepath.
    ref = ref.strip()
    ref_id = ref.split("/")[-1]

    # allow for one trailing slash --- although this should
    # be considered a mistake
    if ref_id == "":
        ref_id = ref.split("/")[-2]

    filepath = f"{PLEIADES_CACHE_DIR}/{ref_id}.json"

    if os.path.isfile(filepath):
        with open(filepath) as f:
            data = json.loads(f.read())
    else:
        logging.info(f"No cached version of {ref} found.")
        r = requests.get(f"{ref}/json")
        data = r.json()

        f = open(filepath, "x")
        f.write(json.dumps(data, indent=2))
        f.close()
        # adding a sleep function here to be kind
        # to the Pleiades servers
        time.sleep(0.5)

    representative_location = data.get("reprPoint")

    if representative_location is None:
        logging.warning(f"No representative location found for {ref}.")

    return representative_location


def main(session):
    files = list_directory_xml(EPIDOC_FILES_DIR)

    for file in files:
        try:
            parser = EpidocParser(f"{EPIDOC_FILES_DIR}/{file}")
        except Exception as error:
            logging.error(error)
            continue

        bibliographic_entries_raw = parser.get_bibliography()
        city_raw = parser.get_city()
        description_raw = parser.get_description()
        dimensions_raw = parser.get_dimensions()
        figures_raw = parser.get_figures()
        iip_forms_raw = parser.get_iip_forms()
        iip_genres_raw = parser.get_iip_genres()
        iip_materials_raw = parser.get_iip_materials()
        iip_preservation_raw = parser.get_iip_preservation()
        iip_religions_raw = parser.get_iip_religions()
        iip_writings_raw = parser.get_iip_writings()
        images_raw = parser.get_images()
        languages_raw = parser.get_languages()
        location_coordinates = parser.get_location_coordinates()
        location_metadata = parser.get_location_metadata()
        not_after_raw = parser.get_not_after()
        not_before_raw = parser.get_not_before()
        provenance_raw = parser.get_provenance()
        region_raw = parser.get_region()
        short_description_raw = parser.get_short_description()
        title_raw = parser.get_title()

        city = None
        if city_raw is not None:
            city = get_or_create_city(
                session, city_raw["placename"], city_raw["pleiades_ref"]
            )

        iip_preservation = None
        if iip_preservation_raw is not None:
            iip_preservation = get_or_create(
                session, models.IIPPreservation, **iip_preservation_raw
            )
        else:
            logging.warning(f"No iip_preservation for {file}.")

        provenance = None
        if provenance_raw.get("placename") is not None:
            provenance = get_or_create(session, models.Provenance, **provenance_raw)
        else:
            logging.warning(f"No provenance for {file}.")

        region = None
        if region_raw is not None:
            region = get_or_create(session, models.Region, **region_raw)
        else:
            logging.warning(f"No region for {file}.")

        if (
            location_coordinates == None
            and city is not None
            and city.pleiades_ref is not None
        ):
            location_coordinates = get_location_coordinates_from_pleiades(
                city.pleiades_ref
            )

        inscription = upsert_inscription(
            session,
            **dict(
                city_id=city.id if city else None,
                description=description_raw,
                dimensions={"dimensions": dimensions_raw},
                filename=file,
                iip_preservation_id=iip_preservation.id if iip_preservation else None,
                location_coordinates=location_coordinates,
                location_metadata=location_metadata,
                not_after=not_after_raw,
                not_before=not_before_raw,
                parsed_at=datetime.now(),
                provenance_id=provenance.id if provenance else None,
                region_id=region.id if region else None,
                short_description=short_description_raw,
                title=title_raw,
            ),
        )

        bibliographic_entries = [
            get_or_create(session, models.BibliographicEntry, **raw)
            for raw in bibliographic_entries_raw
        ]

        for entry in bibliographic_entries:
            inscription.bibliographic_entries.add(entry)

        figures = []
        if figures_raw is not None:
            figures = [
                get_or_create(session, models.Figure, **raw) for raw in figures_raw
            ]

        for figure in figures:
            inscription.figures.add(figure)

        iip_forms = []
        if iip_forms_raw is not None:
            iip_forms = [
                get_or_create(session, models.IIPForm, **raw) for raw in iip_forms_raw
            ]

        for form in iip_forms:
            inscription.iip_forms.add(form)

        iip_genres = []
        if iip_genres_raw is not None:
            iip_genres = [
                get_or_create(session, models.IIPGenre, **raw) for raw in iip_genres_raw
            ]

        for genre in iip_genres:
            inscription.iip_genres.add(genre)

        iip_materials = [
            get_or_create(session, models.IIPMaterial, **raw)
            for raw in iip_materials_raw
        ]

        for material in iip_materials:
            inscription.iip_materials.add(material)

        iip_religions = []
        if iip_religions_raw is not None:
            iip_religions = [
                get_or_create(session, models.IIPReligion, **raw)
                for raw in iip_religions_raw
            ]

        for religion in iip_religions:
            inscription.iip_religions.add(religion)

        iip_writings = []
        if iip_writings_raw is not None:
            iip_writings = [
                get_or_create_iip_writing(session, **raw) for raw in iip_writings_raw
            ]

        for writing in iip_writings:
            inscription.iip_writings.add(writing)

        images = [
            get_or_create(session, models.Image, inscription_id=inscription.id, **raw)
            for raw in images_raw
            if len(raw["graphic_url"]) > 0
        ]

        for image in images:
            inscription.images.add(image)

        languages = [
            get_or_create(session, models.Language, **raw) for raw in languages_raw
        ]

        for language in languages:
            inscription.languages.add(language)

        (diplomatic_xml, s_diplomatic) = parser.get_diplomatic()
        (transcription_xml, s_transcription) = parser.get_transcription()
        (
            transcription_segmented_xml,
            s_transcription_segmented,
        ) = parser.get_transcription_segmented()
        (translation_xml, s_translation) = parser.get_translation()

        if diplomatic_xml is not None:
            upsert_edition(
                session,
                edition_type=models.EditionType.DIPLOMATIC,
                inscription_id=inscription.id,
                raw_xml=diplomatic_xml,
                text=s_diplomatic,
            )

        if transcription_xml is not None:
            upsert_edition(
                session,
                edition_type=models.EditionType.TRANSCRIPTION,
                inscription_id=inscription.id,
                raw_xml=transcription_xml,
                text=s_transcription,
            )

        if transcription_segmented_xml is not None:
            upsert_edition(
                session,
                edition_type=models.EditionType.TRANSCRIPTION_SEGMENTED,
                inscription_id=inscription.id,
                raw_xml=transcription_segmented_xml,
                text=s_transcription_segmented,
            )

        if translation_xml is not None:
            upsert_edition(
                session,
                edition_type=models.EditionType.TRANSLATION,
                inscription_id=inscription.id,
                raw_xml=translation_xml,
                text=s_translation,
            )

        session.add(inscription)
        session.commit()
        session.flush()


def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()

    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance


def get_or_create_city(session, placename, pleiades_ref):
    instance = session.query(models.City).filter_by(placename=placename).one_or_none()

    if instance:
        return instance
    else:
        instance = models.City(placename=placename, pleiades_ref=pleiades_ref)
        session.add(instance)
        session.commit()
        return instance


def upsert_edition(session, **kwargs):
    instance = (
        session.query(models.Edition)
        .filter_by(
            inscription_id=kwargs.get("inscription_id"),
            edition_type=kwargs.get("edition_type"),
        )
        .one_or_none()
    )

    if instance:
        instance.raw_xml = kwargs.get("raw_xml")
        instance.text = kwargs.get("text")
    else:
        instance = models.Edition(**kwargs)
        session.add(instance)

    session.commit()

    return instance


def get_or_create_iip_writing(session, **kwargs):
    stmt = (
        insert(models.IIPWriting)
        .values(kwargs)
        .on_conflict_do_update(
            index_elements=[models.IIPWriting.xml_id], set_=dict(kwargs)
        )
        .returning(models.IIPWriting.id)
    )

    result = session.execute(stmt)

    return session.get(models.IIPWriting, result.scalar_one())


def upsert_inscription(session, **kwargs):
    stmt = (
        insert(models.Inscription)
        .values(kwargs)
        .on_conflict_do_update(
            index_elements=[models.Inscription.filename], set_=dict(kwargs)
        )
        .returning(models.Inscription.id)
    )

    result = session.execute(stmt)

    return session.get(models.Inscription, result.scalar_one())


def list_directory_xml(directory):
    return [f for f in os.listdir(directory) if f[-4:] == ".xml"]


if __name__ == "__main__":
    with Session(db.engine) as session:
        main(session)

        session.commit()
