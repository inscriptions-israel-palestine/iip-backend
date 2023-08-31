import logging
import re

from lxml import etree
from pathlib import Path

NAMESPACES = {
    "tei": "http://www.tei-c.org/ns/1.0",
    "xml": "http://www.w3.org/XML/1998/namespace",
}
TAXONOMY_FILE = Path("./include_taxonomies.xml")
XML_ID_ATTRIB = "{http://www.w3.org/XML/1998/namespace}id"
XML_LANG_ATTRIB = "{http://www.w3.org/XML/1998/namespace}lang"

logging.basicConfig(format="%(levelname)s: %(asctime)s %(message)s", level=logging.INFO)

whitespace_regex = re.compile(r"\s+")

IMAGE_URL_PREFIX = "//github.com/Brown-University-Library/iip-images/raw/master"

LANGUAGES = {
    "arc": {
        "label": "Aramaic",
    },
    "arc-grc": {
        "label": "Aramaic transliterated in Greek",
    },
    # See beth0023.xml for arc-Grek example
    "arc-Grek": {"label": "Aramaic transliterated in Greek", "short_form": "arc-grc"},
    "egy": {"label": "Egyptian"},
    "geo": {
        "label": "Georgian",
    },
    "grc": {
        "label": "Greek",
    },
    "hbo": {"label": "Hebrew", "short_form": "heb"},
    "he": {"label": "Hebrew", "short_form": "heb"},
    "heb": {
        "label": "Hebrew",
    },
    "la": {
        "label": "Latin",
        "short_form": "lat",
    },
    "lat": {"label": "Latin"},
    "Other": {
        "label": "Other",
    },
    "phn": {
        "label": "Phoenician",
    },
    "syc": {
        "label": "Syriac",
    },
    # See beth0045.xml for x-greek-hebrew example
    "x-greek-hebrew": {"label": "Hebrew transliterated in Greek"},
    "x-Arabic": {"label": "Arabic"},
    "x-Nabatean": {"label": "Nabatean"},
    "x-Palmyran": {"label": "Palmyran"},
    "x-Semitic": {"label": "Semitic"},
    "x-unknown": {
        "label": "Unknown",
    },
    "xcl": {"label": "Armenian"},
}


