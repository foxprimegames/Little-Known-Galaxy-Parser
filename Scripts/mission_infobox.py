import re
import os
import json
import yaml
from Utilities.unity_yaml_loader import preprocess_yaml_content, add_unity_yaml_constructors

# Define paths
input_file_path = 'Input/Assets/TextAsset/English_Quests.txt'
guid_lookup_path = 'Output/guid_lookup.json'
mono_behaviour_path = 'Input/Assets/MonoBehaviour/'
output_file_path = 'Output/Missions/mission_infobox.txt'
debug_output_path = '.hidden/debug_output/mission_infobox_debug.txt'

# Ensure output directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Initialize debug file (replace content each run)
def initialize_debug_file():
    with open(debug_output_path, 'w', encoding='utf-8') as debug_file:
        debug_file.write("Debug Log Initialized\n")

def log_debug(message):
    with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

# Initialize the debug file
initialize_debug_file()

# Load GUID lookup from JSON file
with open(guid_lookup_path, 'r', encoding='utf-8') as file:
    guid_lookup = json.load(file)

def lookup_guid(guid, return_field='name'):
    for entry in guid_lookup:
        if entry.get('guid') == guid:
            return entry.get(return_field, 'Unknown')
    return 'Unknown'

# Add Unity YAML constructors
add_unity_yaml_constructors()

def parse_mono_behaviour_file(filename):
    file_path = os.path.join(mono_behaviour_path, f"{filename}.asset")
    log_debug(f"Attempting to load file: {file_path}")

    if not os.path.exists(file_path):
        log_debug(f"File not found: {file_path}")
        return {}

    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            content = file.read()
            log_debug(f"Raw content of {file_path}:\n{content}\n")

            # Preprocess the YAML content
            content = preprocess_yaml_content(content)
            log_debug(f"Preprocessed content of {file_path}:\n{content}\n")

            # Parse the YAML content
            mono_behaviour = yaml.safe_load(content).get('MonoBehaviour', {})
            log_debug(f"Parsed MonoBehaviour data: {mono_behaviour}")

            # Process fields
            expires_in_days = mono_behaviour.get('expiresInDays', 'Unknown')
            if isinstance(expires_in_days, dict) and expires_in_days.get('fileID') == 0:
                expires_in_days = 'Unlimited'
            npc_owner_guid = mono_behaviour.get('npcOwner', {}).get('guid', 'Unknown')
            npc_owner_name = lookup_guid(npc_owner_guid)

            # Replace GUIDs in goalsList and cinesToAddAtActivation with filenames
            goals_list = '; '.join(lookup_guid(goal.get('guid', 'Unknown'), 'filename') for goal in mono_behaviour.get('goalsList', []))
            cines_to_add = '; '.join(lookup_guid(cine.get('guid', 'Unknown'), 'filename') for cine in mono_behaviour.get('cinesToAddAtActivation', []))

            # Replace GUIDs in questsToAddAtActivation and unlockQuests with names
            quests_to_add = '; '.join(lookup_guid(quest.get('guid', 'Unknown')) for quest in mono_behaviour.get('questsToAddAtActivation', []))
            unlock_quests = '; '.join(lookup_guid(quest.get('guid', 'Unknown')) for quest in mono_behaviour.get('unlockQuests', []))

            # Replace GUIDs in unlockStoreItemsOnActivate with filenames
            unlock_store_items = '; '.join(lookup_guid(item.get('guid', 'Unknown'), 'filename') for item in mono_behaviour.get('unlockStoreItemsOnActivate', []))
            purchase_store_items = '; '.join(lookup_guid(item.get('guid', 'Unknown'), 'filename') for item in mono_behaviour.get('purchaseStoreItemsAtComplete', []))

            return {
                'questType': mono_behaviour.get('questType', 'Unknown'),
                'npcOwner': npc_owner_name,
                'goalsList': goals_list,
                'expiresInDays': expires_in_days,
                'activateAfterDays': mono_behaviour.get('activateAfterDays', 'Unknown'),
                'questsToAddAtActivation': quests_to_add,
                'cinesToAddAtActivation': cines_to_add,
                'unlockStoreItemsOnActivate': unlock_store_items,
                'purchaseStoreItemsAtComplete': purchase_store_items,
                'unlockQuests': unlock_quests,
            }
        except yaml.YAMLError as e:
            log_debug(f"YAML error reading file {file_path}: {e}")
            return {}
        except Exception as e:
            log_debug(f"General error processing file {file_path}: {e}")
            return {}

