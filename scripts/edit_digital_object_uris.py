from lxml import etree


def edit_digital_object_uris(DLXSMetadataPrepper):
    dlxs_collection = DLXSMetadataPrepper.dlxs_collection
    resource_id = DLXSMetadataPrepper.resource_id
    aspace = DLXSMetadataPrepper.aspace

    print "Downloading EAD..."
    ead = aspace.export_ead(resource_id, include_unpublished=True, digitization_ead=True)
    tree = etree.fromstring(ead.content)
    daos = tree.xpath("//dao")
    archival_object_uris = []
    print "Parsing daos"
    for dao in daos:
        link = dao.attrib["href"]
        if dlxs_collection in link:
            component = dao.getparent().getparent()
            archival_object_uri = component.attrib["altrender"]
            if archival_object_uri not in archival_object_uris:
                archival_object_uris.append(archival_object_uri)

    print "Updating file_uris"
    for archival_object_uri in archival_object_uris:
        archival_object = aspace.get_aspace_json(archival_object_uri)
        instances = archival_object["instances"]
        digital_object_instances = [instance for instance in instances if instance["instance_type"] == "digital_object"]
        for digital_object_instance in digital_object_instances:
            digital_object_uri = digital_object_instance["digital_object"]["ref"]
            digital_object = aspace.get_aspace_json(digital_object_uri)
            link = digital_object["file_versions"][0]["file_uri"]
            if dlxs_collection in link and not link.endswith("/1"):
                link += "/1"
                digital_object["file_versions"][0]["file_uri"] = link
                print aspace.post_aspace_json(digital_object_uri, digital_object)