from HTMLParser import HTMLParser
from lxml import etree
from lxml.html.builder import *
import os
import re
import shutil
import xml.etree.ElementTree as ET
import requests
import sys


def make_availability_addendum(availability_addendum):
    element = etree.Element("div")
    availability_addendum_div = etree.SubElement(element, "div")
    availability_addendum_div.text = availability_addendum
    etree.SubElement(element, "hr")
    return etree.tostring(element)


def make_display_string(component):
    did = component.xpath("./did")[0]
    display_string_parts = []
    unittitles = did.xpath("./unittitle")
    if unittitles:
        title_text = re.sub(r"<\/?.*?>", "", etree.tostring(unittitles[0]))
        display_string_parts.append(title_text.strip().encode("utf-8"))
    inclusive_dates = []
    bulk_dates = []
    unitdates = did.xpath("./unitdate")
    for unitdate in unitdates:
        if unitdate.attrib["type"] == "inclusive":
            inclusive_dates.append(unitdate.text.strip().encode("utf-8"))
        elif unitdate.attrib["type"] == "bulk":
            bulk_dates.append(unitdate.text.strip().encode("utf-8"))
    if inclusive_dates:
        component_dates = ", ".join(inclusive_dates)
        if bulk_dates:
            component_dates += " (bulk {})".format(", ".join(bulk_dates))
        display_string_parts.append(component_dates)
    return ", ".join(display_string_parts).encode('utf-8')


def convert_subtags(note):
    chronlists = note.xpath("./chronlist")
    lists = note.xpath("./list")
    linking_titles = note.xpath(".//title[@href]")
    italicized_titles = note.xpath(".//title[@render='italic']")
    for chronlist in chronlists:
        chronlist_head = chronlist.xpath("./head")[0]
        chronlist_head.tag = "h3"
        chronlist_items = chronlist.xpath("./chronitem")
        for chronlist_item in chronlist_items:
            item_date = chronlist_item.xpath("./date")[0]
            item_eventgrp = chronlist_item.xpath("./eventgrp")[0]
            item_eventgrp.text = re.sub(
                r"<.*?>", "", etree.tostring(item_eventgrp)).strip()
            item_eventgrp_items = item_eventgrp.xpath(".//event")
            for item in item_eventgrp_items:
                item_eventgrp.remove(item)
            item_date.tag = "td"
            item_eventgrp.tag = "td"
            chronlist_item.tag = "tr"
        chronlist.attrib["class"] = "table"
        chronlist.tag = "table"
    for note_list in lists:
        list_type = note_list.attrib["type"]
        if list_type == "ordered":
            items = note_list.xpath(".//item")
            sublists = note_list.xpath(".//list")
            for item in items:
                item.tag = "li"
            for sublist in sublists:
                sublist.tag = "ol"
            note_list.tag = "ol"
    for linking_title in linking_titles:
        non_href_attribs = [
            attrib for attrib in linking_title.attrib if attrib != "href"]
        for non_href_attrib in non_href_attribs:
            del linking_title.attrib[non_href_attrib]
        linking_title.tag = "a"
        linking_title.attrib["target"] = "_blank"
    for title in italicized_titles:
        title.tag = "cite"
    return note


def make_collapsible_element(component):
    tag = "button"
    attribs = {}
    attribs["class"] = "list-group-item"
    attribs["data-toggle"] = "collapse"
    attribs["href"] = "#{}".format(component.attrib["id"])
    element = etree.Element(tag, attribs)
    glyphicon = etree.SubElement(element, "i")
    glyphicon.attrib["class"] = "glyphicon glyphicon-chevron-down"
    glyphicon.text = ""
    text_span = etree.SubElement(element, "span")
    text_span.attrib["class"] = component.tag
    text_span.text = make_display_string(component)
    return element


