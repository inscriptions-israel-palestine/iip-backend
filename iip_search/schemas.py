from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict

from .models import DisplayStatus
from .models import EditionType


class IIPBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Edition(IIPBase):
    id: int
    edition_type: EditionType
    raw_xml: str
    text: str


class Image(IIPBase):
    id: int
    description: Optional[str]
    graphic_url: str


class City(IIPBase):
    id: int
    placename: str
    pleiades_ref: Optional[str]


class IIPPreservation(IIPBase):
    id: int
    description: Optional[str]
    xml_id: str


class Provenance(IIPBase):
    id: int
    placename: str


class Region(IIPBase):
    id: int
    label: str
    description: str


class BibliographicEntry(IIPBase):
    id: int
    bibl_scope: Optional[str]
    bibl_scope_unit: Optional[str]
    ptr_target: Optional[str]
    ptr_type: Optional[str]
    raw_xml: str
    xml_id: str


class Figure(IIPBase):
    id: int
    name: str
    locus: str


class IIPForm(IIPBase):
    id: int
    ana: Optional[str]
    description: Optional[str]
    xml_id: str


class IIPGenre(IIPBase):
    id: int
    description: Optional[str]
    xml_id: str


class IIPMaterial(IIPBase):
    id: int
    description: Optional[str]
    xml_id: str


class IIPReligion(IIPBase):
    id: int
    description: Optional[str]
    xml_id: str


class IIPWriting(IIPBase):
    id: int
    description: Optional[str]
    note: Optional[str]
    xml_id: str


class Language(IIPBase):
    id: int
    label: str
    short_form: str


class Location(IIPBase):
    id: int
    description: Optional[str]
    label: Optional[str]
    placename: str
    pleiades_ref: Optional[str]


class FacetsResponse(IIPBase):
    cities: list[City]
    genres: list[IIPGenre]
    languages: list[Language]
    materials: list[IIPMaterial]
    physical_types: list[IIPForm]
    provenances: list[Provenance]
    regions: list[Region]
    religions: list[IIPReligion]


# InscriptionMapResponse performs minimal joins
# for displaying all inscriptions on the map
class InscriptionMapResponse(IIPBase):
    id: int
    city: Optional[City]
    description: Optional[str]
    dimensions: Optional[dict]
    display_status: DisplayStatus
    filename: str
    location_coordinates: Optional[List[float]]
    location_metadata: Optional[dict]
    not_after: Optional[int]
    not_before: Optional[int]
    short_description: Optional[str]
    title: Optional[str]


# InscriptionListResponse adds a few additional join
# queries because we're paginating these results
class InscriptionListResponse(InscriptionMapResponse):
    editions: List[Edition]
    images: Optional[List[Image]]
    languages: List[Language]


# Inscription performs all of the joins on the Inscription model.
# This schema should only be used for displaying an individual inscription.
class Inscription(InscriptionListResponse):
    bibliographic_entries: List[BibliographicEntry]
    figures: List[Figure]
    iip_forms: List[IIPForm]
    iip_genres: List[IIPGenre]
    iip_materials: List[IIPMaterial]
    iip_preservation: Optional[IIPPreservation]
    iip_religions: List[IIPReligion]
    iip_writings: List[IIPWriting]
    provenance: Optional[Provenance]
    region: Optional[Region]

# InscriptionPatch is used for updating inscriptions via
# the REST API. Right now, it only supports the `display_status`
# parameter.
class InscriptionPatch(IIPBase):
    display_status: DisplayStatus
