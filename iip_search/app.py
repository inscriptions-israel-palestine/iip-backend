# -*- coding: utf-8 -*-
import logging
import os
import unicodedata

from typing import Annotated
from typing import Literal

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi import Query
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse

from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy import select
from sqlalchemy.orm import Session

from iip_search import crud
from iip_search import schemas

from iip_search.db import SessionLocal
from iip_search.db import engine

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(request, exc_str)
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@app.exception_handler(ResponseValidationError)
async def validation_exception_handler(request: Request, exc: ResponseValidationError):
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.route("/heartbeat")
def heartbeat():
    return "OK"


# Search fields from https://github.com/Brown-University-Library/iip-production/blob/main/iip_smr_web_app/common.py#L146C74-L146C136
# `(
#   'text',
#   'metadata',
#   'figure',
#   'region',
#   'city',
#   'place',
#   'type',
#   'physical_type',
#   'language',
#   'religion',
#   'material',
#   'notBefore',
#   'notAfter',
#   'display_status'
# )`


@app.get("/facets", response_model=schemas.FacetsResponse)
def facets(db: Session = Depends(get_db)):
    return crud.list_facets(db)


@app.get("/inscriptions", response_model=Page[schemas.InscriptionListResponse])
def list_inscriptions(
    text_search: str | None = None,
    description_place_id: str | None = None,
    figures: str | None = None,
    not_before: int | str | None = None,
    not_before_era: Literal["bce"] | Literal["ce"] | None = None,
    not_after: int | str | None = None,
    not_after_era: Literal["bce"] | Literal["ce"] | None = None,
    cities: Annotated[list[int] | None, Query()] = None,
    provenances: Annotated[list[int] | None, Query()] = None,
    genres: Annotated[list[int] | None, Query()] = None,
    physical_types: Annotated[list[int] | None, Query()] = None,
    languages: Annotated[list[int] | None, Query()] = None,
    religions: Annotated[list[int] | None, Query()] = None,
    materials: Annotated[list[int] | None, Query()] = None,
    db: Session = Depends(get_db),
):
    return paginate(
        db,
        crud.list_inscriptions(
            db,
            text_search,
            description_place_id,
            figures,
            not_before,
            not_before_era,
            not_after,
            not_after_era,
            cities,
            provenances,
            genres,
            physical_types,
            languages,
            religions,
            materials,
        ),
    )


@app.get("/map/inscriptions", response_model=list[schemas.InscriptionMapResponse])
def list_inscriptions(
    text_search: str | None = None,
    description_place_id: str | None = None,
    figures: str | None = None,
    not_before: int | str | None = None,
    not_before_era: Literal["bce"] | Literal["ce"] | None = None,
    not_after: int | str | None = None,
    not_after_era: Literal["bce"] | Literal["ce"] | None = None,
    cities: Annotated[list[int] | None, Query()] = None,
    provenances: Annotated[list[int] | None, Query()] = None,
    genres: Annotated[list[int] | None, Query()] = None,
    physical_types: Annotated[list[int] | None, Query()] = None,
    languages: Annotated[list[int] | None, Query()] = None,
    religions: Annotated[list[int] | None, Query()] = None,
    materials: Annotated[list[int] | None, Query()] = None,
    db: Session = Depends(get_db),
):
    query = crud.list_inscriptions(
        db,
        text_search,
        description_place_id,
        figures,
        not_before,
        not_before_era,
        not_after,
        not_after_era,
        cities,
        provenances,
        genres,
        physical_types,
        languages,
        religions,
        materials,
    )
    return query.all()


@app.get("/inscriptions/{slug}", response_model=schemas.Inscription)
def get_inscription(slug: str, db: Session = Depends(get_db)):
    return crud.get_inscription(db, slug)


@app.get("/languages", response_model=list[schemas.Language])
def list_languages(db: Session = Depends(get_db)):
    return crud.list_languages(db)


@app.get("/locations", response_model=list[schemas.Location])
def list_locations(db: Session = Depends(get_db)):
    return crud.list_locations(db)


add_pagination(app)