def make_series_element(component, series_number):
    section_element = etree.Element("section")
    section_element.attrib["class"] = "series"
    list_element = etree.SubElement(section_element, "div")
    list_element.attrib["class"] = "list-group list-group-root"
    series_element = etree.SubElement(list_element, "div")
    series_element.attrib["href"] = "#{}".format(component.attrib["id"])
    series_element.attrib["id"] = "series{}".format(series_number)
    header = etree.SubElement(series_element, "h2")
    header.text = make_display_string(component)
    if component.xpath("./scopecontent"):
        scopecontent_header_element = etree.SubElement(series_element, "h3")
        scopecontent_header_element.text = "Series Overview"
        scopecontent_text = extract_series_scopecontent_text(component)
        scopecontent_text_element = etree.SubElement(series_element, "div")
        scopecontent_text_element.attrib["class"] = "series-overview"
        scopecontent_text_element.text = scopecontent_text
    return section_element


def make_noncollapsible_element(component):
    tag = "div"
    attribs = {}
    attribs["class"] = "list-group-item"
    component_id = component.attrib["id"]
    if component.tag == "c01":
        component_id += "_daos"
    attribs["href"] = "#{}".format(component_id)
    element = etree.Element(tag, attribs)
    element.text = make_display_string(component)
    return element


def make_linking_element(link, element_text):
    tag = "a"
    attribs = {}
    attribs["class"] = "list-group-item"
    attribs["target"] = "_blank"
    attribs["href"] = link
    element = etree.Element(tag, attribs)
    element.text = element_text
    # if the link starts with http, it's an absolute link, not relative, which means it's outside of the textclass collection
    if link.startswith("http"):
        element.text += " "
        glyphicon = etree.SubElement(element, "i")
        glyphicon.attrib["class"] = "glyphicon glyphicon-new-window"
        glyphicon.text = ""
    return element


def make_title_from_note(dao):
    digital_object_note = dao.xpath("./daodesc/p")[0].text.strip("[] ")
    link_title = digital_object_note.replace("view", "").strip().title()
    return link_title


def make_parent_element(component_parent_id, component_tag, collapse=True):
    tag = "div"
    attribs = {}
    attribs["id"] = component_parent_id
    if component_tag not in ["c01", "c02"] and collapse:
        attribs["class"] = "list-group collapse"
    else:
        attribs["class"] = "list-group"
    element = etree.Element(tag, attribs)
    return element


def extract_first_link(component):
    dao = component.xpath(".//dao")[0]
    return dao.attrib["href"]


def extract_series_scopecontent_text(component):
    scopecontent_path = component.xpath("./scopecontent")
    if scopecontent_path:
        scopecontent = scopecontent_path[0]
        convert_subtags(scopecontent)
        scopecontent_text = re.sub(r"</?scopecontent.*?>", "", etree.tostring(scopecontent)).strip()
        return scopecontent_text
    else:
        return ""


def make_iiif_link(collection_shortname, item_id, dry_run):
    iiif_base_url = "https://preview.quod.lib.umich.edu"
    image_id = "/cgi/t/text/api/image/{}:{}:00000001".format(collection_shortname, item_id)
    image_base_url = "{}{}".format(iiif_base_url, image_id)
    iiif_info_url = "{}/info.json".format(image_base_url)
    iiif_info = requests.get(iiif_info_url).json()
    height = iiif_info["height"]
    width = iiif_info["width"]
    half_width = width / 2
    half_height = height / 2
    crop_x_coordinate = half_width / 2
    crop_height = half_width / (5/float(3))
    crop_y_coordinate = half_height - (crop_height/2)
    region = "{},{},{},{}".format(int(crop_x_coordinate), int(crop_y_coordinate), int(half_width), int(crop_height))
    selection_suffix = "/{}/full/0/default.jpg".format(region)
    if dry_run:
        # return a URL for an image that will display locally
        return "{}{}".format(image_base_url, selection_suffix)
    else:
        # return a URL for an image that will only display in DLXS
        return "{}{}".format(image_id, selection_suffix)