# Read English_Quests.txt, extract questKey, questName, and questDescription from each region
with open(input_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

regions = re.findall(r'//#region\s+([^#]+?)\s+\.*?\s*\n(.*?)\n\s*//#endregion', content, re.DOTALL)

quests = []
for region_name, region_content in regions:
    quest_key = re.search(r'"questKey":\s*"([^"]+)"', region_content)
    quest_name = re.search(r'"questName":\s*"([^"]+)"', region_content)
    quest_description = re.search(r'"questDescription":\s*"([^"]+)"', region_content)
    
    if quest_key and quest_name and quest_description:
        # Find the filename associated with the questKey in the guid_lookup
        filename = 'Unknown'
        for entry in guid_lookup:
            if entry.get('save_id') == quest_key.group(1):
                filename = entry.get('filename', 'Unknown')
                break

        log_debug(f"Quest Key: {quest_key.group(1)} mapped to filename: {filename}")

        # Parse the MonoBehaviour file
        mono_data = parse_mono_behaviour_file(filename)

        quests.append({
            'region': region_name.strip().replace(' ', '_'),
            'questKey': quest_key.group(1),
            'questName': quest_name.group(1),
            'questDescription': quest_description.group(1),
            'filename': filename,
            'mono_data': mono_data
        })

try:
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for quest in quests:
            output_file.write(f"\n----------------------------------------\n")
            output_file.write(f"## Region: {quest['region']}\n")
            output_file.write(f"{{{{Mission infobox\n")
            output_file.write(f"|name     = {quest['questName']}\n")
            output_file.write(f"|id       = {quest['region']}\n")
            output_file.write(f"|obj      = {quest['questDescription']}\n")
            output_file.write(f"|type     = {quest['mono_data'].get('questType', 'Unknown')}\n")
            output_file.write(f"|time     = {quest['mono_data'].get('expiresInDays', 'Unknown')}\n")
            output_file.write(f"|location = \n")
            output_file.write(f"|prereq   = \n")
            output_file.write(f"|requires = {quest['mono_data'].get('goalsList', 'Unknown')}\n")
            output_file.write(f"|rewards  = \n")
            output_file.write(f"|npcs     = {quest['mono_data'].get('npcOwner', 'Unknown')}\n")
            output_file.write(f"|prev     = \n")
            output_file.write(f"|next     =  }}}}\n")

            # Conditionally display additional fields
            if quest['mono_data'].get('activateAfterDays', ''):
                output_file.write(f"activateAfterDays = {quest['mono_data'].get('activateAfterDays')}\n")
            if quest['mono_data'].get('questsToAddAtActivation', ''):
                output_file.write(f"questsToAddAtActivation = {quest['mono_data'].get('questsToAddAtActivation')}\n")
            if quest['mono_data'].get('cinesToAddAtActivation', ''):
                output_file.write(f"cinesToAddAtActivation = {quest['mono_data'].get('cinesToAddAtActivation')}\n")
            if quest['mono_data'].get('unlockStoreItemsOnActivate', ''):
                output_file.write(f"unlockStoreItemsOnActivate = {quest['mono_data'].get('unlockStoreItemsOnActivate')}\n")
            if quest['mono_data'].get('purchaseStoreItemsAtComplete', ''):
                output_file.write(f"purchaseStoreItemsAtComplete = {quest['mono_data'].get('purchaseStoreItemsAtComplete')}\n")
            if quest['mono_data'].get('unlockQuests', ''):
                output_file.write(f"unlockQuests = {quest['mono_data'].get('unlockQuests')}\n")

    log_debug("Search completed successfully. Output file created.")
    print(f"Parsed files have been written to '{output_file_path}'")
except Exception as e:
    log_debug(f"An error occurred during search: {str(e)}")
    print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")
