from datetime import datetime
from lxml import etree
from lxml.builder import E
import re


def default_availability_statement():
    return "The University of Michigan Library provides access to these materials for educational and research purposes." \
            " These materials may be under copyright." \
            " If you decide to use any of these materials, you are responsible for making your own legal assessment and securing any necessary permission." \
            " If you have questions about the collection, please contact the Bentley Historical Library at bentley.ref@umich.edu." \
            " If you have concerns about the inclusion of an item in this collection, please contact Library Information Technology at libraryit-info@umich.edu."


def blydenburgh_availability_statement():
    return "The University of Michigan Library provides access to these materials for educational and research purposes." \
            " Some materials may be protected by copyright. If you decide to use any of these materials, you are responsible" \
            " for making your own legal assessment and securing any necessary permission. If you would like to use these materials" \
            " commercially before 2039, please reach out to <a href=\"mailto:michael.odonnell@healthpromotionjournal.com\">Michael O\'Donnell</a>" \
            " or his heirs. If you have questions about the collection, please contact <a href=\"mailto:bentley.ref@umich.edu\">Bentley Historical Library</a>." \
            " If you have concerns about the inclusion of an item in this collection, please contact" \
            " <a href=\"mailto:LibraryIT-info@umich.edu\">Library Information Technology</a>."


def civilwar_availability_statement():
    return "The University of Michigan Library provides access to these materials for educational and research purposes." \
            " Very few of these materials may be protected by copyright." \
            " If you decide to use any of these materials, you are responsible for making your own legal assessment and securing any necessary permission." \
            " If you have questions about the collection, please contact the Bentley Historical Library at bentley.ref@umich.edu." \
            " If you have concerns about the inclusion of an item in this collection, please contact Library Information Technology at libraryit-info@umich.edu."


def get_dlxs_base_url():
    return "https://quod.lib.umich.edu"


def parse_extent_file(extent_file):
    existing_extents = {}
    tree = etree.parse(extent_file)
    rows = tree.xpath("//ROW")
    for row in rows:
        idno = row.xpath("./IDNO")[0].text
        extent = row.xpath("./EXTENT")[0].text
        existing_extents[idno] = extent
    return existing_extents


def make_breadcrumbs(hierarchy):
    breadcrumb_parts = hierarchy.split(" > ")
    breadcrumbs = E.KEYWORDS()
    index = 1
    for i in range(len(breadcrumb_parts)):
        breadcrumb = " > ".join(breadcrumb_parts[0:index])
        breadcrumbs.append(E.TERM({"TYPE": "breadcrumb"}, breadcrumb))
        index += 1
    return breadcrumbs


def make_keywords(subjects, agents):
    keywords = E.KEYWORDS()
    for agent in sorted(set(agents)):
        term = E.TERM(agent)
        keywords.append(term)
    for subject in sorted(set(subjects)):
        term = E.TERM(subject)
        keywords.append(term)
    return keywords


def make_item_note(note_type, abstract, general_note):
    if abstract:
        return E.NOTE(abstract)
    elif general_note:
        return E.NOTE(general_note)
    else:
        return E.NOTE("")


def sanitize_note(note_content):
    return re.sub(r"<.*?>", "", note_content).strip()


def make_item_notesstmt(abstract, general_note, scopecontent):
    notesstmt = E.NOTESSTMT()
    if scopecontent:
        notesstmt.append(E.NOTE(sanitize_note(scopecontent)))
        return notesstmt
    elif abstract:
        notesstmt.append(E.NOTE(sanitize_note(abstract)))
        return notesstmt
    elif general_note:
        notesstmt.append(E.NOTE(sanitize_note(general_note)))
        return notesstmt
    else:
        return ""


def make_availability_addendum(availability_addendum):
    if availability_addendum:
        return E.P(sanitize_note(availability_addendum))
    else:
        return ""


def make_sourcedesc_publicationstmt(date):
    if date:
        return E.PUBLICATIONSTMT(E.DATE(date))
    else:
        return ""


def make_filedesc_publicationstmt(identifier, rights_statement, availability_addendum):
    publicationstmt = E.PUBLICATIONSTMT(
                        E.PUBLISHER("University of Michigan Library"),
                        E.PUBPLACE("Ann Arbor, Michigan"),
                        E.DATE(str(datetime.now().year)),
                        E.IDNO({"TYPE": "dlps"}, identifier),
                        E.AVAILABILITY(
                            E.P(sanitize_note(rights_statement)),
                            make_availability_addendum(availability_addendum)
                        )
                    )
    return publicationstmt


def make_titlestmt(title, creator):
    return E.TITLESTMT(E.TITLE({"TYPE":"245"}, title), E.AUTHOR(creator))


def make_langusage():
    return E.LANGUSAGE({"ID":"eng"}, E.LANGUAGE("English"))


def make_editorialdecl(has_ocr):
    if has_ocr:
        text = """This electronic text file was created with uncorrected Optical Character
                Recognition (OCR). Encoding has been done using the recommendations for
                Level 1 of the TEI in Libraries Guidelines. Digital images are linked to
                the XML file."""
    else:
        text = """This electronic text file was created without Optical Character Recognition (OCR). 
                No transcription has been done of the content of the original document. Encoding has 
                been done using the recommendations for Level 1 of the TEI in Libraries Guidelines. 
                Digital images are linked to the XML file."""

    return E.EDITORIALDECL({"N":"1"}, E.P(text))

def make_header_type_attribs(has_ocr):
    if has_ocr:
        return {}
    else:
        return {"type": "noocr"}


