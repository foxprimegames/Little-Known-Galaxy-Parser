import os
import json

# Define paths
input_folder = 'Input/Assets/MonoBehaviour'
output_file = 'Output/decoration_fixtures.txt'
debug_output_folder = '.hidden/debug_output'
debug_output_file = os.path.join(debug_output_folder, 'decoration_fixture_debug.txt')
guid_lookup_file = 'Output/guid_lookup.json'

# Ensure the debug output directory exists
os.makedirs(debug_output_folder, exist_ok=True)

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_file), exist_ok=True)

def log_debug(message):
    with open(debug_output_file, 'a') as debug_file:
        debug_file.write(message + '\n')

def load_guid_lookup(file_path):
    try:
        with open(file_path, 'r') as f:
            guid_lookup = json.load(f)
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
                        asset_data = asset_file.read()
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
    filename_to_name = load_guid_lookup(guid_lookup_file)
    fixtures = parse_assets(filename_to_name)
    save_fixtures(fixtures)
    log_debug(f'Total files with itemType 6: {len(fixtures)}')
    
    # Print the required messages to the terminal
    print(f"Decoration fixtures have been successfully written to '{output_file}'")
    print(f"Debug information has been written to '{debug_output_file}'")
