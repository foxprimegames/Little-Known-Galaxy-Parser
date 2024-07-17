import os
import re
import yaml
from Utilities.unity_yaml_loader import preprocess_yaml_content

def log_debug(message):
    with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

def find_loot_table_files(input_directory, output_file_path, debug_output_path):
    """
    Find files containing loot tables and write their names to an output file.
    """
    loot_table_files = []

    with open(debug_output_path, 'w') as debug_log:
        for filename in os.listdir(input_directory):
            if filename.endswith(".asset"):
                filepath = os.path.join(input_directory, filename)
                with open(filepath, 'r') as file:
                    raw_content = file.read()
                    clean_content = preprocess_yaml_content(raw_content)
                    try:
                        data = yaml.safe_load(clean_content)
                        if 'MonoBehaviour' in data and 'm_Name' in data['MonoBehaviour'] and 'lootTable' in data['MonoBehaviour']:
                            loot_table_files.append(filename)
                            debug_log.write(f"Found loot table: {data['MonoBehaviour']['m_Name']} in file: {filename}\n")
                        else:
                            debug_log.write(f"No loot table found in file: {filename}\n")
                    except yaml.YAMLError as e:
                        debug_log.write(f"YAML error in file: {filename} - {e}\n")

    with open(output_file_path, 'w') as output_file:
        for filename in loot_table_files:
            output_file.write(filename + '\n')

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
output_file_path = 'Output/Drops/loot_table_list.txt'
debug_output_path = '.hidden/debug_output/loot_table_extraction_debug.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

try:
    # Find loot table files
    find_loot_table_files(input_directory, output_file_path, debug_output_path)

    # Print the required messages to the terminal
    print(f"Loot table list has been written to '{output_file_path}'")
except Exception as e:
    log_debug(f'An error occurred: {str(e)}')
    print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")
