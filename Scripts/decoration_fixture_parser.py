import os
import sys
import json
from Utilities import guid_utils
from Utilities.unity_yaml_loader import preprocess_yaml_content

# Define paths
input_folder = 'Input/Assets/MonoBehaviour'
output_file = 'Output/decoration_fixtures.txt'
debug_output_path = '.hidden/debug_output/decoration_fixture_debug.txt'
guid_lookup_file = 'Output/guid_lookup.json'

# Ensure output directories exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

def log_debug(message):
    with open(debug_output_path, 'a') as debug_file:
        debug_file.write(message + '\n')

def load_guid_lookup(file_path):
    try:
        guid_lookup = guid_utils.load_guid_lookup(file_path)
        filename_to_name = {entry['filename']: entry.get('name', entry['filename']) for entry in guid_lookup}
        return filename_to_name
    except Exception as e:
        log_debug(f'Error loading guid lookup file: {e}')
        return {}

def parse_assets(filename_to_name):
    fixtures = []
    for root, dirs, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.asset'):
                file_base_name = os.path.splitext(file)[0]  # Strip the .asset extension
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as asset_file:
                        asset_data = preprocess_yaml_content(asset_file.read())
                        if 'itemType: 6' in asset_data:
                            can_put_on_tables = 'no'
                            building_surface = 'unknown'
                            deco_type = 'unknown'
                            for line in asset_data.splitlines():
                                if 'canPutOnTables:' in line:
                                    value = int(line.split(':')[-1].strip())
                                    can_put_on_tables = 'yes' if value == 1 else 'no'
                                elif 'buildingSurface:' in line:
                                    value = int(line.split(':')[-1].strip())
                                    building_surface = 'floor' if value == 1 else 'wall' if value == 2 else 'unknown'
                                elif 'decoType:' in line:
                                    deco_type = line.split(':')[-1].strip()
                            fixture_name = filename_to_name.get(file_base_name, file_base_name)
                            fixtures.append(f'{fixture_name} - canPutOnTables: {can_put_on_tables}, buildingSurface: {building_surface}, decoType: {deco_type}')
                            log_debug(f'Found itemType 6 in file: {file}')
                except Exception as e:
                    log_debug(f'Error opening file {file}: {e}')
    
    return fixtures

def save_fixtures(fixtures):
    try:
        with open(output_file, 'w') as out_file:
            for fixture in fixtures:
                out_file.write(f'{fixture}\n')
    except Exception as e:
        log_debug(f'Error writing to output file: {e}')

if __name__ == '__main__':
    try:
        filename_to_name = load_guid_lookup(guid_lookup_file)
        fixtures = parse_assets(filename_to_name)
        save_fixtures(fixtures)
        log_debug(f'Total files with itemType 6: {len(fixtures)}')
        
        # Print the required messages to the terminal
        print(f"Decoration fixtures have been successfully written to '{output_file}'")
    except Exception as e:
        log_debug(f'An error occurred: {str(e)}')
        print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")
