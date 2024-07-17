import os
import re
import yaml
import json
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
        
        loot_table_info.append({
            'name': item_name,
            'percentChance': percent_chance,
            'min': min_num,
            'max': max_num,
            'is_loot_table': loot == 1
        })
    
    return loot_table_info, contains_loot_list

def select_output_file(loot_table_name, output_files):
    """
    Select the appropriate output file based on the loot table name.
    """
    if loot_table_name.startswith("Enemy_"):
        return output_files['enemy']
    elif "stone" in loot_table_name.lower():
        return output_files['stone']
    elif "microbe" in loot_table_name.lower():
        return output_files['microbe']
    elif "grass" in loot_table_name.lower() or "mixedseeds" in loot_table_name.lower():
        return output_files['grass']
    elif "ship" in loot_table_name.lower():
        return output_files['ship']
    elif "discoveritems" in loot_table_name.lower():
        return output_files['discovery']
    elif "friendcard" in loot_table_name.lower():
        return output_files['friend_card']
    else:
        return output_files['other']

def parse_loot_tables(input_directory, guid_mapping, loot_table_list_path, output_files, debug_output_path):
    """
    Parse loot tables from asset files and write the formatted loot tables to various output files.
    """
    with open(loot_table_list_path, 'r') as file:
        loot_table_files = file.read().splitlines()

    with open(debug_output_path, 'w') as debug_log:
        for filename in loot_table_files:
            try:
                filepath = os.path.join(input_directory, filename)
                with open(filepath, 'r') as file:
                    raw_content = file.read()
                    clean_content = preprocess_yaml_content(raw_content)
                    data = yaml.safe_load(clean_content)
                
                loot_table_name = data.get('MonoBehaviour', {}).get('m_Name', 'unknown_loot_table')
                loot_table_info, contains_loot_list = extract_loot_table_info(data, loot_table_name, guid_mapping)
                
                output_file = select_output_file(loot_table_name, output_files)
                header = f"<!-- \n#{loot_table_name} -->\n"
                output_file.write(header)
                for item in loot_table_info:
                    if 'grass' in loot_table_name.lower() or 'mixedseeds' in loot_table_name.lower():
                        output_file.write(f"{{{{Loot table|{item['name']}|{item['percentChance']:.4f}|{item['min']}|{item['max']}|{loot_table_name}}}}}\n")
                    else:
                        output_file.write(f"{{{{Loot table|{item['name']}|{item['percentChance']:.2f}|{item['min']}|{item['max']}|{loot_table_name}}}}}\n")
                
                debug_log.write(f"Processed loot table: {loot_table_name} in file: {filename}\n")
            except Exception as e:
                log_debug(f"Error processing file {filename}: {str(e)}")

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_mapping_path = 'Output/guid_lookup.json'
loot_table_list_path = 'Output/Drops/loot_table_list.txt'
output_files = {
    'enemy': open('Output/Drops/enemy_loot_table.txt', 'w'),
    'stone': open('Output/Drops/stone_loot_table.txt', 'w'),
    'microbe': open('Output/Drops/microbe_loot_table.txt', 'w'),
    'grass': open('Output/Drops/grass_loot_table.txt', 'w'),
    'ship': open('Output/Drops/ship_loot_table.txt', 'w'),
    'discovery': open('Output/Drops/discovery_loot_table.txt', 'w'),
    'friend_card': open('Output/Drops/friend_card_loot_table.txt', 'w'),
    'other': open('Output/Drops/other_loot_table.txt', 'w')
}
debug_output_path = '.hidden/debug_output/loot_table_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

try:
    # Load GUID mapping
    guid_mapping = guid_utils.load_guid_lookup(guid_mapping_path)

    # Parse loot tables
    parse_loot_tables(input_directory, guid_mapping, loot_table_list_path, output_files, debug_output_path)

    # Close all output files
    for file in output_files.values():
        file.close()

    # Print the required messages to the terminal
    print("Parsing completed successfully.")
    print(f"Debug information has been written to '{debug_output_path}'")
except Exception as e:
    log_debug(f'An error occurred: {str(e)}')
    print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")
