import os
import re
import json
from Utilities import guid_utils

# Define paths
input_folder = 'Input/Assets/MonoBehaviour/'
output_folder = 'Output/Missions/'
debug_output_path = '.hidden/debug_output/missions_npc_bb_request_debug.txt'
guid_lookup_path = 'Output/guid_lookup.json'
npc_text_asset_folder = 'Input/Assets/TextAsset/'

# Ensure output directories exist
os.makedirs(output_folder, exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

def log_debug(message):
    with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

# Load GUID lookup
with open(guid_lookup_path, 'r', encoding='utf-8') as f:
    guid_lookup = json.load(f)

def get_item_name_by_guid(guid, guid_lookup):
    for item in guid_lookup:
        if item.get('guid') == guid:
            return item.get('name', 'Unknown'), item.get('filename', 'Unknown')
    return 'Unknown', 'Unknown'

def find_buy_value(filename):
    if not filename:
        return 'None'
    file_path = os.path.join(input_folder, f"{filename}.asset")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'buyValue: (\d+)', content)
            if match:
                return match.group(1)
    except Exception as e:
        log_debug(f"Error finding buy value in file {file_path}: {e}")
    return 'None'

def extract_items_can_request_info(file_path, guid_lookup):
    items_info = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

            # Find itemData and amtRangeOfItem using regex
            pattern = re.compile(
                r'itemData: \{fileID: \d+, guid: ([a-f0-9]+), type: \d+\}\s+amtRangeOfItem:\s+minimumNum: (\d+)\s+maxiumNum: (\d+)',
                re.MULTILINE
            )
            matches = pattern.findall(content)
            
            if matches:
                log_debug(f"Processing file: {file_path}")  # Log only if matches are found
            
            for match in matches:
                guid, min_num, max_num = match

                # Get item name and filename using the GUID
                item_name, filename = get_item_name_by_guid(guid, guid_lookup)

                if not filename or filename == "Unknown":
                    log_debug(f"Could not find filename for GUID {guid} (Item: {item_name})")
                    continue

                # Find the buy value
                buy_value = find_buy_value(filename)
                items_info.append({
                    'name': item_name,
                    'min': min_num,
                    'max': max_num,
                    'buy_value': buy_value
                })
                log_debug(f"Item Name: {item_name}, Min: {min_num}, Max: {max_num}, Buy Value: {buy_value}")

    except Exception as e:
        log_debug(f"Error processing file {file_path}: {e}")
    return items_info

def extract_quest_text(npc_name):
    npc_file_path = os.path.join(npc_text_asset_folder, f"English_{npc_name}.txt")
    if not os.path.exists(npc_file_path):
        log_debug(f"NPC text asset file not found: {npc_file_path}")
        return "", ""

    try:
        with open(npc_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Extract the quest name
            quest_name_match = re.search(r'"questName":\s*"([^"]+)"', content)
            quest_name = quest_name_match.group(1) if quest_name_match else "Unknown_Quest"

            # Extract the quest text
            pattern = re.compile(
                r'//#region T_BRING ITEMS\s+((?:.|\n)*?)\s+//#endregion',
                re.MULTILINE
            )
            quest_text_match = pattern.search(content)
            quest_text = quest_text_match.group(1) if quest_text_match else ""
            
            if quest_text:
                log_debug(f"Quest text found for NPC: {npc_name}, Quest: {quest_name}")
            else:
                log_debug(f"No quest text found in {npc_file_path} for NPC: {npc_name}")
            
            return quest_name, quest_text

    except Exception as e:
        log_debug(f"Error extracting quest text for {npc_name}: {e}")
        return "", ""

def process_assets(input_folder, guid_lookup):
    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.asset'):
                file_path = os.path.join(root, file)
                items_info = extract_items_can_request_info(file_path, guid_lookup)
                npc_name = file.split('.')[0]
                if items_info:
                    quest_name, quest_text = extract_quest_text(npc_name)
                    
                    if quest_name == "Unknown_Quest":
                        log_debug(f"Skipping NPC {npc_name} due to unknown quest name.")
                        continue
                    
                    output_lines = []
                    output_lines.append(f"## {npc_name}")
                    output_lines.append('{{bulletin mission table')
                    for idx, item in enumerate(items_info, start=1):
                        output_lines.append(f"|item{idx} = {item['name']}")
                        output_lines.append(f"   |buyValue{idx} = {item['buy_value']}")
                        output_lines.append(f"   |min{idx} = {item['min']}")
                        output_lines.append(f"   |max{idx} = {item['max']}")
                    output_lines.append("}}")
                    if quest_text:
                        output_lines.append(f"\n{quest_text}\n")
                    
                    # Write to a file named after the quest
                    quest_file_name = f"mission_bb_request_{quest_name.replace(' ', '_')}.txt"
                    quest_file_path = os.path.join(output_folder, quest_file_name)
                    try:
                        with open(quest_file_path, 'w', encoding='utf-8') as output_file:
                            output_file.write("\n".join(output_lines))
                        log_debug(f"Successfully wrote output to {quest_file_path}")
                    except Exception as e:
                        log_debug(f"Failed to write output to {quest_file_path}: {e}")

# Clear the debug file at the start of each run
open(debug_output_path, 'w').close()

# Run the processing function
process_assets(input_folder, guid_lookup)
