import json
import os
import re
import yaml
from Utilities import guid_utils
from Utilities.unity_yaml_loader import preprocess_yaml_content

def log_debug(message):
    with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

def to_sentence_case(text):
    """
    Convert a string to sentence case.
    """
    return text.capitalize()

def get_loot_table_name(item_guid, input_directory, guid_mapping):
    """
    Get the name of the loot table from its GUID.
    """
    item_info = next((item for item in guid_mapping if item['guid'] == item_guid), {})
    asset_filename = item_info.get('filename', '')
    if not asset_filename:
        return 'unknown_loot_table'

    asset_filepath = os.path.join(input_directory, f"{asset_filename}.asset")
    if not os.path.exists(asset_filepath):
        return 'unknown_loot_table'

    with open(asset_filepath, 'r') as asset_file:
        raw_content = asset_file.read()
        clean_content = preprocess_yaml_content(raw_content)
        data = yaml.safe_load(clean_content)
        return data.get('MonoBehaviour', {}).get('m_Name', 'unknown_loot_table')

def parse_loot_lists(input_directory, guid_mapping, loot_table_list_path, list_output_file_path, debug_output_path):
    """
    Parse loot lists from asset files and write the formatted loot lists to an output file.
    """
    with open(loot_table_list_path, 'r') as file:
        loot_table_files = file.read().splitlines()

    with open(list_output_file_path, 'w') as list_output_file, open(debug_output_path, 'w') as debug_log:
        for filename in loot_table_files:
            try:
                filepath = os.path.join(input_directory, filename)
                with open(filepath, 'r') as file:
                    raw_content = file.read()
                    clean_content = preprocess_yaml_content(raw_content)
                    data = yaml.safe_load(clean_content)
                
                loot_table_name = data.get('MonoBehaviour', {}).get('m_Name', 'unknown_loot_table')
                loot_table_info, contains_loot_list = extract_loot_table_info(data, loot_table_name, input_directory, guid_mapping)
                
                if contains_loot_list:
                    list_output_file.write(f"<!-- \n#{loot_table_name} -->\n")
                    list_output_file.write(f"{{{{TYPE drops|lootlist={loot_table_name}|name=\n")
                    for item in loot_table_info:
                        list_output_file.write(item + '\n')
                    list_output_file.write("}}\n")
                
                debug_log.write(f"Processed loot list: {loot_table_name} in file: {filename}\n")
            except Exception as e:
                log_debug(f"Error processing file {filename}: {str(e)}")

def extract_loot_table_info(data, loot_table_name, input_directory, guid_mapping):
    """
    Extract loot table information from the YAML data.
    """
    loot_table_info = []
    contains_loot_list = False
    loot_table_entries = data.get('MonoBehaviour', {}).get('lootTable', [])
    item_count = 1
    table_count = 1
    
    for entry in loot_table_entries:
        loot = entry.get('loot', 0)
        if loot == 1:
            nested_loot_table_name = get_loot_table_name(entry['lootTable']['guid'], input_directory, guid_mapping)
            loot_table_info.append(f"|table{table_count}={nested_loot_table_name}\n   |table{table_count}chance={entry.get('percentChance', 0) / 100.0:.2f}\n   |table{table_count}min={entry.get('amtToGive', {}).get('minimumNum', 0)}\n   |table{table_count}max={entry.get('amtToGive', {}).get('maxiumNum', 0)}")
            table_count += 1
            contains_loot_list = True
        else:
            item_guid = entry.get('itemToDrop', {}).get('guid', '0')
            if item_guid == '0':
                item_name = "Nothing"
            else:
                item_info = next((item for item in guid_mapping if item['guid'] == item_guid), {})
                item_name = to_sentence_case(item_info.get('name', 'unknown_item'))
            loot_table_info.append(f"|item{item_count}={item_name}\n   |item{item_count}chance={entry.get('percentChance', 0) / 100.0:.2f}\n   |item{item_count}min={entry.get('amtToGive', {}).get('minimumNum', 0)}\n   |item{item_count}max={entry.get('amtToGive', {}).get('maxiumNum', 0)}")
            item_count += 1
    
    return loot_table_info, contains_loot_list

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_mapping_path = 'Output/guid_lookup.json'
loot_table_list_path = 'Output/Drops/loot_table_list.txt'
list_output_file_path = 'Output/Drops/loot_list.txt'
debug_output_path = '.hidden/debug_output/loot_table_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(list_output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

try:
    # Load GUID mapping
    guid_mapping = guid_utils.load_guid_lookup(guid_mapping_path)

    # Parse loot lists
    parse_loot_lists(input_directory, guid_mapping, loot_table_list_path, list_output_file_path, debug_output_path)

    # Print the required messages to the terminal
    print(f"Parsed loot lists have been written to '{list_output_file_path}'")
except Exception as e:
    log_debug(f'An error occurred: {str(e)}')
    print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")