def make_series_card(DLXSMetadataPrepper, series_dict, series_number, dry_run):
    digital_object = series_dict["digital_object"]
    collection_path = DLXSMetadataPrepper.dlxs_collection
    textclass_link_regex = re.compile(r".*?quod\.lib\.umich\.edu" + collection_path + r".*?$")
    if textclass_link_regex.match(digital_object):
        link = re.sub(r"(.*?)(" + collection_path + ".*?$)", r"\2", digital_object)
        collection_shortname = link.split("/")[2]
        item_id = link.split("/")[3]
        image_link = make_iiif_link(collection_shortname, item_id, dry_run)
    else:
        image_link = "graphics/series{}.jpg".format(series_number)
    wrapper_element = etree.Element("div", {"class": "col-sm-6"})
    series_panel_element = etree.SubElement(wrapper_element, "div")
    series_panel_element.attrib["class"] = "panel panel-default series-card"
    panel_body = etree.SubElement(series_panel_element, "div")
    panel_body.attrib["class"] = "panel-body"
    img = etree.SubElement(panel_body, "img")
    img.attrib["src"] = image_link
    img.attrib["alt"] = ""
    img.attrib["class"] = "img-responsive"
    header = etree.SubElement(panel_body, "h3")
    anchor = etree.SubElement(header, "a")
    anchor.attrib["href"] = "browse.html#series{}".format(series_number)
    anchor.text = series_dict["title"]
    if series_dict.get("scopecontent"):
        series_overview = series_dict["scopecontent"]
        if len(series_overview) > 155:
            series_overview = series_overview[:155] + " ... "
        series_overview_element = etree.SubElement(panel_body, "p")
        series_overview_element.text = sanitize_text(series_overview)
    return wrapper_element


def sanitize_text(text):
    return re.sub(r"</?.*?>", "", text)


# series_dicts needs: [{"series_title": "", "first_link": "", "series_overview": "", "image": ""}]
def make_series_cards(DLXSMetadataPrepper, series_dicts, dry_run):
    tag = "div"
    attribs = {}
    attribs["class"] = "row series-cards"
    series_cards_element = etree.Element(tag, attribs)
    for i, series_dict in enumerate(series_dicts):
        series_card_element = make_series_card(DLXSMetadataPrepper, series_dict, i+1, dry_run)
        series_cards_element.append(series_card_element)
    return series_cards_element


def parse_ead(DLXSMetadataPrepper, redownload_ead):
    collection_dir = DLXSMetadataPrepper.collection_dir
    ead_filepath = os.path.join(collection_dir, "ead.xml")
    if redownload_ead or not os.path.exists(ead_filepath):
        download_ead(DLXSMetadataPrepper, ead_filepath)
    tree = etree.parse(ead_filepath)
    collection_info = get_collection_info(tree)
    series_dicts = get_series_dicts(tree)
    browse_contents = get_browse_contents(DLXSMetadataPrepper, tree)

    return {
        "collection_info": collection_info,
        "series_dicts": series_dicts,
        "browse_contents": browse_contents
        }


def get_collection_info(tree):
    collection_info = {}
    abstract = tree.xpath("//archdesc/did/abstract")[0]
    convert_subtags(abstract)
    abstract_text = re.sub(r"</?abstract.*?>", "", etree.tostring(abstract)).strip().encode("utf-8")
    collection_title = tree.xpath("//archdesc/did/unittitle")[0].text.strip().encode("utf-8") \
        .replace("records", "Records") \
        .replace("papers", "Papers") \
        .replace("collection", "Collection")
    inclusive_dates = []
    collection_date_paths = tree.xpath("//archdesc/did/unitdate")
    for collection_date in collection_date_paths:
        if collection_date.attrib["type"] == "inclusive":
            inclusive_dates.append(collection_date.text.strip().encode("utf-8"))
    collection_dates = ", ".join(inclusive_dates)
    collection_display_string = "{}, {}".format(collection_title, collection_dates)
    ead_id = tree.xpath("//eadid")[0].text.strip()
    collection_info["abstract"] = abstract_text
    collection_info["title"] = collection_display_string
    collection_info["ead_id"] = ead_id
    return collection_info


