import datetime
import enum

from dataclasses import dataclass

from sqlalchemy import create_engine
from sqlalchemy import Column
from sqlalchemy import Computed
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import UniqueConstraint

from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import TSVECTOR

from sqlalchemy.ext.mutable import MutableDict

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import sessionmaker

from sqlalchemy.types import TypeDecorator

from typing import Optional
from typing import List
from typing import Set

from iip_search.db import Base


class TSVector(TypeDecorator):
    impl = TSVECTOR
    cache_ok = False


class City(Base):
    __tablename__ = "cities"
    __table_args__ = (UniqueConstraint("placename", name="city_placename"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    inscriptions: Mapped[Set["Inscription"]] = relationship(back_populates="city")
    placename: Mapped[str] = mapped_column(nullable=False)
    pleiades_ref: Mapped[str] = mapped_column(nullable=True)
    searchable_text = mapped_column(
        TSVector,
        Computed("to_tsvector('english', immutable_concat_ws(' ', placename, pleiades_ref))"
        ),
    )


"""
IIP{Form,Material,Genre,Preservation,Writing,Religion} should 
be validated against those listed
in include_taxonomies.xml (./classDecl/taxonomy[@xml:id="IIP-{form,material,genre,preservation,writing,religion}"]).

`xml_id` corresponds to the @xml:id attribute in the taxonomy, e.g.,
for
```xml
<category xml:id="funerary">
    <catDesc>Funerary</catDesc>
</category>
```
`xml_id` == "funerary"

`description` corresponds to the textValue of `catDesc`, e.g.,
for 
```xml
<category xml:id="funerary">
    <catDesc>Funerary</catDesc>
</category>
```
`description` == "Funerary"
"""


class IIPPreservation(Base):
    __tablename__ = "iip_preservations"
    __table_args__ = (UniqueConstraint("xml_id", name="iip_preservation_xml_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        back_populates="iip_preservation"
    )
    xml_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', coalesce(description, ''))
    """
        ),
    )


class Provenance(Base):
    __tablename__ = "provenances"
    __table_args__ = (UniqueConstraint("placename", name="provenance_placename"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inscriptions: Mapped[Set["Inscription"]] = relationship(back_populates="provenance")
    placename: Mapped[str]
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', coalesce(placename, ''))
    """
        ),
    )


class Region(Base):
    __tablename__ = "regions"
    __table_args__ = (UniqueConstraint("label", name="region_label"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inscriptions: Mapped[Set["Inscription"]] = relationship(back_populates="region")
    label: Mapped[str] = mapped_column(nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=False, unique=True
    )
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', immutable_concat_ws(' ', description, label))
    """
        ),
    )


figure_inscription = Table(
    "figure_inscription",
    Base.metadata,
    Column("figure_id", ForeignKey("figures.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

iip_form_inscription = Table(
    "iip_form_inscription",
    Base.metadata,
    Column("iip_form_id", ForeignKey("iip_forms.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

iip_genre_inscription = Table(
    "iip_genre_inscription",
    Base.metadata,
    Column("iip_genre_id", ForeignKey("iip_genres.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

iip_material_inscription = Table(
    "iip_material_inscription",
    Base.metadata,
    Column("iip_material_id", ForeignKey("iip_materials.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

iip_writing_inscription = Table(
    "iip_writing_inscription",
    Base.metadata,
    Column("iip_writing_id", ForeignKey("iip_writings.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

iip_religion_inscription = Table(
    "iip_religion_inscription",
    Base.metadata,
    Column("iip_religion_id", ForeignKey("iip_religions.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

inscription_bibliographic_entry = Table(
    "inscription_bibliographic_entry",
    Base.metadata,
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
    Column(
        "bibliographic_entry_id",
        ForeignKey("bibliographic_entries.id"),
        primary_key=True,
    ),
)

language_inscription = Table(
    "language_inscription",
    Base.metadata,
    Column("language_id", ForeignKey("languages.id"), primary_key=True),
    Column("inscription_id", ForeignKey("inscriptions.id"), primary_key=True),
)

"""
Example bibliography:
<div type="bibliography">
    <listBibl>
        <bibl xml:id="b1">
            <ptr type="biblItem" target="IIP-475.xml"/>
            <biblScope unit="page">52</biblScope>
        </bibl>
        <bibl xml:id="b2">
            <ptr type="biblItem" target="IIP-053.xml"/>
            <biblScope unit="page">57</biblScope>
        </bibl>
    </listBibl>
</div>
"""


class BibliographicEntry(Base):
    __tablename__ = "bibliographic_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    bibl_scope: Mapped[Optional[str]]
    bibl_scope_unit: Mapped[Optional[str]]
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        secondary=inscription_bibliographic_entry,
        back_populates="bibliographic_entries",
    )
    ptr_target: Mapped[Optional[str]]
    ptr_type: Mapped[Optional[str]]
    raw_xml: Mapped[str] = mapped_column(Text, nullable=False)
    xml_id: Mapped[str] = mapped_column(nullable=False)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector(immutable_concat_ws(' ', ptr_target, xml_id, raw_xml))
    """
        ),
    )


"""
  <xsl:template name="figure">
    <xsl:for-each select="tei:teiHeader/tei:fileDesc/tei:sourceDesc/tei:msDesc/tei:physDesc/tei:decoDesc/tei:decoNote">
      <xsl:variable name="desc" select="tei:ab/normalize-space()"/>
      <xsl:variable name="loc" select="tei:locus/normalize-space()"/>
      <xsl:if test="$desc!= ''">
        <xsl:element name="field">
          <xsl:attribute name="name">figure_desc</xsl:attribute>
          <xsl:value-of select="$desc"/>
        </xsl:element>
      </xsl:if>
      <xsl:if test="$loc != ''">
        <xsl:element name="field">
          <xsl:attribute name="name">figure</xsl:attribute>
          <xsl:value-of select="translate($desc, '#', '')"/> (<xsl:value-of select="$loc"/>)</xsl:element>
      </xsl:if>
    </xsl:for-each>
  </xsl:template>
"""


class Figure(Base):
    __tablename__ = "figures"
    __table_args__ = (UniqueConstraint("name", name="figure_name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        back_populates="figures", secondary=figure_inscription
    )
    # the name field corresponds to the text value of the <ab> tags
    name: Mapped[str] = mapped_column(Text)
    locus: Mapped[Optional[str]] = mapped_column(Text)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', immutable_concat_ws(' ', locus, name))
    """
        ),
    )


class IIPForm(Base):
    __tablename__ = "iip_forms"
    __table_args__ = (UniqueConstraint("xml_id", name="iip_form_xml_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    ana: Mapped[str] = mapped_column(nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        back_populates="iip_forms", secondary=iip_form_inscription
    )
    xml_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', immutable_concat_ws(' ', description, ana))
    """
        ),
    )


