import os


def export_ead(DLXSMetadataPrepper):
    ead_dir = DLXSMetadataPrepper.ead_dir
    resource_id = DLXSMetadataPrepper.resource_id

    aspace = DLXSMetadataPrepper.aspace

    metadata = aspace.get_export_metadata(resource_id)
    ead = aspace.export_ead(resource_id)
    ead_filename = metadata["filename"]
    ead_filepath = os.path.join(ead_dir, ead_filename)
    with open(ead_filepath, "wb") as f:
        f.write(ead.content)