def get_series_dicts(tree):
    # title, scopecontent, first digital object
    series_dicts = []
    series_to_include = [series for series in tree.xpath("//c01") if series.xpath(".//dao")]
    for series in series_to_include:
        series_info = {}
        series_info["title"] = make_display_string(series)
        series_info["scopecontent"] = extract_series_scopecontent_text(series)
        series_info["digital_object"] = extract_first_link(series)
        series_dicts.append(series_info)
    return series_dicts


def get_browse_contents(DLXSMetadataPrepper, tree):
    collection_path = DLXSMetadataPrepper.dlxs_collection
    textclass_link_regex = re.compile( r".*?quod\.lib\.umich\.edu" + collection_path + r".*?$")
    dsc = tree.xpath("//dsc")[0]
    components_to_include = [component for component in dsc.xpath("//*[starts-with(local-name(), 'c0')]") if component.xpath(".//dao")]
    component_paths = [tree.getpath(component) for component in components_to_include]
    contents_list = etree.Element("div", {"id": "series-container"})
    for component_path in component_paths:
        component = tree.xpath(component_path)[0]
        if component.tag != "c01":
            component_parent_id = component.getparent().attrib["id"]
            parent_element = contents_list.xpath('//*[@id="{}"]'.format(component_parent_id))
        elif component.tag == "c01":
            series_number = tree.xpath("//c01").index(component) + 1
            element = make_series_element(component, series_number)
            contents_list.xpath("//*[@id='series-container']")[0].append(element)
        daos = component.xpath("./did/dao")
        if daos:
            if component.tag == "c01":
                component_parent_id = component.attrib["id"]
                parent_element = contents_list.xpath('//*[@id="{}"]'.format(component_parent_id))
            if len(daos) == 1:
                dao = daos[0]
                link = dao.attrib["href"].strip()
                # Check if it's part of the text class collection; if so, make the link relative, not absolute
                if textclass_link_regex.match(link):
                    link = re.sub(r"(.*?)(" + collection_path + ".*?$)", r"\2", link)
                element_text = make_display_string(component)
                element = make_linking_element(link, element_text)
                if not parent_element:
                    parent_element_html = make_parent_element(component_parent_id, component.tag)
                    grandparent_element = contents_list.xpath('//*[@href="#{}"]'.format(component_parent_id))[0]
                    greatgrandparent_element = grandparent_element.getparent()
                    greatgrandparent_element.insert(greatgrandparent_element.index(grandparent_element) + 1, parent_element_html)
                    parent_element = contents_list.xpath('//*[@id="{}"]'.format(component_parent_id))
                parent_element[0].append(element)
            elif len(daos) > 1:
                element = make_noncollapsible_element(component)
                if not parent_element:
                    parent_element_html = make_parent_element(component_parent_id, component.tag)
                    grandparent_element = contents_list.xpath('//*[@href="#{}"]'.format(component_parent_id))[0]
                    greatgrandparent_element = grandparent_element.getparent()
                    greatgrandparent_element.insert(greatgrandparent_element.index(grandparent_element) + 1, parent_element_html)
                    parent_element = contents_list.xpath('//*[@id="{}"]'.format(component_parent_id))
                parent_element[0].append(element)
                for dao in daos:
                    link = dao.attrib["href"].strip()
                    if textclass_link_regex.match(link):
                        link = re.sub(r"(.*?)(" + collection_path + ".*?$)", r"\2", link)
                    element_text = make_title_from_note(dao)
                    subelement = make_linking_element(link, element_text)
                    component_id = component.attrib["id"]
                    if component.tag == "c01":
                        component_id += "_daos"
                    dao_parent = contents_list.xpath('//*[@id="{}"]'.format(component_id))
                    if not dao_parent:
                        parent_element_html = make_parent_element(component_id, component.tag, collapse=False)
                        grandparent_element = contents_list.xpath('//*[@href="#{}"]'.format(component_id))[0]
                        greatgrandparent_element = grandparent_element.getparent()
                        greatgrandparent_element.insert(greatgrandparent_element.index(grandparent_element) + 1, parent_element_html)
                        dao_parent = contents_list.xpath('//*[@id="{}"]'.format(component_id))
                    dao_parent[0].append(subelement)
        else:
            if component.tag != "c01":
                element = make_collapsible_element(component)
                if not parent_element:
                    parent_element_html = make_parent_element(component_parent_id, component.tag)
                    grandparent_element = contents_list.xpath('//*[@href="#{}"]'.format(component_parent_id))[0]
                    greatgrandparent_element = grandparent_element.getparent()
                    greatgrandparent_element.insert(greatgrandparent_element.index(grandparent_element) + 1, parent_element_html)
                    parent_element = contents_list.xpath('//*[@id="{}"]'.format(component_parent_id))
                parent_element[0].append(element)
    return contents_list


