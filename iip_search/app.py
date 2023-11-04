# -*- coding: utf-8 -*-
import logging


# I imagine this style of imports looks strange at first,
# but it makes it much easier to keep things
# organized than using comma-separated lists
from typing import Annotated

from fastapi import Body
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi import Query
from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer

from fastapi_pagination import Page
from fastapi_pagination import add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

from sqlalchemy.orm import Session

from iip_search import admin_crud
from iip_search import crud
from iip_search import schemas

from iip_search.auth_utils import VerifyToken
from iip_search.db import SessionLocal

app = FastAPI()
token_auth_scheme = HTTPBearer()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
    logging.error(request, exc_str)
    content = {"status_code": 10422, "message": exc_str, "data": None}
    return JSONResponse(
        content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(
    request: Request, exc: ResponseValidationError
):
    return JSONResponse(
        status_code=500,
        content=jsonable_encoder({"detail": exc.errors(), "body": exc.body}),
    )


@app.route("/heartbeat")
def heartbeat():
    return "OK"


@app.get(
    "/admin/display_status/{display_status}/inscriptions",
    response_model=Page[schemas.InscriptionListResponse],
)
def inscriptions_by_display_status(
    response: Response,
    display_status: schemas.DisplayStatus,
    token: str = Depends(token_auth_scheme),
    db: Session = Depends(get_db),
):
    result = VerifyToken(token.credentials).verify()  # type: ignore

    if result.get("status"):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return result

    return admin_crud.list_inscriptions_by_display_status(db, display_status)


@app.get("/facets", response_model=schemas.FacetsResponse)
def facets(
    text_search: str | None = None,
    description_place_id: str | None = None,
    figures: str | None = None,
    not_before: int | str | None = None,
    not_before_era: str | None = None,
    not_after: int | str | None = None,
    not_after_era: str | None = None,
    cities: Annotated[list[int] | None, Query()] = None,
    provenances: Annotated[list[int] | None, Query()] = None,
    genres: Annotated[list[int] | None, Query()] = None,
    physical_types: Annotated[list[int] | None, Query()] = None,
    languages: Annotated[list[int] | None, Query()] = None,
    religions: Annotated[list[int] | None, Query()] = None,
    materials: Annotated[list[int] | None, Query()] = None,
    db: Session = Depends(get_db),
):
    inscription_ids = []
    # crud.list_inscription_ids is kind of an expensive query,
    # so we only want to do it if we have query params
    if any(
        [
            text_search,
            description_place_id,
            figures,
            not_before,
            not_after,
            cities,
            provenances,
            genres,
            physical_types,
            languages,
            religions,
            materials,
        ]
    ):
        inscription_ids = crud.list_inscription_ids(
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

    return crud.list_facets_with_inscriptions(db, inscription_ids)


@app.get("/inscriptions", response_model=Page[schemas.InscriptionListResponse])
def list_inscriptions(
    text_search: str | None = None,
    description_place_id: str | None = None,
    figures: str | None = None,
    not_before: int | str | None = None,
    not_before_era: str | None = None,
    not_after: int | str | None = None,
    not_after_era: str | None = None,
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
        crud.list_inscriptions_query(
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


@app.get("/inscriptions/map", response_model=list[schemas.InscriptionMapResponse])
def list_map_inscriptions(
    text_search: str | None = None,
    description_place_id: str | None = None,
    figures: str | None = None,
    not_before: int | str | None = None,
    not_before_era: str | None = None,
    not_after: int | str | None = None,
    not_after_era: str | None = None,
    cities: Annotated[list[int] | None, Query()] = None,
    provenances: Annotated[list[int] | None, Query()] = None,
    genres: Annotated[list[int] | None, Query()] = None,
    physical_types: Annotated[list[int] | None, Query()] = None,
    languages: Annotated[list[int] | None, Query()] = None,
    religions: Annotated[list[int] | None, Query()] = None,
    materials: Annotated[list[int] | None, Query()] = None,
    db: Session = Depends(get_db),
):
    query = crud.list_inscriptions_query(
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
def get_inscription(
    slug: str,
    db: Session = Depends(get_db),
):
    inscription = crud.get_inscription(db, slug)

    # TODO: restricting individual views requires a more complex
    # frontend authentication flow. For now, because an un-authed user
    # won't be able to do anything besides view the unapproved inscription,
    # let's just let them view it if they have the URL?

    # if inscription.display_status != schemas.DisplayStatus.APPROVED:
    #     verification = VerifyToken(token.credentials).verify()

    #     if verification.get("status"):
    #         response.status_code = status.HTTP_404_NOT_FOUND
    #         return verification

    return inscription


@app.patch("/inscriptions/{slug}", response_model=schemas.Inscription)
def update_inscription(
    response: Response,
    slug: str,
    inscription: Annotated[schemas.InscriptionPatch, Body()],
    token: str = Depends(token_auth_scheme),
    db: Session = Depends(get_db),
):
    result = VerifyToken(token.credentials).verify()  # type: ignore

    if result.get("status"):
        response.status_code = status.HTTP_400_BAD_REQUEST
        return result

    return admin_crud.update_inscription(db, slug, inscription)


add_pagination(app)
