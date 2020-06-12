import csv
import os


def add_counts_to_titles(items_metadata, parents_to_titles_and_barcodes):
    for item_metadata in items_metadata:
        barcode = item_metadata["identifier"]
        hierarchy = item_metadata["hierarchy"]
        parent_title = hierarchy.split(" > ")[-1]
        parent_titles = parents_to_titles_and_barcodes[parent_title]
        title = item_metadata["title"]
        if len(parent_titles[title]) > 1:
            title_barcodes = sorted(parent_titles[title])
            current_count = title_barcodes.index(barcode) + 1
            total_count = len(title_barcodes)
            suffix = "({} of {})".format(current_count, total_count)
            item_metadata["title"] = "{} {}".format(title, suffix)

    return items_metadata


def get_aspace_metadata(DLXSMetadataPrepper):
    collection_dir = DLXSMetadataPrepper.collection_dir
    digitization_db_file = os.path.join(collection_dir, "digitization_db_items.csv")
    dlxs_metadata_file = os.path.join(collection_dir, "dlxs_metadata.csv")

    aspace = DLXSMetadataPrepper.aspace

    barcodes_to_ids = {}
    with open(digitization_db_file, "rb") as f:
        reader = csv.DictReader(f)
        for row in reader:
            barcode = row["identifier"].strip()
            aspace_uri = row["aspace_uri"].strip()
            barcodes_to_ids[barcode] = aspace_uri

    items_metadata = []
    parents_to_titles_and_barcodes = {}
    for barcode in sorted(barcodes_to_ids.keys()):
        aspace_uri = barcodes_to_ids[barcode]
        print "Gathering metadata for {}".format(barcode)
        aspace_json = aspace.get_aspace_json(aspace_uri)
        item_metadata = {}
        item_metadata["date"] = aspace.format_dates(aspace_json)
        item_metadata["general_note"] = aspace.find_note_by_type(aspace_json, "odd")
        item_metadata["abstract"] = aspace.find_note_by_type(aspace_json, "abstract")
        item_metadata["scopecontent"] = aspace.find_note_by_type(aspace_json, "scopecontent")
        display_string = aspace.make_display_string(aspace_json, add_parent_title=False)
        item_metadata["title"] = display_string
        if aspace_json.get("parent"):
            hierarchy = aspace.build_hierarchy(aspace_json)
        else:
            hierarchy = display_string
        item_metadata["hierarchy"] = hierarchy
        parent_title = hierarchy.split(" > ")[-1]
        if parent_title not in parents_to_titles_and_barcodes:
            parents_to_titles_and_barcodes[parent_title] = {}
        if display_string not in parents_to_titles_and_barcodes[parent_title]:
            parents_to_titles_and_barcodes[parent_title][display_string] = []
        parents_to_titles_and_barcodes[parent_title][display_string].append(barcode)

        item_metadata["identifier"] = barcode
        items_metadata.append(item_metadata)

    data = add_counts_to_titles(items_metadata, parents_to_titles_and_barcodes)

    fieldnames = ["identifier", "title", "date", "hierarchy", "general_note", "abstract", "scopecontent"]
    with open(dlxs_metadata_file, "wb") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)