def make_series_navigation_list(series_dicts):
    series_navigation_list = etree.Element("ul")
    for i, series_dict in enumerate(series_dicts):
        series_list_item = etree.SubElement(series_navigation_list, "li")
        series_list_item.attrib["class"] = "series-nav-list-item"
        series_link = etree.SubElement(series_list_item, "a")
        series_link.attrib["href"] = "browse.html#series{}".format(i+1)
        series_link.attrib["class"] = "text-muted"
        series_link.text = series_dict["title"]
        series_navigation_list.append(series_list_item)
    return series_navigation_list


def download_ead(DLXSMetadataPrepper, ead_filepath):
    print("Downloading EAD")
    ead = DLXSMetadataPrepper.aspace.export_ead(DLXSMetadataPrepper.resource_id)
    with open(ead_filepath, "wb") as f:
        f.write(ead.content)


def make_sidebar_link(shortname, header_text, note):
    if note:
        list_item = etree.Element("li")
        anchor = etree.SubElement(list_item, "a")
        anchor.attrib["href"] = "index.html#{}".format(shortname)
        anchor.attrib["class"] = "text-muted"
        anchor.text = header_text
        return etree.tostring(list_item)
    else:
        return ""


def make_index_note(shortname, header_text, note):
    if note:
        note_element = etree.Element("div")
        note_element.attrib["id"] = shortname
        header = etree.SubElement(note_element, "h2")
        header.text = header_text
        note_text_element = etree.SubElement(note_element, "p")
        note_text_element.text = note
        return etree.tostring(note_element)
    else:
        return ""


def get_bib_or_simple(r_drive_folder):
    path_to_r_drive_folder = os.path.join("R:/MLibrary Drop", r_drive_folder)
    if os.path.exists(path_to_r_drive_folder):
        ocr_directory = os.path.join(path_to_r_drive_folder, "flat_ocr")
        if os.path.exists(ocr_directory):
            return "simple"
        else:
            return "bib"
    else:
        print "Directory {} not found on R drive".format(r_drive_folder)
        sys.exit()