class IIPGenre(Base):
    __tablename__ = "iip_genres"
    __table_args__ = (UniqueConstraint("xml_id", name="iip_genre_xml_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        secondary=iip_genre_inscription, back_populates="iip_genres"
    )
    xml_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', coalesce(description, ''))
    """
        ),
    )


class IIPMaterial(Base):
    __tablename__ = "iip_materials"
    __table_args__ = (UniqueConstraint("xml_id", name="iip_material_xml_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        secondary=iip_material_inscription, back_populates="iip_materials"
    )
    xml_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', coalesce(description, ''))
    """
        ),
    )


class IIPReligion(Base):
    __tablename__ = "iip_religions"
    __table_args__ = (UniqueConstraint("xml_id", name="iip_religion_xml_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        secondary=iip_religion_inscription, back_populates="iip_religions"
    )
    xml_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', coalesce(description, ''))
    """
        ),
    )


class IIPWriting(Base):
    __tablename__ = "iip_writings"
    __table_args__ = (UniqueConstraint("xml_id", name="iip_writing_xml_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        secondary=iip_writing_inscription, back_populates="iip_writings"
    )
    note: Mapped[str] = mapped_column(nullable=True)
    xml_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', immutable_concat_ws(' ', description, note))
    """
        ),
    )


class Language(Base):
    __tablename__ = "languages"
    __table_args__ = (UniqueConstraint("label", name="language_label"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    inscriptions: Mapped[Set["Inscription"]] = relationship(
        secondary=language_inscription, back_populates="languages"
    )
    label: Mapped[str] = mapped_column(nullable=False, unique=True)
    short_form: Mapped[str] = mapped_column(nullable=False, unique=True)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
    to_tsvector('english', immutable_concat_ws(' ', short_form, label))
    """
        ),
    )


class DisplayStatus(enum.Enum):
    APPROVED = "approved"
    TO_CORRECT = "to correct"
    TO_APPROVE = "to approve"


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
        to_tsvector('english', immutable_concat_ws(' ', description, replace(filename, '.xml', ''), short_description, title))
        """
        ),
    )


"""
<facsimile xmlns:xi="http://www.w3.org/2001/XInclude">
    <surface>
        <desc>Gary Todd - Flickr (public domain)</desc>
        <graphic url="cape0002.jpg"/>
        <note>https://www.flickr.com/photos/101561334@N08/43293429452/in/album-72157668660233597/</note>
    </surface>
</facsimile>
"""


class Image(Base):
    __tablename__ = "images"

    id: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    graphic_url: Mapped[str] = mapped_column(nullable=False)
    inscription_id: Mapped[int] = mapped_column(ForeignKey("inscriptions.id"))
    inscription: Mapped[Inscription] = relationship(back_populates="images")


class EditionType(enum.Enum):
    DIPLOMATIC = "diplomatic"
    TRANSCRIPTION = "transcription"
    TRANSCRIPTION_SEGMENTED = "transcription_segmented"
    TRANSLATION = "translation"


class Edition(Base):
    __tablename__ = "editions"
    __table_args__ = (
        UniqueConstraint(
            "edition_type",
            "inscription_id",
            name="edition_type_inscription_id",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    edition_type: Mapped[EditionType]
    inscription_id = mapped_column(ForeignKey("inscriptions.id"))
    inscription: Mapped["Inscription"] = relationship(back_populates="editions")
    # NOTE: (charles) Since we're using Postgres, we *could* use the built-in
    # XML type. But there's really no advantage in doing so unless
    # we plan to query against this column. As it stands now, this column
    # is mainly a sanity check to make sure that the derived `text` field
    # looks correct.
    raw_xml: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    searchable_text = mapped_column(
        TSVector,
        Computed(
            """
        to_tsvector('english', regexp_replace(normalize(text, NFKD), '[\u0300-\u036f]', '', 'g'))
        """,
            persisted=True,
        ),
    )
