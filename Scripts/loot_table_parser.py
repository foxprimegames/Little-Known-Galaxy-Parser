import os
import re
import yaml
import json

def load_guid_mapping(guid_mapping_path):
    """
    Load the GUID to item mapping from a JSON file.
    """
    with open(guid_mapping_path, 'r') as file:
        guid_mapping = json.load(file)
    return guid_mapping

def preprocess_yaml_content(content):
    """
    Remove custom Unity tags from YAML content.
    """
    return re.sub(r'!u![\d]+ &[\d]+', '', content)

def to_sentence_case(text):
    """
    Convert a string to sentence case.
    """
    return text.capitalize()

def split_loot_tables_by_criteria(loot_table_name):
    """
    Determine the output file based on the loot table name.
    """
    if loot_table_name.startswith("Enemy_"):
        return "Output/Drops/enemy_loot_table.txt"
    elif "stone" in loot_table_name.lower():
        return "Output/Drops/stone_loot_table.txt"
    elif "microbe" in loot_table_name.lower():
        return "Output/Drops/microbe_loot_table.txt"
    elif "grass" in loot_table_name.lower() or "mixedseeds" in loot_table_name.lower():
        return "Output/Drops/grass_loot_table.txt"
    elif "ship" in loot_table_name.lower():
        return "Output/Drops/ship_loot_table.txt"
    elif "discoveritems" in loot_table_name.lower():
        return "Output/Drops/discovery_loot_table.txt"
    elif "friendcard" in loot_table_name.lower():
        return "Output/Drops/friend_card_loot_table.txt"
    else:
        return "Output/Drops/other_loot_table.txt"

def parse_loot_tables(input_directory, guid_mapping, loot_table_list_path, debug_output_path):
    """
    Parse loot tables from asset files and write the formatted loot tables to output files based on criteria.
    """
    with open(loot_table_list_path, 'r') as file:
        loot_table_files = file.read().splitlines()

    with open(debug_output_path, 'w') as debug_log:
        for filename in loot_table_files:
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r') as file:
                raw_content = file.read()
                clean_content = preprocess_yaml_content(raw_content)
                data = yaml.safe_load(clean_content)

            loot_table_name = data.get('MonoBehaviour', {}).get('m_Name', 'unknown_loot_table')
            loot_table_info, contains_loot_list = extract_loot_table_info(data, loot_table_name, guid_mapping)
            
            output_file_path = split_loot_tables_by_criteria(loot_table_name)
            with open(output_file_path, 'a') as output_file:
                header = f"<!-- \n#{loot_table_name} -->\n"
                output_file.write(header)
                for item in loot_table_info:
                    output_file.write(item + '\n')
            
            debug_log.write(f"Processed loot table: {loot_table_name} in file: {filename}\n")

def extract_loot_table_info(data, loot_table_name, guid_mapping):
    """
    Extract loot table information from the YAML data.
    """
    loot_table_info = []
    contains_loot_list = False
    loot_table_entries = data.get('MonoBehaviour', {}).get('lootTable', [])
    
    for entry in loot_table_entries:
        loot = entry.get('loot', 0)
        item_guid = entry.get('itemToDrop', {}).get('guid', '0')
        percent_chance = entry.get('percentChance', 0) / 100.0
        min_num = entry.get('amtToGive', {}).get('minimumNum', 0)
        max_num = entry.get('amtToGive', {}).get('maxiumNum', 0)
        
        if loot == 0 and item_guid == '0':
            item_name = "Nothing"
        elif loot == 1:
            item_name = "loot_table"
            contains_loot_list = True
        else:
            item_info = next((item for item in guid_mapping if item['guid'] == item_guid), {})
            item_name = to_sentence_case(item_info.get('name', 'unknown_item'))
        
        loot_table_info.append(f"{{{{Loot table|{item_name}|{percent_chance:.2f}|{min_num}|{max_num}|{loot_table_name}}}}}")
    
    return loot_table_info, contains_loot_list

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_mapping_path = 'Output/guid_lookup.json'
loot_table_list_path = 'Output/Drops/loot_table_list.txt'
debug_output_path = '.hidden/debug_output/loot_table_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Load GUID mapping
guid_mapping = load_guid_mapping(guid_mapping_path)

# Parse loot tables
parse_loot_tables(input_directory, guid_mapping, loot_table_list_path, debug_output_path)

print(f"Debug information has been written to {debug_output_path}")
