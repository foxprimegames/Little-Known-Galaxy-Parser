import os
import re
import json

def load_guid_mapping(mapping_file_path):
    """
    Loads the GUID mapping from the specified JSON file.

    Args:
        mapping_file_path (str): The path to the GUID mapping file.

    Returns:
        dict: A dictionary mapping GUIDs to their corresponding information.
    """
    with open(mapping_file_path, 'r') as file:
        guid_mapping = json.load(file)
    return guid_mapping

def load_english_emails(file_path):
    """
    Loads the English emails from the specified file.

    Args:
        file_path (str): The path to the English emails file.

    Returns:
        list: A list of dictionaries containing email information.
    """
    emails = []
    with open(file_path, 'r') as file:
        data = file.read()
        email_sections = data.split('//EMAIL_')[1:]
        for section in email_sections:
            trigger_match = re.match(r'(.*?)\s*{', section, re.DOTALL)
            trigger = trigger_match.group(1).strip() if trigger_match else ""
            json_part_match = re.search(r'{(.*?)}', section, re.DOTALL)
            json_part = json_part_match.group(1).strip() if json_part_match else ""
            json_part = json_part.replace('\n', '').replace('\r', '')
            try:
                email_data = json.loads(f"{{{json_part}}}")
                email_data['trigger'] = trigger
                emails.append(email_data)
            except json.JSONDecodeError:
                continue
    return emails

def sentence_case(s):
    """
    Converts a string to sentence case.

    Args:
        s (str): The string to convert.

    Returns:
        str: The string in sentence case.
    """
    return s.capitalize()

def parse_email_assets(input_directory, guid_mapping, debug_file):
    email_subjects = {}
    email_bodies = {}
    english_emails_path = os.path.join(input_directory, 'TextAsset', 'English_Emails.txt')
    
    # Load email subjects and bodies from English_Emails.txt
    with open(english_emails_path, 'r') as file:
        data = file.read()
        email_entries = re.findall(r'{.*?}', data, re.DOTALL)
        for entry in email_entries:
            save_id_match = re.search(r'"emailKey":\s*"([^"]+)"', entry)
            subject_match = re.search(r'"emailSubject":\s*"([^"]+)"', entry)
            body_match = re.search(r'"emailBody":\s*"([^"]+)"', entry)
            if save_id_match and subject_match and body_match:
                save_id = save_id_match.group(1)
                email_subjects[save_id] = subject_match.group(1)
                email_bodies[save_id] = body_match.group(1)
    
    emails = []
    for entry in guid_mapping:
        if 'save_id' not in entry or not entry['save_id'].startswith("email_"):
            continue

        save_id = entry['save_id']
        filename = entry['filename']
        subject = sentence_case(email_subjects.get(save_id, 'unknown'))
        body = email_bodies.get(save_id, 'unknown')

        asset_path = os.path.join(input_directory, 'MonoBehaviour', f"{filename}.asset")
        npc_emailer_guid = None
        items_to_attach = []

        if os.path.exists(asset_path):
            with open(asset_path, 'r') as file:
                asset_data = file.read()
                npc_emailer_match = re.search(r'npcEmailer:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}', asset_data)
                if npc_emailer_match:
                    npc_emailer_guid = npc_emailer_match.group(1)
                
                items_to_attach_match = re.findall(r'itemData:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}.*?amountOfItem:\s*(\d+)', asset_data, re.DOTALL)
                for item_guid, amount in items_to_attach_match:
                    items_to_attach.append(f"{item_guid}*{amount}")

        npc_name = sentence_case(next((e['name'] for e in guid_mapping if e['guid'] == npc_emailer_guid), 'unknown'))

        item_names = []
        for item in items_to_attach:
            try:
                item_guid, item_amount = item.split('*')
                item_name = sentence_case(next((e['name'] for e in guid_mapping if e['guid'] == item_guid), 'unknown_item'))
                if item_amount == '1':
                    item_names.append(item_name)
                else:
                    item_names.append(f"{item_name}*{item_amount}")
            except ValueError:
                debug_file.write(f"Skipping invalid item entry: {item}\n")
                continue

        gift = '; '.join(item_names)
        body = body.replace('$playerName', '[PLAYER]').replace('\\n', '<br>')

        email = f"{{{{Mail|collapse=true|trigger={filename.replace('.asset', '')}\n|npc={npc_name}\n|subject={subject}\n|gift={gift}\n|emailBody={body} }}}}"
        emails.append(email)

    return emails

# Define the input and output file paths
input_directory = 'Input/Assets'
mapping_file_path = 'Output/guid_lookup.json'
output_file_path = 'Output/Emails/all_emails.txt'
debug_output_path = '.hidden/debug_output/email_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Load the GUID mapping
guid_mapping = load_guid_mapping(mapping_file_path)

# Open the debug file for writing
with open(debug_output_path, 'w') as debug_file:
    debug_file.write(f"GUID to Item Mapping: {guid_mapping}\n")

    # Parse the email assets and get the formatted content
    parsed_emails = parse_email_assets(input_directory, guid_mapping, debug_file)

    # Write the output to a new file
    with open(output_file_path, 'w') as output_file:
        output_file.write('\n\n'.join(parsed_emails))

print(f"Parsed emails have been written to {output_file_path}")
print(f"Debug information has been written to {debug_output_path}")