def make_civilwar_header(collection_metadata, item_metadata):
    keywords = make_keywords(collection_metadata["subjects"], collection_metadata["agents"])
    item_notesstmt = make_item_notesstmt(item_metadata["abstract"], item_metadata["general_note"], item_metadata["scopecontent"])
    availability_addendum = make_availability_addendum(collection_metadata["availability_addendum"])
    sourcedesc_publicationstmt = make_sourcedesc_publicationstmt(item_metadata["date"])
    editorialdecl = make_editorialdecl(collection_metadata["has_ocr"])
    header_type_attribs = make_header_type_attribs(collection_metadata["has_ocr"])
    langusage = make_langusage()
    filedesc_publicationstmt = make_filedesc_publicationstmt(item_metadata["identifier"], 
                                                            collection_metadata["rights_statement"], 
                                                            collection_metadata["availability_addendum"])

    header = E.HEADER(header_type_attribs,
                E.FILEDESC(
                    make_titlestmt(item_metadata["title"], collection_metadata["creator"]),
                    E.EXTENT(item_metadata["extent_statement"]),
                    filedesc_publicationstmt,
                    E.SERIESSTMT(
                        E.TITLE(collection_metadata["title"])
                    ),
                    E.SOURCEDESC(
                        E.BIBFULL(
                            make_titlestmt(item_metadata["title"], collection_metadata["creator"]),
                            E.EXTENT(item_metadata["extent_statement"]),
                            sourcedesc_publicationstmt,
                            item_notesstmt

                        )
                    )
                ),
                E.ENCODINGDESC(
                    E.PROJECTDESC(
                        E.P("Header created with script DLXSMetadataPrep.py on {}".format(datetime.today().strftime("%Y-%m-%d")))
                    ),
                    editorialdecl
                ),
                E.PROFILEDESC(
                    langusage,
                    E.TEXTCLASS(
                        keywords
                    )
                )
            )
    return header


def make_polar_bear_header(collection_metadata, item_metadata):
    keywords = make_keywords(collection_metadata["subjects"], collection_metadata["agents"])
    item_notesstmt = make_item_notesstmt(item_metadata["abstract"], item_metadata["general_note"], item_metadata["scopecontent"])
    availability_addendum = make_availability_addendum(collection_metadata["availability_addendum"])
    sourcedesc_publicationstmt = make_sourcedesc_publicationstmt(item_metadata["date"])
    editorialdecl = make_editorialdecl(False)
    langusage = make_langusage()
    filedesc_publicationstmt = make_filedesc_publicationstmt(item_metadata["identifier"], 
                                                            collection_metadata["rights_statement"], 
                                                            collection_metadata["availability_addendum"])

    header = E.HEADER({"type": "noocr"},
                E.FILEDESC(
                    make_titlestmt(item_metadata["title"], collection_metadata["creator"]),
                    E.EXTENT(item_metadata["extent_statement"]),
                    filedesc_publicationstmt,
                    E.SOURCEDESC(
                        E.BIBFULL(
                            make_titlestmt(item_metadata["title"], collection_metadata["creator"]),
                            E.EXTENT(item_metadata["extent_statement"]),
                            sourcedesc_publicationstmt,
                            item_notesstmt

                        )
                    )
                ),
                E.ENCODINGDESC(
                    E.PROJECTDESC(
                        E.P("Header created with script DLXSMetadataPrep.py on {}".format(datetime.today().strftime("%Y-%m-%d")))
                    ),
                    editorialdecl
                ),
                E.PROFILEDESC(
                    langusage,
                    E.TEXTCLASS(
                        keywords
                    )
                )
            )
    return header


def make_header(collection_metadata, item_metadata):
    if len(item_metadata["hierarchy"]) > 0:
        breadcrumbs = make_breadcrumbs(item_metadata["hierarchy"])
        series_title = E.TITLE({"TYPE": "series"}, item_metadata["hierarchy"])
    else:
        breadcrumbs = ""
        series_title = ""
    item_notesstmt = make_item_notesstmt(item_metadata["abstract"], item_metadata["general_note"], item_metadata["scopecontent"])
    sourcedesc_publicationstmt = make_sourcedesc_publicationstmt(item_metadata["date"])
    editorialdecl = make_editorialdecl(collection_metadata["has_ocr"])
    langusage = make_langusage()
    header_type_attribs = make_header_type_attribs(collection_metadata["has_ocr"])
    filedesc_publicationstmt = make_filedesc_publicationstmt(item_metadata["identifier"], 
                                                            collection_metadata["rights_statement"], 
                                                            collection_metadata["availability_addendum"])

    header = E.HEADER(header_type_attribs,
                E.FILEDESC(
                    make_titlestmt(item_metadata["title"], collection_metadata["creator"]),
                    E.EXTENT(item_metadata["extent_statement"]),
                    filedesc_publicationstmt,
                    E.SERIESSTMT(
                        E.TITLE({"TYPE": "collection"}, collection_metadata["title"]),
                        series_title
                    ),
                    E.SOURCEDESC(
                        E.BIBLFULL(
                            make_titlestmt(item_metadata["title"], collection_metadata["creator"]),
                            E.EXTENT(item_metadata["extent_statement"]),
                            sourcedesc_publicationstmt,
                            item_notesstmt
                        )
                    )
                ),
                E.ENCODINGDESC(
                    E.PROJECTDESC(
                        E.P("Header created with script DLXSMetadataPrep.py on {}".format(datetime.today().strftime("%Y-%m-%d")))
                    ),
                    editorialdecl
                ),
                E.PROFILEDESC(
                    langusage,
                    E.TEXTCLASS(
                        breadcrumbs
                    )
                )

            )

    return header
