import json
import re
import os

def parse_emails(file_path):
    # Read the content of the file
    with open(file_path, 'r') as file:
        data = file.read()

    # Split the data by each email to handle it in parts
    email_sections = data.split('//EMAIL_')[1:]

    # Function to process a single email section
    def process_email_section(section):
        # Extract trigger
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
            return None

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

        # Create the formatted email
        formatted_email = f"{{{{Mail|collapse=true|trigger={trigger}\n|npc={npc_name}\n|subject={email_data.get('emailSubject', '')}\n|gift=\n|emailBody={email_body} }}}}"
        return formatted_email

    # Process each section and collect formatted emails
    formatted_emails = [process_email_section(section) for section in email_sections if process_email_section(section)]

    # Join all formatted emails into a single string
    output_content = "\n\n".join(formatted_emails)

    return output_content

# Define the input and output file paths
input_file_path = 'Input/TextAsset/English_Emails.txt'
output_file_path = 'Output/Emails/parsed_emails.txt'

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Parse the emails and get the formatted content
parsed_content = parse_emails(input_file_path)

# Write the output to a new file
with open(output_file_path, 'w') as output_file:
    output_file.write(parsed_content)

print(f"Parsed emails have been written to {output_file_path}")
