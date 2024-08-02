import re
import os
from Utilities import guid_utils

# Define paths
input_folder = "Input/Assets/TextAsset"
output_folder = "Output/Cutscenes"
debug_file_path = '.hidden/debug_output/courting_cinematics_debug.txt'
input_file_path = os.path.join(input_folder, 'English_Cine.txt')
mapping_file_path = 'Output/guid_lookup.json'

# Function to log debug information
def log_debug(message):
    with open(debug_file_path, 'a') as debug_file:
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

# Function to format the extracted content
def format_content(npc_name, cine_number, content):
    title_mapping = {
        "1": "First date with",
        "2": "Second date with",
        "3": "Third date with"
    }
    title = title_mapping.get(cine_number, "Date with")
    formatted_content = f"{{{{Cine|title={title} {npc_name}\n|npc={npc_name}\n"

    content = re.sub(r'\$playerName', '[PLAYER]', content)

    emote_count = 1
    text_pattern = re.compile(r'"text": "([^"]+)"(, "expression": "([^"]+)")?')
    option_pattern = re.compile(r'"optionText": "([^"]+)", "response": "([^"]+)"(, "responseExpression": "([^"]+)")?')

    for match in text_pattern.finditer(content):
        text = match.group(1)
        expression = match.group(3)
        formatted_content += f"|{text}"
        if expression:
            formatted_content += f"|emote{emote_count}={expression}"
        formatted_content += "\n"
        emote_count += 1

    options = option_pattern.findall(content)
    for i, option in enumerate(options, start=1):
        option_text, response_text, _, response_expression = option
        formatted_content += f"   |option{emote_count}{chr(64+i)}={option_text}\n"
        formatted_content += f"   |response{emote_count}{chr(64+i)}={response_text}\n"
        if response_expression:
            formatted_content += f"   |emote{emote_count}{chr(64+i)}={response_expression}\n"
    formatted_content += "}}\n"
    return formatted_content

try:
    # Load GUID lookup data and create mappings
    mappings = load_guid_mapping(mapping_file_path)
    log_debug(f"Loaded mappings with {len(mappings['save_id_to_name'])} save IDs")

    # Log the contents of the mappings for debugging
    log_debug(f"Mappings content: {mappings['save_id_to_name']}")

    # Read the input file
    with open(input_file_path, 'r') as file:
        content = file.read()

    # Log the length of the content read
    log_debug(f"Read {len(content)} characters from input file")

    # Extract courtship cinematics regions using the provided regex patterns
    courtship_pattern = re.compile(
        r'//#endregion\s*\.+\n\s*//#region CINE COURTSHIPS NPC PORTIONS\s([\s\S]*?)//#region CINE COURTSHIP\s([\s\S]*?)//#endregion\s*\.+\n\s*//#endregion\s*\.+\n',
        re.DOTALL
    )

    matches = list(courtship_pattern.finditer(content))

    # Log the number of matches found
    log_debug(f"Found {len(matches)} courtship regions")

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    npc_contents = {}

    for match in matches:
        extracted_section = match.group(2)
        
        # Log extracted section for debugging
        log_debug(f"Extracted section: {extracted_section[:200]}...")

        # Extract NPC key and date number from the cineKey
        cine_key_matches = re.findall(r'"cineKey": "([^"]+)"', extracted_section)
        
        for cine_key in cine_key_matches:
            npc_key_match = re.match(r'(npc_\d+)_(\d+)', cine_key)
            if npc_key_match:
                npc_key = npc_key_match.group(1)
                cine_number = npc_key_match.group(2)
                npc_name = guid_utils.get_name_from_save_id(npc_key, mappings)
                log_debug(f"Identified NPC: {npc_name} for cineKey: {cine_key}")

                if npc_name not in npc_contents:
                    npc_contents[npc_name] = ""

                # Extract only the relevant content for this NPC
                start_idx = extracted_section.find(f'"cineKey": "{cine_key}"')
                end_idx = extracted_section.find('//#endregion', start_idx)
                npc_specific_content = extracted_section[start_idx:end_idx]

                # Format the extracted content
                formatted_content = format_content(npc_name, cine_number, npc_specific_content)
                npc_contents[npc_name] += formatted_content

    # Write each NPC's content to a separate file
    for npc_name, content in npc_contents.items():
        output_file_path = os.path.join(output_folder, f'courtship_cine_{npc_name}.txt')
        with open(output_file_path, 'w') as output_file:
            output_file.write(content)
        log_debug(f"Written content to {output_file_path}")

    # Print success message
    print(f"Courting cinematics regions have been successfully extracted, formatted, and written to individual files")

except Exception as e:
    log_debug(f'An error occurred: {str(e)}')
    print(f"An error occurred. Check the debug output for details: '{debug_file_path}'")

