import json
import re
import os
from guid_mapper import load_guid_to_item_mapping
from email_asset_parser import parse_email_assets

def parse_emails(file_path, guid_to_item, email_assets, debug_file):
    """
    Parses emails from the given file and includes item information.

    Args:
        file_path (str): The path to the file containing email data.
        guid_to_item (dict): A dictionary mapping GUIDs to item names.
        email_assets (dict): A dictionary mapping saveIDs to items and their quantities.
        debug_file (file object): The file object to write debug information to.

    Returns:
        str: The formatted content of all emails.
    """
    # Read the content of the file
    with open(file_path, 'r') as file:
        data = file.read()

    # Split the data by each email to handle it in parts
    email_sections = data.split('//EMAIL_')[1:]

    # Function to process a single email section
    def process_email_section(section):
        # Extract trigger and email_key
        trigger_match = re.match(r'(.*?)\s*{', section, re.DOTALL)
        trigger = trigger_match.group(1).strip() if trigger_match else ""
        # Remove trailing dots from the trigger
        trigger = re.sub(r'(\s*\.*\s*)$', '', trigger)

        # Extract the JSON part
        json_part_match = re.search(r'{(.*?)}', section, re.DOTALL)
        json_part = json_part_match.group(1).strip() if json_part_match else ""

        # Fix the JSON part
        json_part = json_part.replace('\n', '').replace('\r', '')

        # Parse the JSON part
        try:
            email_data = json.loads(f"{{{json_part}}}")
        except json.JSONDecodeError:
            debug_file.write(f"Failed to parse JSON for section: {section}\n")
            return None

        email_key = email_data.get('emailKey', '')

        # Extract email body
        email_body_match = re.search(r'"emailBody":\s*"(.*?)"', section, re.DOTALL)
        email_body = email_body_match.group(1) if email_body_match else ""

        # Replace placeholders and new lines
        email_body = email_body.replace('\\n', '<br>').replace('$playerName', '[PLAYER]')

        # Extract NPC name after replacements
        npc_name_match = re.search(r'<br>-(.*?)$', email_body, re.DOTALL)
        npc_name = npc_name_match.group(1).strip() if npc_name_match else ""

        # Remove the NPC name from the email body
        email_body = re.sub(r'<br>-' + re.escape(npc_name), '', email_body)

        # Extract items attached to the email using email_key
        items = email_assets.get(email_key, [])
        gift = '; '.join([f"{item_name}*{amount}" for item_name, amount in items]) if items else ''

        # Debugging
        debug_file.write(f"Processing email_key: {email_key}, trigger: {trigger}, npc: {npc_name}, items: {items}\n")

        # Create the formatted email
        formatted_email = f"{{{{Mail|collapse=true|trigger={trigger}\n|npc={npc_name}\n|subject={email_data.get('emailSubject', '')}\n|gift={gift}\n|emailBody={email_body} }}}}"
        return formatted_email

    # Process each section and collect formatted emails
    formatted_emails = [process_email_section(section) for section in email_sections if process_email_section(section)]

    # Join all formatted emails into a single string
    output_content = "\n\n".join(formatted_emails)

    return output_content

# Define the input and output file paths
input_file_path = 'Input/Assets/TextAsset/English_Emails.txt'
output_file_path = 'Output/Emails/parsed_emails.txt'
guid_directory = 'Input/Assets/MonoBehaviour'
debug_output_path = '.hidden/debug_output/email_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Open the debug file for writing
with open(debug_output_path, 'w') as debug_file:
    # Load GUID to item mapping
    guid_to_item = load_guid_to_item_mapping(guid_directory, debug_file)
    debug_file.write(f"GUID to Item Mapping: {guid_to_item}\n")

    # Load email assets
    email_assets = parse_email_assets(guid_directory, guid_to_item, debug_file)
    debug_file.write(f"Email Assets Mapping: {email_assets}\n")

    # Parse the emails and get the formatted content
    parsed_content = parse_emails(input_file_path, guid_to_item, email_assets, debug_file)

    # Write the output to a new file
    with open(output_file_path, 'w') as output_file:
        output_file.write(parsed_content)

print(f"Parsed emails have been written to {output_file_path}")
print(f"Debug information has been written to {debug_output_path}")