class EpidocParser:
    bibliography_xpath = (
        "//tei:text/tei:back/tei:div[@type = 'bibliography']/tei:listBibl/tei:bibl"
    )
    dimensions_xpath = "//tei:dimensions"
    iip_form_description_xpath = (
        "//tei:sourceDesc/tei:msDesc/tei:physDesc/tei:objectDesc"
    )
    diplomatic_xpath = (
        "//tei:text/tei:body/tei:div[@type = 'edition' and @subtype = 'diplomatic']"
    )
    transcription_xpath = (
        "//tei:text/tei:body/tei:div[@type = 'edition' and @subtype = 'transcription']"
    )
    transcription_segmented_xpath = "//tei:text/tei:body/tei:div[@type = 'edition' and @subtype = 'transcription_segmented']"
    translation_xpath = "//tei:text/tei:body/tei:div[@type = 'translation']"

    def __init__(self, filename):
        self.filename = filename
        self.taxonomies = self._get_taxonomies()
        self.tree = self._parse_file()

    # ------- Begin Inscription fields and relations ------- #

    def get_bibliography(self):
        entries = []
        for bibl in self.tree.iterfind(self.bibliography_xpath, namespaces=NAMESPACES):
            xml_id = bibl.attrib.get(XML_ID_ATTRIB)

            if xml_id is not None:
                bibl_scope = bibl.find("./tei:biblScope", namespaces=NAMESPACES)
                bibl_scope_unit = bibl_scope.attrib.get("unit")
                bibl_scope_text = bibl_scope.text
                ptr = bibl.find("./tei:ptr", namespaces=NAMESPACES)
                ptr_target = ptr.attrib.get("target")
                ptr_type = ptr.attrib.get("type")

                entries.append(
                    dict(
                        xml_id=xml_id,
                        bibl_scope=bibl_scope_text,
                        bibl_scope_unit=bibl_scope_unit,
                        ptr_target=ptr_target,
                        ptr_type=ptr_type,
                        raw_xml=etree.tostring(bibl, encoding="unicode"),
                    )
                )
        return entries

    def get_city(self):
        settlement = self.tree.find(
            "//tei:placeName/tei:settlement", namespaces=NAMESPACES
        )

        if settlement is not None:
            try:
                placename = whitespace_regex.sub(" ", settlement.text).strip()
            except TypeError:
                logging.warn(f"No placename provided for {self.filename}.")
                placename = "No placename provided"

            return dict(
                placename=placename,
                pleiades_ref=settlement.get("ref"),
            )

    def get_description(self):
        commentary = self.tree.xpath(
            "//tei:div[@type = 'commentary']/tei:p/text()", namespaces=NAMESPACES
        )

        if len(commentary) > 0:
            return whitespace_regex.sub(" ", commentary[0]).strip()

        return None

    def get_dimensions(self):
        dimensions = []
        for dimension_entry in self.tree.iterfind(
            self.dimensions_xpath, namespaces=NAMESPACES
        ):
            attributes = dict(dimension_entry.attrib)

            depth = dimension_entry.xpath("./tei:depth/text()", namespaces=NAMESPACES)
            height = dimension_entry.xpath("./tei:height/text()", namespaces=NAMESPACES)
            width = dimension_entry.xpath("./tei:width/text()", namespaces=NAMESPACES)

            depth = depth[0] if len(depth) > 0 else None
            height = height[0] if len(height) > 0 else None
            width = width[0] if len(width) > 0 else None
            entry = {"depth": depth, "height": height, "width": width}
            entry.update(attributes)
            dimensions.append(entry)

        return dimensions

    def get_figures(self):
        figures = []
        for figure in self.tree.iterfind(
            "//tei:decoDesc/tei:decoNote", namespaces=NAMESPACES
        ):
            name = figure.xpath("./tei:ab/text()", namespaces=NAMESPACES)
            locus = figure.xpath("./tei:locus/text()", namespaces=NAMESPACES)
            if len(name) > 0 and len(locus) > 0:
                figures.append(dict(name=name[0], locus=locus[0]))

        return figures

    def get_iip_forms(self):
        object_description = self.tree.find(
            self.iip_form_description_xpath, namespaces=NAMESPACES
        )

        ana = object_description.get("ana")

        if ana is not None:
            forms = []
            for form in ana.replace("#", "").split(" "):
                taxonomy = self.taxonomies.get("forms")
                # Some forms that appear in documents, like "handle in tjez0004",
                # are not present in the taxonomy.
                ana = taxonomy.get(form, {}).get("ana")
                description = taxonomy.get(form, {}).get("description")

                forms.append(dict(xml_id=form, ana=ana, description=description))

            return forms

        return None

    def get_iip_genres(self):
        ms_item = self.tree.find("//tei:msItem", namespaces=NAMESPACES)
        ms_item_class = ms_item.get("class")

        if ms_item_class is not None:
            genres = []

            for genre in ms_item_class.replace("#", "").split(" "):
                # Some genres that appear in documents, like "commodity_chit",
                # are not present in the taxonomy.
                description = (
                    self.taxonomies.get("genres").get(genre, {}).get("description")
                )

                genres.append(dict(xml_id=genre, description=description))

            return genres

        return None

    def get_iip_materials(self):
        support_desc = self.tree.find("//tei:supportDesc", namespaces=NAMESPACES)
        ana = support_desc.get("ana")

        materials = []
        if ana is not None:
            anas = ana.replace("#", "").split(" ")

            for material in anas:
                materials.append(
                    dict(
                        xml_id=material,
                        description=self.taxonomies.get("materials")
                        .get(material.lower(), {})
                        .get("description", material),
                    )
                )
        return materials

    def get_iip_preservation(self):
        preservation = self.tree.find("//tei:condition", namespaces=NAMESPACES)
        ana = preservation.get("ana")

        if ana is not None:
            ana = ana.replace("#", "")

            return dict(
                xml_id=ana,
                description=self.taxonomies.get("preservations")
                .get(ana, {})
                .get("description", ana),
            )

        return None

    def get_iip_religions(self):
        ms_item = self.tree.find("//tei:msItem", namespaces=NAMESPACES)
        ana = ms_item.get("ana")

        if ana is not None:
            religions = []

            for religion in ana.replace("#", "").split(" "):
                # escape hatch for bad encoding in hamm0009.xml (and possibly elsewhere)
                if religion == "unknown":
                    religion = "unknown_religion"

                religions.append(
                    dict(
                        xml_id=religion,
                        description=self.taxonomies.get("religions")[religion].get(
                            "description"
                        ),
                    )
                )

            return religions

        return None

    def get_iip_writings(self):
        hand_note = self.tree.find("//tei:handNote", namespaces=NAMESPACES)
        ana = hand_note.get("ana")

        if ana is not None:
            ana = ana.replace("#", "")
            note = hand_note.find("./tei:p", namespaces=NAMESPACES)

            if note is not None:
                note = note.text
            # Some writings that appear in documents, like "engraved",
            # are not present in the taxonomy.
            description = (
                self.taxonomies.get("writings").get(ana, {}).get("description")
            )
            return [
                dict(
                    xml_id=ana,
                    note=note,
                    description=description,
                )
            ]

        return None

    def get_images(self):
        images = []

        main_image = self.tree.find(
            "//tei:facsimile/tei:graphic", namespaces=NAMESPACES
        )

        if main_image is not None:
            url = main_image.get("url")

            if url != "":
                images.append(
                    dict(graphic_url=f"{IMAGE_URL_PREFIX}/{main_image.get('url')}")
                )

        for image in self.tree.iterfind(
            "//tei:facsimile/tei:surface", namespaces=NAMESPACES
        ):
            desc_tag = image.find("./tei:desc", namespaces=NAMESPACES)
            graphic_tag = image.find("./tei:graphic", namespaces=NAMESPACES)

            if graphic_tag is not None:
                graphic_url = graphic_tag.get("url", "")

                description = None

                if desc_tag is not None:
                    description = desc_tag.text

                if len(graphic_url) > 0:
                    images.append(
                        dict(
                            description=description,
                            graphic_url=f"{IMAGE_URL_PREFIX}/{graphic_url}",
                        )
                    )

        return images

    def get_languages(self):
        lang_codes = set()
        for tag in self.tree.iterfind(
            f"//*[@{XML_LANG_ATTRIB}]", namespaces=NAMESPACES
        ):
            lang = tag.get(XML_LANG_ATTRIB).strip()
            logging.debug(f"Looking up short form for {lang}...")

            if lang.strip() == "":
                continue

            short_form = LANGUAGES.get(lang).get("short_form", lang)

            lang_codes.add(short_form)

        languages = []
        for short_form in list(lang_codes):
            label = LANGUAGES.get(short_form).get("label")

            # TODO: This check is most likely unnecessary, but it's worth
            # keeping an eye on.
            if label is not None:
                languages.append(dict(label=label, short_form=short_form))
            else:
                logging.warn(
                    f"No language label found for short (ISO 639-3) form {short_form}."
                )

        return languages

    def get_location_coordinates(self):
        geo = self.tree.xpath("//tei:geo/text()", namespaces=NAMESPACES)

        if len(geo) > 0:
            try:
                # the location coordinates are listed as lat,lng
                # in the EpiDoc files, but Mapbox requires lng,lat pairs.
                coords = [float(s) for s in geo[0].strip().split(",")].reverse()
            except ValueError:
                logging.error(f"Incorrect geo coordinates: {geo[0]}.")

                return None

            return coords

    def get_location_metadata(self):
        locus = self.tree.xpath(
            "//tei:geogFeat[@type='locus']/text()", namespaces=NAMESPACES
        )
        site = self.tree.xpath(
            "//tei:geogName[@type='site']/text()", namespaces=NAMESPACES
        )

        metadata = {}
        if len(locus) > 0:
            metadata["locus"] = locus[0]

        if len(site) > 0:
            metadata["site"] = site[0]

        return metadata

    def get_not_before(self):
        date = self.tree.find("//tei:origin/tei:date", namespaces=NAMESPACES)

        if date is not None:
            not_before = date.get("notBefore")

            if not_before is not None:
                return int(not_before)

        return None

    def get_not_after(self):
        date = self.tree.find("//tei:origin/tei:date", namespaces=NAMESPACES)

        if date is not None:
            not_after = date.get("notAfter")

            if not_after is not None:
                return int(not_after)

        return None

    def get_provenance(self):
        provenance_tag = self.tree.find(
            "//tei:history/tei:provenance", namespaces=NAMESPACES
        )

        if provenance_tag is not None:
            placename = provenance_tag.find("./tei:placeName", namespaces=NAMESPACES)

            if placename is not None:
                return dict(placename=placename.text)

        return None

    def get_region(self):
        region_tag = self.tree.find(
            "//tei:history/tei:origin/tei:region", namespaces=NAMESPACES
        )

        if region_tag is not None:
            return dict(label=region_tag.text)

        return None

    def get_short_description(self):
        pass

    def get_title(self):
        ms_item_text = self.tree.xpath(
            "//tei:msDesc/tei:msContents/tei:msItem/*/text()", namespaces=NAMESPACES
        )

        if len(ms_item_text) > 0:
            return ms_item_text[0].strip()

        return None

    # ------- End Inscription fields and relations ------- #

    def get_edition(self, xpath):
        editions = self.tree.xpath(xpath, namespaces=NAMESPACES)

        if len(editions) > 1:
            logging.warn(
                f"Expected to find a single edition, but found {len(editions)} for {xpath} in {etree.tostring(self.tree, encoding='unicode')}."
            )

        if len(editions) == 0:
            return None

        return editions[0]

    def get_text_elements(self, xpath):
        return self.tree.xpath(f"{xpath}/tei:p/*", namespaces=NAMESPACES)

    def get_diplomatic(self):
        return self._stringify_xml_and_text(self.diplomatic_xpath)

    def get_transcription(self):
        return self._stringify_xml_and_text(self.transcription_xpath)

    def get_transcription_segmented(self):
        return self._stringify_xml_and_text(self.transcription_segmented_xpath)

    def get_translation(self):
        return self._stringify_xml_and_text(self.translation_xpath)

    def _get_taxonomies(self):
        tree = etree.parse(TAXONOMY_FILE)

        forms = self._get_taxonomy(tree, "form")
        genres = self._get_taxonomy(tree, "genre")
        materials = self._get_taxonomy(tree, "materials")
        preservations = self._get_taxonomy(tree, "preservation")
        religions = self._get_taxonomy(tree, "religion")
        writings = self._get_taxonomy(tree, "writing")

        return {
            "forms": forms,
            "genres": genres,
            "materials": materials,
            "preservations": preservations,
            "religions": religions,
            "writings": writings,
        }

    def _get_taxonomy(self, tree, taxonomy_name):
        logging.info(f"Getting {taxonomy_name} taxonomy...")
        taxonomy = {}
        for item in tree.find(
            f"//tei:taxonomy[@xml:id = 'IIP-{taxonomy_name}']", namespaces=NAMESPACES
        ):
            xml_id = item.get(XML_ID_ATTRIB)
            taxonomy[xml_id] = {}

            # only forms appear to have an @ana attribute
            if taxonomy_name == "form":
                taxonomy[xml_id]["ana"] = item.get("ana")

            description = item.find("./tei:catDesc", namespaces=NAMESPACES)
            taxonomy[xml_id]["description"] = (
                description.text if description is not None else description
            )

        return taxonomy

    def _parse_file(self):
        logging.info(f"Attempting to parse {self.filename}.")

        return etree.parse(self.filename)

    def _stringify_xml_and_text(self, xpath):
        edition = self.get_edition(xpath)

        if edition is not None:
            text = etree.tostring(edition, encoding="unicode", method="text").strip()
            xml = etree.tostring(edition, encoding="unicode")

            return (xml, text)

        logging.warning(f"No nodes found for {xpath} in {self.filename}.")

        return (None, None)
