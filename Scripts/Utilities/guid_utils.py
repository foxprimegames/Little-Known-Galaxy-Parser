# guid_utils.py

import json

def load_guid_lookup(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def create_mappings(lookup_data):
    guid_to_filename = {}
    guid_to_save_id = {}
    guid_to_name = {}
    save_id_to_filename = {}
    save_id_to_name = {}
    filename_to_name = {}
    filename_to_guid = {}

    for entry in lookup_data:
        guid = entry.get('guid')
        filename = entry.get('filename')
        save_id = entry.get('save_id')
        name = entry.get('name', 'Unknown')

        if guid:
            guid_to_filename[guid] = filename
            guid_to_save_id[guid] = save_id
            guid_to_name[guid] = name
        
        if save_id:
            save_id_to_filename[save_id] = filename
            save_id_to_name[save_id] = name

        if filename:
            filename_to_name[filename] = name
            filename_to_guid[filename] = guid

    return {
        'guid_to_filename': guid_to_filename,
        'guid_to_save_id': guid_to_save_id,
        'guid_to_name': guid_to_name,
        'save_id_to_filename': save_id_to_filename,
        'save_id_to_name': save_id_to_name,
        'filename_to_name': filename_to_name,
        'filename_to_guid': filename_to_guid,
    }

# Existing functions for getting information
def get_name_from_guid(guid, mappings):
    return mappings['guid_to_name'].get(guid, 'Unknown')

def get_filename_from_guid(guid, mappings):
    return mappings['guid_to_filename'].get(guid, 'Unknown')

def get_save_id_from_guid(guid, mappings):
    return mappings['guid_to_save_id'].get(guid, 'Unknown')

def get_name_from_save_id(save_id, mappings):
    return mappings['save_id_to_name'].get(save_id, 'Unknown')

def get_filename_from_save_id(save_id, mappings):
    return mappings['save_id_to_filename'].get(save_id, 'Unknown')

def get_name_from_filename(filename, mappings):
    return mappings['filename_to_name'].get(filename, 'Unknown')

def get_guid_from_filename(filename, mappings):
    return mappings['filename_to_guid'].get(filename, 'Unknown')
