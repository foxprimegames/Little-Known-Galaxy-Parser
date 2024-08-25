import os
import re
import json

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_lookup_path = 'Output/guid_lookup.json'
output_file_path = 'Output/Recipes/loot_table_recipes.txt'
debug_output_path = '.hidden/debug_output/loot_table_recipes_debug.txt'

def log_debug(message):
    with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

def load_guid_mapping(guid_lookup_path):
    log_debug(f"Loading GUID mapping from: {guid_lookup_path}")
    with open(guid_lookup_path, 'r') as file:
        guid_mapping = json.load(file)
        log_debug(f"GUID mapping loaded. Total entries: {len(guid_mapping)}")
        return guid_mapping

def extract_loot_table_info(filename):
    loot_table_info = []
    file_path = os.path.join(input_directory, filename + ".asset")
    log_debug(f"Extracting loot table info from: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            in_loot_table = False
            for line in f:
                stripped_line = line.strip()
                if stripped_line == "lootTable:":
                    in_loot_table = True
                    log_debug(f"Found lootTable in {file_path}")
                    continue
                if in_loot_table and not stripped_line.startswith("-"):
                    break
                if in_loot_table:
                    item_to_drop_match = re.search(r'itemToDrop:\s*{fileID:\s*\d+,\s*guid:\s*([0-9a-fA-F]+)}', stripped_line)
                    percent_chance_match = re.search(r'percentChance:\s*(\d+)', stripped_line)
                    min_num_match = re.search(r'minimumNum:\s*(\d+)', stripped_line)
                    max_num_match = re.search(r'maxiumNum:\s*(\d+)', stripped_line)
                    if item_to_drop_match:
                        item_to_drop = item_to_drop_match.group(1)
                        log_debug(f"Extracted itemToDrop GUID: {item_to_drop}")
                        loot_table_info.append({
                            "itemToDrop": item_to_drop,
                            "percentChance": percent_chance_match.group(1) if percent_chance_match else None,
                            "min": min_num_match.group(1) if min_num_match else None,
                            "max": max_num_match.group(1) if max_num_match else None
                        })
        log_debug(f"Completed extracting loot table info from {file_path}. Total items found: {len(loot_table_info)}")
    except Exception as e:
        log_debug(f"Error while extracting loot table info from {file_path}: {e}")
    return loot_table_info

def search_files(guid_mapping):
    log_debug(f"Starting search in directory: {input_directory}")
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

        # Prepare the output and debug files
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for root, _, files in os.walk(input_directory):
                for file in files:
                    if file.endswith('.asset'):
                        file_path = os.path.join(root, file)
                        log_debug(f"Processing file: {file_path}")
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                in_machine_production_guide = False
                                current_indent_level = None
                                produces_item_indent = None
                                machine_type = None
                                produce_duration = None
                                loot_table_guid = None
                                loot_table_filename = None

                                for line in f:
                                    stripped_line = line.strip()
                                    current_indent = len(line) - len(stripped_line)

                                    # Check if we are entering the machineProductionGuide block
                                    if stripped_line == "machineProductionGuide:":
                                        in_machine_production_guide = True
                                        current_indent_level = current_indent
                                        block_content = []
                                        log_debug(f"Started machineProductionGuide block in {file_path}")
                                        continue

                                    if in_machine_production_guide:
                                        block_content.append(stripped_line)

                                        # Extract machineType
                                        if "machineType:" in stripped_line:
                                            machine_type = re.search(r'machineType:\s*(\d+)', stripped_line).group(1)
                                            log_debug(f"Found machineType: {machine_type} in {file_path}")

                                        # Extract produceDuration
                                        if "produceDuration:" in stripped_line:
                                            produce_duration = re.search(r'produceDuration:\s*(\d+)', stripped_line).group(1)
                                            log_debug(f"Found produceDuration: {produce_duration} in {file_path}")

                                        # Check for producesItem
                                        if "producesItem:" in stripped_line:
                                            produces_item_indent = current_indent
                                            log_debug(f"Found producesItem in {file_path}")

                                        # Extract lootTable GUID and map to filename
                                        if produces_item_indent is not None and current_indent > produces_item_indent:
                                            if "lootTable:" in stripped_line and "guid:" in stripped_line:
                                                loot_table_guid = re.search(r'guid:\s*([0-9a-fA-F]+)', stripped_line).group(1)
                                                loot_table_filename = next((entry["filename"] for entry in guid_mapping if entry["guid"] == loot_table_guid), None)
                                                log_debug(f"Found lootTable GUID: {loot_table_guid} mapped to {loot_table_filename} in {file_path}")
                                                break

                                    # Exit machineProductionGuide block if a new top-level section starts
                                    if in_machine_production_guide and current_indent <= current_indent_level and not line.startswith(" "):
                                        in_machine_production_guide = False
                                        produces_item_indent = None
                                        log_debug(f"Ended machineProductionGuide block in {file_path}")

                                if machine_type and produce_duration and loot_table_filename:
                                    output_file.write(f"### {file}\n")
                                    output_file.write(f"machineType: {machine_type}\n")
                                    output_file.write(f"produceDuration: {produce_duration}\n")
                                    output_file.write(f"lootTable: {loot_table_filename}\n")

                                    # Extract and write loot table details
                                    loot_table_info = extract_loot_table_info(loot_table_filename)
                                    for item in loot_table_info:
                                        output_file.write(f"   itemToDrop: {item['itemToDrop']}\n")
                                        output_file.write(f"   percentChance: {item['percentChance']}\n")
                                        output_file.write(f"   min: {item['min']} max: {item['max']}\n")
                                    output_file.write("\n")
                                else:
                                    log_debug(f"No match in: {file_path}")
                        except Exception as e:
                            log_debug(f"Error processing file {file_path}: {e}")

        log_debug("Search completed successfully. Output file created.")
        print(f"Parsed files have been written to '{output_file_path}'")
    except Exception as e:
        log_debug(f"An error occurred during search: {str(e)}")
        print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")

if __name__ == "__main__":
    log_debug("Starting loot_table_recipes.py execution")
    try:
        guid_mapping = load_guid_mapping(guid_lookup_path)
    except Exception as e:
        log_debug(f"Failed to load GUID lookup: {e}")
        print("An error occurred. Check the debug output for details.")
        exit()

    search_files(guid_mapping)
    log_debug("Finished loot_table_recipes.py execution")
