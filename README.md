IIP Search
------

This application parses the Epidoc XML files that store transcriptions for the [Inscriptions in Ancient Israel and Palestine](https://www.inscriptionsisraelpalestine.org/) project.

It consists of three main parts:

1. an Epidoc parser [↳](#epidoc-parser)
2. a database API [↳](#database-api)
3. a web server [↳](#web-server)

## Installation

1. Create a [virtual environment](https://docs.python.org/3/library/venv.html):

```sh
$ python -m venv my_venv
```

2. Install dependencies:

```sh
$ pip install -r requirements.txt
```

3. Run the ingestion script:

```sh
python ./ingest_inscriptions.py
```

The ingestion script uses upserts on data that can change, so you can rerun the script whenever you need.

## Epidoc Parser

Source: [epidoc_parser.py](epidoc_parser.py)

The Epidoc Parser, as its name suggests, handles the Epidoc inscription files. If it seems like some data isn't being pulled in, it's a good idea to start by looking here.

You'll see a function defined for each unit of data --- e.g., rather than trying to glom everything onto a large `inscription` object, we start by pulling out things like the `description`:

```python
def get_description(self):
    commentary = self.tree.xpath(
        "//tei:div[@type = 'commentary']/tei:p/text()", namespaces=NAMESPACES
    )

    if len(commentary) > 0:
        return whitespace_regex.sub(" ", commentary[0])

    return None
```

If you add a field, make sure to add it in [ingest_inscriptions.py](ingest_inscriptions.py) as well --- otherwise it won't be persisted to the database.

## Database API

Source: [db.py](iip_search/db.py)

Models: [models.py](iip_search/models.py)

Inscriptions are stored in a fairly compact relational database. The main `Inscription` model contains most of the action:

```python
@dataclass
class Inscription(Base):
    __tablename__ = "inscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    bibliographic_entries: Mapped[Set[BibliographicEntry]] = relationship(
        secondary=inscription_bibliographic_entry, back_populates="inscriptions"
    )
    city_id = mapped_column(ForeignKey("cities.id"), nullable=True)
    city: Mapped[Optional[City]] = relationship(back_populates="inscriptions")
    description: Mapped[Optional[str]] = mapped_column(Text)
    dimensions: Mapped[Optional[dict]] = mapped_column(MutableDict.as_mutable(JSONB))
    display_status: Mapped[DisplayStatus] = mapped_column(
        nullable=False, default=DisplayStatus.APPROVED
    )
    editions: Mapped[Set["Edition"]] = relationship(back_populates="inscription")
    figures: Mapped[Set[Figure]] = relationship(
        secondary=figure_inscription, back_populates="inscriptions"
    )
    filename: Mapped[str] = mapped_column(nullable=False, unique=True)
    iip_forms: Mapped[Set[IIPForm]] = relationship(
        secondary=iip_form_inscription, back_populates="inscriptions"
    )
    iip_genres: Mapped[Set[IIPGenre]] = relationship(
        secondary=iip_genre_inscription, back_populates="inscriptions"
    )
    iip_materials: Mapped[Set[IIPMaterial]] = relationship(
        secondary=iip_material_inscription, back_populates="inscriptions"
    )
    iip_preservation_id = mapped_column(ForeignKey("iip_preservations.id"))
    iip_preservation: Mapped[IIPPreservation] = relationship(
        back_populates="inscriptions"
    )
    iip_religions: Mapped[Set[IIPReligion]] = relationship(
        secondary=iip_religion_inscription, back_populates="inscriptions"
    )
    iip_writings: Mapped[Set[IIPWriting]] = relationship(
        secondary=iip_writing_inscription, back_populates="inscriptions"
    )
    images: Mapped[Set["Image"]] = relationship(back_populates="inscription")
    languages: Mapped[Set[Language]] = relationship(
        secondary=language_inscription, back_populates="inscriptions"
    )
    location_coordinates: Mapped[Optional[List[Float]]] = mapped_column(
        ARRAY(Float), nullable=True
    )
    location_metadata: Mapped[Optional[dict]] = mapped_column(
        MutableDict.as_mutable(JSONB)
    )
    not_after: Mapped[Optional[int]]
    not_before: Mapped[Optional[int]]
    parsed_at: Mapped[datetime.datetime]
    provenance_id = mapped_column(ForeignKey("provenances.id"), nullable=True)
    provenance: Mapped[Optional[Provenance]] = relationship(
        back_populates="inscriptions"
    )
    region_id = mapped_column(ForeignKey("regions.id"), nullable=True)
    region: Mapped[Optional[Region]] = relationship(back_populates="inscriptions")
    short_description: Mapped[Optional[str]]
    title: Mapped[Optional[str]]
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
        to_tsvector('english', 
            coalesce(description, '') || 
            coalesce(filename, '') || 
            coalesce(short_description, '') || 
            coalesce(title, '')
        )
        """
        ),
    )
```

An `Inscription` `belongs_to` a number of other objects (`City`, `Provenance`, etc. --- occasionally, as with `Language`, we need a join table), and it `has_many` `Edition` objects.

Every `Edition` must have an `edition_type`, defined as

```python
class EditionType(enum.Enum):
    DIPLOMATIC = "diplomatic"
    TRANSCRIPTION = "transcription"
    TRANSCRIPTION_SEGMENTED = "transcription_segmented"
    TRANSLATION = "translation"
```

We're using PostgreSQL's built-in [`TSVECTOR`](https://www.postgresql.org/docs/current/datatype-textsearch.html) column type to handle full-text search.

## Web Server

Source: [app.py](iip_search/app.py)

The web server defines a RESTful interface for interacting with the data. For the most part, they'll want to make `GET` requests to `/inscriptions`, with or without the query parameters to define their search criteria.

As a convenience (and breaking with REST conventions), we provide a `/map/inscriptions` endpoint that returns _all_ matching inscriptions, but without performing many of the `JOIN`s that take place for the paginated requests at `/inscriptions`.

## Deployment

You can get a general idea of how deployment works locally by running `docker compose up` from the root directory of this repository.

On Reclaim, we only use the [`Dockerfile`](../Dockerfile), rather than `docker compose`, as Reclaim provides the Postgres instance for us.

# License
