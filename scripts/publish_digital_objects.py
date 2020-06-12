from lxml import etree


def publish_digital_objects(DLXSMetadataPrepper):
    resource_id = DLXSMetadataPrepper.resource_id
    collection_path = DLXSMetadataPrepper.dlxs_collection

    aspace = DLXSMetadataPrepper.aspace
    ead = aspace.export_ead(resource_id, digitization_ead=True, include_unpublished=True)

    tree = etree.fromstring(ead.content)

    aspace_uris = []
    hrefs_to_publish = []
    daos = tree.xpath("//dao")
    print "Parsing EAD"
    for dao in daos:
        href = dao.attrib["href"]
        if collection_path in href:
            hrefs_to_publish.append(href)
            component = dao.getparent().getparent()
            aspace_uri = component.attrib["altrender"]
            if aspace_uri not in aspace_uris:
                aspace_uris.append(aspace_uri)

    digital_object_uris = []
    for aspace_uri in aspace_uris:
        print "Gathering Digital Object URIs for {}".format(aspace_uri)
        archival_object = aspace.get_aspace_json(aspace_uri)
        instances = archival_object["instances"]
        for instance in instances:
            if instance["instance_type"] == "digital_object":
                digital_object_uri = instance["digital_object"]["ref"]
                if digital_object_uri not in digital_object_uris:
                    digital_object_uris.append(digital_object_uri)

    for digital_object_uri in digital_object_uris:
        print "Updating {}".format(digital_object_uri)
        digital_object = aspace.get_aspace_json(digital_object_uri)
        file_uri = digital_object["file_versions"][0]["file_uri"]
        if file_uri in hrefs_to_publish:
            digital_object["publish"] = True
            print aspace.post_aspace_json(digital_object_uri, digital_object)