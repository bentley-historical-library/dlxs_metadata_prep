from dlxs_helpers import get_dlxs_base_url
import csv
import json
import os


def make_digital_object(dlxs_info, digital_object_note, collection_base_url):
    dlxs_id = dlxs_info["dlxs_id"]
    title = dlxs_info["title"]
    href = "{}{}/1".format(collection_base_url, dlxs_id)
    digital_object = {}
    digital_object["title"] = title
    digital_object["digital_object_id"] = dlxs_id
    digital_object["notes"] = [make_digital_object_note(digital_object_note)]
    digital_object["publish"] = False
    digital_object["file_versions"] = [{"file_uri":href, "xlink_show_attribute":"new","xlink_actuate_attribute":"onRequest"}]
    return digital_object


def make_digital_object_note(note_content):
    note = {}
    note["type"] = "note"
    note["content"] = [note_content]
    note["publish"] = True
    note["jsonmodel_type"] = "note_digital_object"
    return note


def make_digital_object_instance(digital_object_uri):
    instance = {'instance_type':'digital_object', 'digital_object':{'ref':digital_object_uri}}
    return instance


def make_aspace_uri_to_barcodes_dict(aspace_matches_csv, barcodes):
    aspace_uris_to_barcodes = {}
    with open(aspace_matches_csv, "rb") as f:
        reader = csv.DictReader(f)
        for row in reader:
            aspace_uri = row["aspace_uri"].strip()
            barcode = row["identifier"]
            if barcode in barcodes:
                if aspace_uri not in aspace_uris_to_barcodes:
                    aspace_uris_to_barcodes[aspace_uri] = []
                aspace_uris_to_barcodes[aspace_uri].append(barcode)
    return aspace_uris_to_barcodes


def make_dlxs_info_dict(dlxs_metadata_csv):
    dlxs_info = {}
    with open(dlxs_metadata_csv, "rb") as f:
        reader = csv.DictReader(f)
        for row in reader:
            barcode = row["identifier"].strip()
            title = row["title"].strip().encode("utf-8")
            dlxs_info[barcode] = {"dlxs_id":barcode, "title":title}
    return dlxs_info


def create_digital_objects(DLXSMetadataPrepper):
    collection_dir = DLXSMetadataPrepper.collection_dir
    collection_path = DLXSMetadataPrepper.dlxs_collection
    dlxs_base_url = get_dlxs_base_url()
    collection_base_url = dlxs_base_url + collection_path + "/"
    digital_object_post_uri = "/repositories/2/digital_objects"

    aspace = DLXSMetadataPrepper.aspace

    # This includes all barcodes and their corresponding archivesspace archival object URIs
    aspace_matches_csv = os.path.join(collection_dir, "digitization_db_items.csv")

    # This includes metadata for only identifiers which ultimately corresponded to a digitized item
    dlxs_metadata_csv = os.path.join(collection_dir, "dlxs_metadata.csv")

    dlxs_info = make_dlxs_info_dict(dlxs_metadata_csv)
    aspace_uris_to_barcodes = make_aspace_uri_to_barcodes_dict(aspace_matches_csv, dlxs_info.keys())

    for aspace_uri, barcodes in aspace_uris_to_barcodes.items():
        barcodes = sorted(barcodes)
        digital_object_instances = []
        for barcode in barcodes:
            if len(barcodes) == 1:
                digital_object_note = "view item"
            else:
                digital_object_note = "view part {}".format(barcodes.index(barcode)+1)
            digital_object = make_digital_object(dlxs_info[barcode], digital_object_note, collection_base_url)
            digital_object_uri = aspace.session.post(aspace.backend_url + digital_object_post_uri, data=json.dumps(digital_object)).json()["uri"]
            digital_object_instance = make_digital_object_instance(digital_object_uri)
            digital_object_instances.append(digital_object_instance)
        archival_object = aspace.get_aspace_json(aspace_uri)
        if "instances" in archival_object:
            archival_object["instances"].extend(digital_object_instances)
        else:
            archival_object["instances"] = digital_object_instances
        print aspace.post_aspace_json(aspace_uri, archival_object)