from bhlaspaceapiclient import ASpaceClient
import ConfigParser
import os
import sys

from scripts.dlxs_helpers import default_availability_statement
from scripts.dlxs_helpers import blydenburgh_availability_statement
from scripts.dlxs_helpers import civilwar_availability_statement
from scripts.edit_digital_object_uris import edit_digital_object_uris
from scripts.export_ead import export_ead
from scripts.export_identifiers_from_digitization_database import export_identifiers
from scripts.get_aspace_metadata import get_aspace_metadata
from scripts.make_index_and_browse import make_index_and_browse
from scripts.make_dlxs_headers import make_dlxs_headers
from scripts.publish_digital_objects import publish_digital_objects
from scripts.refresh_metadata import refresh_metadata
from scripts.update_aspace import create_digital_objects

__all__ = ["DLXSMetadataPrep"]


class DLXSMetadataPrep(object):

    def __init__(self, collection_name=False, collection_id=False, aspace_instance=None):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        collections_dir = os.path.join(base_dir, "collections")
        self.ead_dir = os.path.join(base_dir, "eads")
        self.templates_dir = os.path.join(base_dir, "templates")
        self.config_file = os.path.join(base_dir, "config.cfg")
        configuration = self._load_config(collection_name, collection_id)
        self.access_note = self._normalize_access_note(configuration.get("access_note", False))
        self.header_image = configuration.get("header_image", "img/header.PNG")
        self.availability_statement = self._normalize_availability_statement(configuration["availability_statement"])
        self.availability_addendum = self._normalize_availability_addendum(configuration["availability_addendum"])
        self.collection_dir = os.path.join(collections_dir, self.collection_name)
        self.collection_id = configuration["collection_id"]
        self.dlxs_collection = configuration["dlxs_collection"]
        self.r_drive_folder = configuration["r_drive_folder"]
        self.resource_id = configuration["resource_id"]
        self.aspace = ASpaceClient(instance_name=aspace_instance)

    def _load_config(self, collection_name, collection_id):
        config = ConfigParser.RawConfigParser()
        config.read(self.config_file)
        collections = config.sections()
        if len(collections) == 0:
            print "No collections configured. Configure a collection? (y/n)"
            configure = raw_input(": ")
            if configure.lower().strip() in ["y", "yes"]:
                return self._add_collection(config)
            else:
                sys.exit()
        elif collection_name and collection_name in collections:
            return self._load_collection(config, collection_name)
        elif collection_id:
            collection_ids_to_names = {config.get(collection, "collection_id"):collection for collection in collections}
            if collection_id in collection_ids_to_names:
                collection_name = collection_ids_to_names[collection_id]
                return self._load_collection(config, collection_name)
            else:
                print "Collection ID {} not found".format(collection_id)
        else:
            collection_mapping = {}
            collection_number = 0
            print "*** CONFIGURED COLLECTIONS ***"
            for collection in collections:
                collection_number += 1
                collection_mapping[str(collection_number)] = collection
                print "{} - {} [{}]".format(collection_number, collection, config.get(collection, "collection_id"))
            print "A - Add Collection"
            option = raw_input("Select an option: ")
            if option.strip() in collection_mapping.keys():
                collection_name = collection_mapping[option]
                return self._load_collection(config, collection_name)
            elif option.lower().strip() == "a":
                return self._add_collection(config)
            else:
                sys.exit()

    def _save_config(self, config):
        with open(self.config_file, "wb") as f:
            config.write(f)

    def _add_collection(self, config):
        collection_name = raw_input("Collection name: ")
        has_availability_statement = raw_input("Does this collection have its own availability statement? (y/n): ")
        if has_availability_statement.lower().strip() in ["y", "yes"]:
            availability_statement = raw_input("Enter the availability statement: ")
        else:
            availability_statement = "default"
        has_availability_addendum = raw_input("Does this collection require an availability addendum? (y/n): ")
        if has_availability_addendum in ["y", "yes"]:
            availability_addendum = raw_input("Enter the availability addendum: ")
        else:
            availability_addendum = "false"
        collection_id = raw_input("Collection ID: ")
        dlxs_collection = raw_input("DLXS Collection (e.g., /a/angell): ")
        r_drive_folder = raw_input("R Drive Folder (e.g., 851644-Angell): ")
        resource_id = raw_input("ArchivesSpace Resource ID: ")
        config.add_section(collection_name)
        config.set(collection_name, "availability_statement", availability_statement)
        config.set(collection_name, "availability_addendum", availability_addendum)
        config.set(collection_name, "collection_id", collection_id)
        config.set(collection_name, "dlxs_collection", dlxs_collection)
        config.set(collection_name, "r_drive_folder", r_drive_folder)
        config.set(collection_name, "resource_id", resource_id)
        self._save_config(config)
        return self._load_collection(config, collection_name)

    def _load_collection(self, config, collection_name):
        self.collection_name = collection_name
        return {key: value for (key, value) in config.items(collection_name)}

    def _normalize_access_note(self, access_note):
        if not access_note or access_note.lower().strip() == "false":
            access_note = False
        return access_note

    def _normalize_availability_addendum(self, availability_addendum):
        if availability_addendum.lower().strip() == "false":
            availability_addendum = False
        return availability_addendum

    def _normalize_availability_statement(self, availability_statement):
        if availability_statement.lower().strip() == "default":
            availability_statement = default_availability_statement()
        elif availability_statement.lower().strip() == "civilwar":
            availability_statement = civilwar_availability_statement()
        elif availability_statement.lower().strip() == "blydenburgh":
            availability_statement = blydenburgh_availability_statement()
        return availability_statement

    def create_digital_objects(self):
        """ Create Digital Objects for new Text Class collections """
        create_digital_objects(self)

    def edit_digital_object_uris(self):
        """ For existing collections, edit digital object URIs to end in /1 """
        edit_digital_object_uris(self)

    def export_ead(self):
        """ Export an EAD for the collection """
        export_ead(self)

    def export_identifiers(self):
        """ Export identifiers and ASpace URIs for digitized items """
        export_identifiers(self)

    def get_aspace_metadata(self):
        """ For new collections, get metadata from ArchivesSpace, keying off of the aspace_uri from the digitization database """
        get_aspace_metadata(self)

    def list_collections(self):
        config = ConfigParser.RawConfigParser()
        config.read(self.config_file)
        collections = config.sections()
        for collection in collections:
            print collection

    def make_index_and_browse(self, redownload_ead=False, dry_run=False):
        """ Make an index and a browse page """
        template_dir = os.path.join(self.templates_dir, "index_and_browse")
        make_index_and_browse(self, template_dir=template_dir, redownload_ead=redownload_ead, dry_run=dry_run)

    def make_dlxs_headers(self):
        """ Make DLXS headers using the dlxs_metadata.csv for the collection """
        make_dlxs_headers(self)

    def make_civilwar_headers(self):
        """ Make headers for the bhlcivilwar collection """
        make_dlxs_headers(self, header_type="civilwar")

    def make_polar_bear_headers(self):
        """ Make polarbear headers using the dlxs_metadata.csv for the collection """
        make_dlxs_headers(self, header_type="polar_bear")

    def publish_digital_objects(self):
        """ Publish Digital Objects in ArchivesSpace once the collection goes online """
        publish_digital_objects(self)

    def refresh_metadata(self):
        """ For existing collections, download metadata for DLXS from ArchivesSpace
            Requires that the ArchivesSpace Resource already includes digital objects """
        refresh_metadata(self)