def make_index_and_browse(DLXSMetadataPrepper, template_dir, redownload_ead=False, dry_run=True):
    collection_dir = DLXSMetadataPrepper.collection_dir
    r_drive_folder = DLXSMetadataPrepper.r_drive_folder
    bib_or_simple = get_bib_or_simple(r_drive_folder)
    header_image = DLXSMetadataPrepper.header_image
    if dry_run:
        header_image = "https://preview.quod.lib.umich.edu" + header_image

    collid = DLXSMetadataPrepper.dlxs_collection.split("/")[-1]
    availability_addendum = DLXSMetadataPrepper.availability_addendum
    if availability_addendum:
        availability_addendum_element = make_availability_addendum(availability_addendum)
    else:
        availability_addendum_element = ""
    access_link = make_sidebar_link("access", "Access Note", DLXSMetadataPrepper.access_note)
    access_note = make_index_note("access", "Access Note", DLXSMetadataPrepper.access_note)
    copyright_link = make_sidebar_link("copyright", "Copyright Notice", DLXSMetadataPrepper.availability_statement)
    copyright_note = make_index_note("copyright", "Copyright Notice", DLXSMetadataPrepper.availability_statement)
    collection_dicts = parse_ead(DLXSMetadataPrepper, redownload_ead)
    collection_info = collection_dicts["collection_info"]
    abstract_element = make_index_note("collection-overview", "Collection Overview", collection_info["abstract"])
    series_dicts = collection_dicts["series_dicts"]
    series_navigation_list = make_series_navigation_list(series_dicts)
    series_cards = make_series_cards(DLXSMetadataPrepper, series_dicts, dry_run)
    browse_contents = collection_dicts["browse_contents"]

    template_dirname = os.path.split(template_dir)[-1]
    collection_browse_dir = os.path.join(collection_dir, template_dirname)
    if os.path.exists(collection_browse_dir):
        for filename_or_dirname in os.listdir(collection_browse_dir):
            file_or_dir = os.path.join(
                collection_browse_dir, filename_or_dirname)
            if os.path.isfile(file_or_dir):
                os.remove(file_or_dir)
            elif os.path.isdir(file_or_dir):
                shutil.rmtree(file_or_dir)

        shutil.rmtree(collection_browse_dir)
    shutil.copytree(template_dir, collection_browse_dir)

    index_template = os.path.join(collection_browse_dir, "index_template.html")
    browse_template = os.path.join(collection_browse_dir, "browse_template.html")
    with open(index_template, "r") as f:
        index_html = f.read() \
            .replace("{{ COLLID }}", collid) \
            .replace("{{ HEADER_IMAGE }}", header_image) \
            .replace("{{ COLLECTION_OVERVIEW }}", abstract_element) \
            .replace("{{ AVAILABILITY_ADDENDUM }}", availability_addendum_element) \
            .replace("{{ ACCESS_NOTE }}", access_note) \
            .replace("{{ ACCESS_LINK }}", access_link) \
            .replace("{{ COPYRIGHT_NOTE }}", copyright_note) \
            .replace("{{ COPYRIGHT_LINK }}", copyright_link) \
            .replace("{{ COLLECTION_TITLE }}", collection_info["title"]) \
            .replace("{{ COLLECTION_PATH }}", DLXSMetadataPrepper.dlxs_collection) \
            .replace("{{ BIB_OR_SIMPLE }}", bib_or_simple) \
            .replace("{{ EAD_ID }}", collection_info["ead_id"]) \
            .replace("{{ SERIES_NAVIGATION_LIST }}", etree.tostring(series_navigation_list, pretty_print=True)) \
            .replace("{{ SERIES_CARDS }}", etree.tostring(series_cards, pretty_print=True))

    with open(browse_template, "r") as f:
        browse_html = f.read() \
            .replace("{{ COLLID }}", collid) \
            .replace("{{ COLLECTION_TITLE }}", collection_info["title"]) \
            .replace("{{ EAD_ID }}", collection_info["ead_id"]) \
            .replace("{{ ACCESS_LINK }}", access_link) \
            .replace("{{ COPYRIGHT_LINK }}", copyright_link) \
            .replace("{{ COLLECTION_PATH }}", DLXSMetadataPrepper.dlxs_collection) \
            .replace("{{ BIB_OR_SIMPLE }}", bib_or_simple) \
            .replace("{{ SERIES_NAVIGATION_LIST }}", etree.tostring(series_navigation_list, pretty_print=True)) \
            .replace("{{ BROWSE_CONTENTS }}", etree.tostring(browse_contents, pretty_print=True))

    collection_dlxs_hierarchy_dir = os.path.join(collection_browse_dir, collid[0], collid)
    os.makedirs(collection_dlxs_hierarchy_dir)

    collection_index_file = os.path.join(collection_dlxs_hierarchy_dir, "index.html")
    collection_browse_file = os.path.join(collection_dlxs_hierarchy_dir, "browse.html")

    with open(collection_index_file, "w") as f:
        f.write(HTMLParser().unescape(index_html))
    with open(collection_browse_file, "w") as f:
        f.write(HTMLParser().unescape(browse_html))

    os.remove(index_template)
    os.remove(browse_template)

    collection_img_dir = os.path.join(collection_dir, "img")
    if os.path.exists(collection_img_dir):
        browse_img_dir = os.path.join(collection_dlxs_hierarchy_dir, "graphics")
        shutil.copytree(collection_img_dir, browse_img_dir)
