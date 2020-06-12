import csv
import fnmatch
from lxml import etree
import os
import sys

from dlxs_helpers import *

allowed_header_types = ["standard", "civilwar", "polar_bear"]


def UnicodeDictReader(utf8_data, **kwargs):
    csv_reader = csv.DictReader(utf8_data, **kwargs)
    for row in csv_reader:
        yield {key: unicode(value, 'utf-8').replace(u"\u000b", "\n") for key, value in row.iteritems()}


def has_ocr(r_drive_folder):
    path_to_r_drive_folder = os.path.join("R:/MLibrary Drop", r_drive_folder)
    if os.path.exists(path_to_r_drive_folder):
        ocr_directory = os.path.join(path_to_r_drive_folder, "flat_ocr")
        if os.path.exists(ocr_directory):
            return True
        else:
            return False
    else:
        print "Directory {} not found on R drive".format(r_drive_folder)
        sys.exit()


def make_extent_dict(collection_dir, collection_id, r_drive_folder):
    identifiers_to_extents = {}
    path_to_r_drive_folder = os.path.join("R:/MLibrary Drop", r_drive_folder)
    extent_file_dir = os.path.join(collection_dir, "extent_tables")
    header_dir = os.path.join(collection_dir, "headers")
    if os.path.exists(path_to_r_drive_folder):
        contones_dir = os.path.join(path_to_r_drive_folder, "contones")
        image_base_dir = os.path.join(contones_dir, collection_id)
        box_numbers = os.listdir(image_base_dir)
        for box_number in box_numbers:
            box_dir = os.path.join(image_base_dir, box_number)
            folders = os.listdir(box_dir)
            for folder in folders:
                folder_dir = os.path.join(box_dir, folder)
                pages_dir = os.path.join(folder_dir, "pages")
                if os.path.exists(pages_dir):
                    folder_dir = pages_dir
                identifier = "{}.{}.{}".format(collection_id, box_number, folder)
                extent = str(len(fnmatch.filter(os.listdir(folder_dir), "*.tif"))) + " continuous tone images"
                identifiers_to_extents[identifier] = extent
        return identifiers_to_extents
    elif os.path.exists(extent_file_dir):
        extent_files = [filename for filename in os.listdir(extent_file_dir) if filename.endswith(".xml")]
        if extent_files:
            extent_filepath = os.path.join(extent_file_dir, extent_files[0])
            return parse_extent_file(extent_filepath)
        else:
            print "No existing extent file found in {}".format(extent_file_dir)
            sys.exit()
    elif os.path.exists(header_dir):
        for filename in os.listdir(header_dir):
            header = etree.parse(os.path.join(header_dir, filename))
            extent = header.xpath("//EXTENT")[0].text.strip()
            identifiers_to_extents[filename] = extent
        return identifiers_to_extents
    else:
        return {}


def make_dlxs_headers(DLXSMetadataPrepper, header_type="standard"):
    if header_type not in allowed_header_types:
        print "header_type {} is not one of {}".format(header_type, allowed_header_types)
        sys.exit()
    availability_addendum = DLXSMetadataPrepper.availability_addendum
    availability_statement = DLXSMetadataPrepper.availability_statement
    collection_dir = DLXSMetadataPrepper.collection_dir
    collection_id = DLXSMetadataPrepper.collection_id
    r_drive_folder = DLXSMetadataPrepper.r_drive_folder
    resource_id = DLXSMetadataPrepper.resource_id

    dlxs_metadata_csv = os.path.join(collection_dir, "dlxs_metadata.csv")
    identifiers_to_extents = make_extent_dict(collection_dir, collection_id, r_drive_folder)
    header_dir = os.path.join(collection_dir, "headers")
    if not os.path.exists(header_dir):
        os.makedirs(header_dir)
    for filename in os.listdir(header_dir):
        os.remove(os.path.join(header_dir, filename))

    aspace = DLXSMetadataPrepper.aspace
    resource_json = aspace.get_resource(resource_id)

    collection_metadata = {}
    collection_metadata["title"] = aspace.make_display_string(resource_json)
    collection_metadata["abstract"] = aspace.find_note_by_type(resource_json, "abstract")
    collection_metadata["creator"] = aspace.get_resource_creator(resource_json)
    collection_metadata["agents"] = aspace.get_linked_agents(resource_json)
    collection_metadata["subjects"] = aspace.get_linked_subjects(resource_json, ignore_types=["genre_form"])
    collection_metadata["rights_statement"] = availability_statement
    collection_metadata["availability_addendum"] = availability_addendum
    collection_metadata["has_ocr"] = has_ocr(r_drive_folder)

    with open(dlxs_metadata_csv, "rb") as f:
        reader = UnicodeDictReader(f)
        for row in reader:
            item_metadata = {}
            identifier = row["identifier"].strip()
            item_metadata["identifier"] = identifier
            header_filename = identifier + ".xml"
            collection_id, box_number, folder_number = identifier.split(".")
            item_metadata["title"] = row["title"].strip()
            item_metadata["hierarchy"] = row["hierarchy"].strip()
            item_metadata["abstract"] = row["abstract"]
            item_metadata["general_note"] = row["general_note"]
            item_metadata["scopecontent"] = row["scopecontent"]
            item_metadata["date"] = row["date"]		
            item_metadata["extent_statement"] = identifiers_to_extents.get(identifier, "")
            if header_type == "standard":
                header = make_header(collection_metadata, item_metadata)
            elif header_type == "polar_bear":
                header = make_polar_bear_header(collection_metadata, item_metadata)
            elif header_type == "civilwar":
                header = make_civilwar_header(collection_metadata, item_metadata)
            else:
                print "function not defined for header_type {}".format(header_type)
                sys.exit()

            with open(os.path.join(header_dir, header_filename), "w") as f:
                f.write(etree.tostring(header, encoding="utf-8", pretty_print=True))
