import csv
import os
import re


def refresh_metadata(DLXSMetadataPrepper):
    collection_dir = DLXSMetadataPrepper.collection_dir
    collection_path = DLXSMetadataPrepper.dlxs_collection
    resource_id = DLXSMetadataPrepper.resource_id

    aspace = DLXSMetadataPrepper.aspace
    metadata_csv = os.path.join(collection_dir, "dlxs_metadata.csv")
    textclass_link_regex = re.compile(r".*?quod\.lib\.umich\.edu" + collection_path + r".*?$")

    archival_object_uris_to_identifiers = {}
    print "Getting a list of children with instances for resource {}...".format(resource_id)
    resource_children_with_instances = aspace.get_resource_children_with_instances(resource_id)
    for archival_object_uri in resource_children_with_instances:
        print "Checking {} for digital object instances matching {}".format(archival_object_uri, collection_path)
        instance_uris = aspace.find_instance_uris(archival_object_uri)
        digital_object_uris = [instance_uri for instance_uri in instance_uris if "digital_object" in instance_uri]
        for digital_object_uri in digital_object_uris:
            digital_object = aspace.get_aspace_json(digital_object_uri)
            file_uri = digital_object["file_versions"][0]["file_uri"]
            if textclass_link_regex.match(file_uri):
                identifier = re.findall(collection_path + r"/([A-Za-z0-9\.]+)", file_uri)[0]
                if archival_object_uri not in archival_object_uris_to_identifiers:
                    archival_object_uris_to_identifiers[archival_object_uri] = []
                archival_object_uris_to_identifiers[archival_object_uri].append(identifier)

    data = []
    for archival_object_uri, identifiers in archival_object_uris_to_identifiers.items():
        print "Gathering metadata for {}".format(archival_object_uri)
        aspace_json = aspace.get_aspace_json(archival_object_uri)
        date = aspace.format_dates(aspace_json)
        general_note = aspace.find_note_by_type(aspace_json, "odd").encode("utf-8")
        abstract = aspace.find_note_by_type(aspace_json, "abstract").encode("utf-8")
        display_string = aspace.make_display_string(aspace_json, add_parent_title=False).encode("utf-8")
        hierarchy = aspace.build_hierarchy(aspace_json).encode("utf-8")
        for identifier in identifiers:
            item_metadata = {}
            item_metadata["identifier"] = identifier
            item_metadata["date"] = date
            item_metadata["general_note"] = general_note
            item_metadata["abstract"] = abstract
            item_metadata["hierarchy"] = hierarchy
            if len(identifiers) > 1:
                total_count = len(identifiers)
                current_count = identifiers.index(identifier) + 1
                suffix = "({} of {})".format(current_count, total_count)
                item_metadata["title"] = display_string + " " + suffix
            else:
                item_metadata["title"] = display_string
            data.append(item_metadata)

    fieldnames = ["identifier", "title", "date", "hierarchy", "general_note", "abstract"]
    with open(metadata_csv, "wb") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)