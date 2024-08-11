import re
import os
from Utilities import guid_utils

# Define paths
input_folder = "Input/Assets/TextAsset"
output_folder = "Output/Cutscenes"
debug_file_path = '.hidden/debug_output/noncourting_cinematics_debug.txt'
input_file_path = os.path.join(input_folder, 'English_Cine.txt')
output_file_path = os.path.join(output_folder, 'noncourtship_cutscenes.txt')
mapping_file_path = 'Output/guid_lookup.json'

# Function to log debug information
def log_debug(message):
    with open(debug_file_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

# Clear the debug file at the start
open(debug_file_path, 'w').close()

# Function to load NPC names from the JSON file using guid_utils
def load_guid_mapping(mapping_file_path):
    try:
        guid_mapping = guid_utils.load_guid_lookup(mapping_file_path)
        return guid_utils.create_mappings(guid_mapping)
    except Exception as e:
        log_debug(f"Error loading GUID mapping: {e}")
        return {}

# Clear the output file at the start
open(output_file_path, 'w').close()

# Function to format and write non-courting regions
def format_and_write_non_courting_regions(content, mappings):
    with open(output_file_path, 'a', encoding='utf-8') as output_file:
        # Extract all regions
        all_regions_pattern = re.compile(r'//#region\s+CINE\s+([^\n]+?)\s*\n([\s\S]*?)//#endregion', re.DOTALL)
        matches = list(all_regions_pattern.finditer(content))

        for match in matches:
            title = match.group(1).strip()
            if "COURTSHIP" not in title:
                title_formatted = title.split("...")[0].title().strip()
                region_content = match.group(2)

                formatted_content = f'data["{title_formatted}"] = {{\n'

                # Find dialogue sets within each region
                text_pattern = re.compile(r'"key":\s*"(npc_\d+|None)"\s*,[\s\S]*?"textSet":\s*\[(.*?)\s*\]', re.DOTALL)
                dialogue_sets = text_pattern.findall(region_content)

                for dialogue_set in dialogue_sets:
                    npc_key, texts = dialogue_set
                    npc_name = "None" if npc_key == "None" else guid_utils.get_name_from_save_id(npc_key, mappings)
                    text_entries = re.findall(r'\{[^}]*"text":\s*"([^"]+)"(?:,\s*"expression":\s*"([^"]+)")?[^}]*\}', texts)

                    for text_entry in text_entries:
                        text = text_entry[0].replace('$shipName', '[SHIP NAME]')
                        text = re.sub(r'\\n', '<br>', text)
                        expression = text_entry[1]
                        formatted_content += f'    {{npc = "{npc_name}", text = "{text}"'
                        if expression:
                            formatted_content += f', emote = "{expression}"'
                        formatted_content += '},\n'

                formatted_content += '}\n\n'
                output_file.write(formatted_content)
                log_debug(f"Formatted non-courtship region: {title_formatted}")

try:
    # Load GUID lookup data and create mappings
    mappings = load_guid_mapping(mapping_file_path)
    log_debug(f"Loaded mappings with {len(mappings['save_id_to_name'])} save IDs")

    # Read the input file
    with open(input_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # Log the length of the content read
    log_debug(f"Read {len(content)} characters from input file")

    # Format and write the non-courting regions
    format_and_write_non_courting_regions(content, mappings)

    # Print success message
    print(f"Non-courtship regions have been successfully identified, formatted, and written to '{output_file_path}'")

except Exception as e:
    log_debug(f'An error occurred: {str(e)}')
    print(f"An error occurred. Check the debug output for details: '{debug_file_path}'")
