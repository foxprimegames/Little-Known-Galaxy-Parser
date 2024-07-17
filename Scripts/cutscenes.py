import os
import sys
import yaml
import json

# Add the Utilities directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Utilities')))

from Utilities import guid_utils
from Utilities.unity_yaml_loader import add_unity_yaml_constructors, preprocess_yaml_content

# Add Unity YAML constructors
add_unity_yaml_constructors()

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_lookup_path = 'Output/guid_lookup.json'
output_file_path = 'Output/Cutscenes/cutscene_information.txt'
debug_output_path = '.hidden/debug_output/cutscenes_debug.txt'

# Ensure output directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

def extract_cutscene_data(asset_file_path, mappings):
    cutscene_data = {
        "previousCineRequired": "",
        "oneFriendConditionPasses": "",
        "friendConditions": [],
        "activateAfterDays": "",
        "dayOfWeekRequired": "",
        "addEmails": [],
        "itemsToReward": [],
        "storeItemsToUnlock": [],
        "cinesToAddAtComplete": [],
        "endDayCine": "",
        "beginDayCine": "",
        "dateToTrigger": "",
        "quarterToTrigger": "",
        "endDayAfter": ""
    }

    with open(asset_file_path, 'r') as file:
        raw_content = file.read()
        clean_content = preprocess_yaml_content(raw_content)
        data = yaml.safe_load(clean_content)
        mono_behaviour = data.get('MonoBehaviour', {})
        
        previous_cine_guid = mono_behaviour.get("previousCineRequired", {}).get('guid', '')
        cutscene_data["previousCineRequired"] = guid_utils.get_name_from_guid(previous_cine_guid, mappings)
        cutscene_data["oneFriendConditionPasses"] = mono_behaviour.get("oneFriendConditionPasses", 0) == 1
        cutscene_data["activateAfterDays"] = mono_behaviour.get("activateAfterDays", "")
        cutscene_data["dayOfWeekRequired"] = mono_behaviour.get("dayOfWeekRequired", "")
        cutscene_data["addEmails"] = [guid_utils.get_name_from_guid(email.get('guid', ''), mappings) for email in mono_behaviour.get("addEmails", [])]
        
        # Append debugging information for itemsToReward to the debug file
        with open(debug_output_path, 'a') as debug_file:
            for item in mono_behaviour.get("itemsToReward", []):
                guid = item.get('itemData', {}).get('guid', '')
                if not guid:
                    debug_file.write(f"Empty or missing GUID found in itemsToReward in {asset_file_path}\n")
                    continue
                name = guid_utils.get_name_from_guid(guid, mappings)
                debug_file.write(f"Item GUID: {guid}, Name: {name}\n")
                cutscene_data["itemsToReward"].append(name)
        
        cutscene_data["storeItemsToUnlock"] = [guid_utils.get_name_from_guid(item.get('guid', ''), mappings) for item in mono_behaviour.get("storeItemsToUnlock", [])]
        cutscene_data["cinesToAddAtComplete"] = [guid_utils.get_name_from_guid(cine.get('guid', ''), mappings) for cine in mono_behaviour.get("cineScenesToAdd", [])]
        cutscene_data["endDayCine"] = mono_behaviour.get("endDayCine", "")
        cutscene_data["beginDayCine"] = mono_behaviour.get("beginDayCine", "")
        cutscene_data["dateToTrigger"] = mono_behaviour.get("dateToTrigger", "")
        cutscene_data["quarterToTrigger"] = mono_behaviour.get("quarterToTrigger", "")
        cutscene_data["endDayAfter"] = mono_behaviour.get("endDayAfter", "")
        
        friend_conditions = mono_behaviour.get("friendConditions", [])
        for condition in friend_conditions:
            guid = condition.get("npcToCheck", {}).get("guid", "")
            level = condition.get("friendshipLevelCondition", "")
            cutscene_data["friendConditions"].append(f"{guid_utils.get_name_from_guid(guid, mappings)} - Friend level {level}")

    return cutscene_data, raw_content

def main():
    try:
        # Load the GUID lookup and create mappings
        guid_lookup = guid_utils.load_guid_lookup(guid_lookup_path)
        mappings = guid_utils.create_mappings(guid_lookup)

        # Read the JSON file
        with open(guid_lookup_path, 'r') as file:
            data = json.load(file)
        
        # Filter filenames with save_id starting with "cine_"
        filtered_filenames = [
            entry['filename'] for entry in data if 'save_id' in entry and entry['save_id'].startswith('cine_')
        ]
        
        with open(output_file_path, 'w') as output_file, open(debug_output_path, 'a') as debug_file:
            for filename in filtered_filenames:
                asset_file_path = os.path.join(input_directory, f"{filename}.asset")
                if os.path.exists(asset_file_path):
                    try:
                        cutscene_data, raw_content = extract_cutscene_data(asset_file_path, mappings)
                        output_file.write(f"### {filename}\n")
                        output_file.write("REQUIREMENTS --\n")
                        output_file.write(f"previousCineRequired: {cutscene_data['previousCineRequired']}\n")
                        output_file.write(f"oneFriendConditionPasses: {cutscene_data['oneFriendConditionPasses']}\n")
                        output_file.write("friendConditions:\n")
                        for condition in cutscene_data["friendConditions"]:
                            output_file.write(f"  {condition}\n")
                        output_file.write("\nTRIGGER INFO --\n")
                        output_file.write(f"activateAfterDays: {cutscene_data['activateAfterDays']}\n")
                        output_file.write(f"endDayCine: {cutscene_data['endDayCine']}\n")
                        output_file.write(f"beginDayCine: {cutscene_data['beginDayCine']}\n")
                        output_file.write(f"dateToTrigger: {cutscene_data['dateToTrigger']}\n")
                        output_file.write(f"quarterToTrigger: {cutscene_data['quarterToTrigger']}\n")
                        output_file.write(f"dayOfWeekRequired: {cutscene_data['dayOfWeekRequired']}\n")
                        output_file.write(f"endDayAfter: {cutscene_data['endDayAfter']}\n")
                        output_file.write("\nADD TO PLAYER --\n")
                        output_file.write(f"addEmails: {', '.join(cutscene_data['addEmails'])}\n")
                        output_file.write(f"itemsToReward: {', '.join(cutscene_data['itemsToReward'])}\n")
                        output_file.write(f"storeItemsToUnlock: {', '.join(cutscene_data['storeItemsToUnlock'])}\n")
                        output_file.write(f"cinesToAddAtComplete: {', '.join(cutscene_data['cinesToAddAtComplete'])}\n")
                        output_file.write("\n")
                    except yaml.YAMLError as e:
                        debug_file.write(f"Error parsing {filename}: {str(e)}\n")
                        debug_file.write(f"File Content: {raw_content}\n")
                        debug_file.write(f"Parsed Content: {data}\n")
                        debug_file.write(f"Cutscene Data: {cutscene_data}\n")
        
        # Write debugging information to the debug file
        with open(debug_output_path, 'a') as debug_file:
            debug_file.write(f"Total entries processed: {len(data)}\n")
            debug_file.write(f"Filtered entries: {len(filtered_filenames)}\n")
            debug_file.write(f"Filtered filenames: {filtered_filenames}\n")
        
        # Print success message to terminal
        print("Filenames with save_id starting with 'cine_' have been successfully written to 'cutscenes.txt'.")

    except Exception as e:
        with open(debug_output_path, 'a') as debug_file:
            debug_file.write(f"An error occurred: {str(e)}\n")
        print("An error occurred. Check the debug output for details.")

if __name__ == "__main__":
    main()
