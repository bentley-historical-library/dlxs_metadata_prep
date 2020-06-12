# DLXS Metadata Prepper
Helper scripts for preparing XML headers and HTML index and browse pages for DLXS Text Class collections for the Bentley Historical Library.

Disclaimer: These scripts evolved over several years of doing this and were never properly documented or refactored to make them easier to understand, use, or update. This would probably best be thought of as a reference source for what DLXS headers and index and browse pages should look like as the result of some other process.

## Installation

- Clone this repository
- `cd dlxs_metadata_prep`
- `pip install -r requirements.txt`

## Example usage:
First, create a `config.cfg` file in this repository's root directory. In the `config.cfg` file, add a section for each collection like so:

```
[angell]
availability_statement = default # Can be used to configure collection specific "Copyright Notice"/"Rights/Permissions" statements. If default, pulls from `scripts.dlxs_headers.default_availability_statement`
availability_addendum = false # Only used for one or two collections to add some additional disclaimers to the availability_statement
collection_id = 851644
dlxs_collection = /a/angell
r_drive_folder = 851644-Angell # Directory name for the folder in R:\MLibrary Drop
resource_id = 117 # ArchivesSpace Resource ID
header_image = https://quod.lib.umich.edu/cgi/t/text/api/image/angell:851644.0015.001:00000001/900,1900,3801,1267/full/0/default.jpg # Pre-defined header image formatted using the DLXS IIIF image API
```

There should also be a `collections` directory within this repository's root directory that contains a subdirectory for each configured collection, e.g.:
```
dlxs_metadata_prep
    \ collections
        \ angell
```

Once configured, the DLXS Metadata Prepper can be used like so:

```python
from DLXSMetadataPrep import DLXSMetadataPrep

# Instantiate the DLXSMetadataPrep object. Passing the collection_name pulls in information for the collection from config.cfg
metadata_prepper = DLXSMetadataPrep(collection_name="angell") 

# Export barcodes and ASpace URIs from the digitization database. Saved to a digitization_db_items.csv file in the collection directory
metadata_prepper.export_identifiers() 

# Export metadata from ArchivesSpace using the ASpace URIs from digitization_db_items.csv. Saved to a dlxs_metadata.csv file in the collection directory
metadata_prepper.get_aspace_metadata() 

# Construct DLXS XML headers using the dlxs_metadata.csv file. Headers are saved to a headers subdirectory of the collection directory
metadata_prepper.make_dlxs_headers() 

# Create ArchivesSpace digital objects for each item in the DLXS collection and associate them with archival objects. These are unpublished at first (since this all happens before the collection has been launched). They need to be published later on using metadata_prepper.publish_digital_objects()
metadata_prepper.create_digital_objects() 

# Export an EAD from ArchivesSpace and create an index.html and browse.html page for the collection using the templates found in templates\index_and_browse. The pages are saved to an index_and_browse directory in the collection directory
metadata_prepper.make_index_and_browse() 
```