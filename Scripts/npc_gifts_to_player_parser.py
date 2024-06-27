import os
import re
import json
from collections import defaultdict

# Define paths
input_folder = 'Input/Assets/TextAsset'
output_folder = 'Output/Gifts'
debug_folder = '.hidden/debug_output'
guid_lookup_path = 'Output/guid_lookup.json'
output_file = os.path.join(output_folder, 'npc_gifts_to_player.txt')
debug_file = os.path.join(debug_folder, 'npc_gifts_to_player_debug.txt')

# Ensure output directories exist
os.makedirs(output_folder, exist_ok=True)
os.makedirs(debug_folder, exist_ok=True)

# Function to load the guid lookup data
def load_guid_mapping(mapping_file_path):
    with open(mapping_file_path, 'r') as file:
        guid_mapping = json.load(file)
    return guid_mapping

# Load the guid lookup data
guid_mapping = load_guid_mapping(guid_lookup_path)

# Create dictionaries to map save_id and item_id to names
save_id_to_name = {entry['save_id']: entry['name'] for entry in guid_mapping if 'save_id' in entry and 'name' in entry}
item_id_to_name = {entry['save_id']: entry['name'] for entry in guid_mapping if 'save_id' in entry and 'name' in entry}

# Regular expressions to find the quest key, itemID, and NPC name in the specified pattern
npc_name_pattern = re.compile(r'"name":\s*"(.*?)"')
quest_pattern = re.compile(r'"key":\s*"(quest_\d+)"')
text_set_pattern = re.compile(r'"textSet":\s*\[(.*?)\]', re.DOTALL)
reward_pattern = re.compile(r'"boxType": "Reward".*?"itemID": "(item_\d+)",\s*"amount": (\d+)', re.DOTALL)
dialogue_pattern = re.compile(r'"text":\s*"(.*?)"', re.DOTALL)

# Lists to store results and debug information
results = []
debug_info = []
npc_gifts_combined = defaultdict(list)

# Function to find NPC name in the file content
def find_npc_name(content):
    npc_name_match = npc_name_pattern.search(content)
    return npc_name_match.group(1) if npc_name_match else "Unknown NPC"

# Function to convert item names to sentence case
def to_sentence_case(text):
    return text.capitalize()

# Parse quest rewards
for root, dirs, files in os.walk(input_folder):
    for file in files:
        if file.endswith('.txt'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    npc_name = find_npc_name(content)
                    quest_keys = quest_pattern.findall(content)
                    
                    for quest in quest_keys:
                        text_set_match = re.search(rf'"key":\s*"{quest}".*?"textSet":\s*\[(.*?)\]', content, re.DOTALL)
                        if text_set_match:
                            text_set_content = text_set_match.group(1)
                            reward_match = reward_pattern.search(text_set_content)
                            if reward_match:
                                item_id = reward_match.group(1)
                                amount = int(reward_match.group(2))
                                quest_name = save_id_to_name.get(quest, f"Unknown ({quest})")
                                item_name = to_sentence_case(item_id_to_name.get(item_id, f"Unknown ({item_id})"))
                                amount_str = f"*{amount}" if amount > 1 else ""
                                npc_gifts_combined[npc_name].append(f"{item_name}{amount_str}:Dialogue after starting [[{quest_name}]]")
                                debug_info.append(f"Found reward for {quest} ({quest_name}) in {file} with item {item_id} ({item_name}) and amount {amount}")
                            else:
                                debug_info.append(f"No reward found for {quest} in {file}")
                        else:
                            debug_info.append(f"No textSet found for {quest} in {file}")
                    
            except Exception as e:
                debug_info.append(f"Error processing file {file}: {e}")

# Parse email gifts
def parse_email_assets(input_directory, guid_mapping, debug_file):
    email_gifts = {}
    english_emails_path = os.path.join(input_directory, 'TextAsset', 'English_Emails.txt')
    
    # Load email names from English_Emails.txt
    with open(english_emails_path, 'r', encoding='utf-8') as file:
        data = file.read()
        email_sections = re.split(r'//EMAIL_', data)[1:]
        for section in email_sections:
            email_name_match = re.match(r'([\w\s]+)\s*\.+', section)
            email_name = email_name_match.group(1).strip() if email_name_match else "unknown_email"
            email_key_match = re.search(r'"emailKey":\s*"([^"]+)"', section)
            if email_key_match:
                email_key = email_key_match.group(1)
                email_gifts[email_key] = {'email_name': email_name, 'gifts': [], 'npc_name': 'Unknown NPC'}

    for entry in guid_mapping:
        if 'save_id' not in entry or not entry['save_id'].startswith("email_"):
            continue

        save_id = entry['save_id']
        filename = entry['filename']
        asset_path = os.path.join(input_directory, f"MonoBehaviour/{filename}.asset")

        if os.path.exists(asset_path):
            with open(asset_path, 'r') as file:
                asset_data = file.read()
                npc_emailer_match = re.search(r'npcEmailer:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}', asset_data)
                if npc_emailer_match:
                    npc_emailer_guid = npc_emailer_match.group(1)
                    npc_name = next((e['name'] for e in guid_mapping if e['guid'] == npc_emailer_guid), 'Unknown NPC')
                    if save_id in email_gifts:
                        email_gifts[save_id]['npc_name'] = npc_name
                
                items_to_attach = re.findall(r'itemData:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}.*?amountOfItem:\s*(\d+)', asset_data, re.DOTALL)
                for item_guid, amount in items_to_attach:
                    item_name = to_sentence_case(next((e['name'] for e in guid_mapping if e['guid'] == item_guid), 'unknown_item'))
                    if amount == '1':
                        email_gifts[save_id]['gifts'].append(item_name)
                    else:
                        email_gifts[save_id]['gifts'].append(f"{item_name}*{amount}")

    for email_key, details in email_gifts.items():
        if details['gifts'] and "friend" in details['email_name'].lower():
            npc_name = details['npc_name']
            gift_str = ', '.join(details['gifts'])
            email_name = details['email_name']
            if "friend" in email_name.lower() and "01" in email_name:
                formatted_email_name = "Friendship eMail (friend)"
            elif "friend" in email_name.lower() and "02" in email_name:
                formatted_email_name = "Friendship eMail (best friend)"
            else:
                formatted_email_name = email_name
            npc_gifts_combined[npc_name].append(f"{gift_str}:{formatted_email_name}")

# Parse the email assets
parse_email_assets('Input/Assets', guid_mapping, debug_file)

# Write results to the output file, excluding entries with 'false'
with open(output_file, 'w', encoding='utf-8') as f:
    for npc_name, gifts in npc_gifts_combined.items():
        combined_gifts = ', '.join(gifts)
        f.write(f"## {npc_name}\n{combined_gifts}\n\n")  # Add a blank line between NPC entries

# Write debug information to the debug file
with open(debug_file, 'w', encoding='utf-8') as f:
    for info in debug_info:
        f.write(info + '\n')

# Print messages to the terminal
print(f"Gifts for the player written to {output_file}")
print(f"Debug information has been written to {debug_file}")
