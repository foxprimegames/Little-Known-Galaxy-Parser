import os
import re
import fnmatch

# Function to parse a single NPC file
def parse_npc_file(data, debug_file):
    npc_name = None
    dialogues = []
    current_dialogue = None
    in_section = False
    in_dialogue = False
    text_set = None

    lines = data.splitlines()
    last_text_line = None

    for i, line in enumerate(lines):
        # Extract NPC name
        if '"name":' in line:
            npc_name_match = re.search(r'"name":\s*"([^"]+)"', line)
            if npc_name_match:
                npc_name = npc_name_match.group(1)
                debug_file.write(f"NPC Name: {npc_name}\n")

        # Identify and replace the specific initial section with formatted text
        if '"dialogue": [' in line and i + 1 < len(lines) and '#region RESTING' in lines[i + 1]:
            current_dialogue = {"section": "===Resting===", "lines": []}
            dialogues.append(current_dialogue)
            debug_file.write("Replacing dialogue and region resting with formatted text\n")
            in_section = True
            continue

        # Check for end of the section
        if in_section and '//#endregion' in line:
            in_section = False
            debug_file.write("Exiting section\n")
            continue

        # Look for the next region name
        if not in_section and '#region' in line:
            region_name_match = re.search(r'#region\s+([^\s]+)', line)
            if region_name_match:
                region_name = region_name_match.group(1).strip()
                formatted_region = f"==={region_name.replace('_', ' ').lower().capitalize()}==="
                formatted_region = re.sub(r'\s+', ' ', formatted_region)  # Remove extra whitespace
                current_dialogue = {"section": formatted_region, "lines": []}
                dialogues.append(current_dialogue)
                debug_file.write(f"Entering section: {formatted_region}\n")
                in_section = True
                continue

        # Extract dialogues within the specified section
        if in_section and '"textSet":' in line:
            in_dialogue = True
            text_set = []
            continue

        if in_dialogue:
            text_match = re.search(r'"text":\s*"([^"]+)"', line)
            expression_match = re.search(r'"expression":\s*"([^"]+)"', line)

            if text_match:
                dialogue_line = {"text": text_match.group(1)}
                debug_file.write(f"Found text: {dialogue_line['text']}\n")
                last_text_line = dialogue_line
                text_set.append(last_text_line)

            if expression_match:
                if last_text_line is not None:
                    last_text_line["emote"] = expression_match.group(1)
                    debug_file.write(f"Found emote: {last_text_line['emote']} for line: {last_text_line['text']}\n")

            # End of textSet
            if ']' in line:
                if text_set:
                    current_dialogue["lines"].append(text_set)
                    debug_file.write(f"Captured dialogue set\n")
                text_set = None  # Reset text_set
                last_text_line = None
                in_dialogue = False

    return npc_name, dialogues

# Function to format dialogues
def format_dialogues(npc_name, dialogues):
    formatted_dialogues = []

    for dialogue in dialogues:
        if "section" in dialogue:
            formatted_dialogues.append(dialogue["section"])
        if dialogue["lines"]:
            for line_set in dialogue["lines"]:
                formatted_line = f"{{{{Dialogue|npc={npc_name}"
                for i, line in enumerate(line_set):
                    formatted_line += f"|{line['text']}"
                    if "emote" in line:
                        if i == 0:
                            formatted_line += f"|emote={line['emote']}"
                        else:
                            formatted_line += f"|emote{i+1}={line['emote']}"
                formatted_line += "}}"
                formatted_dialogues.append(formatted_line)

    return formatted_dialogues

# Main script to process files in the input folder
input_folder = "Input/Assets/TextAsset"
output_folder = "Output/Dialogues"

# Ensure output folder exists
os.makedirs(output_folder, exist_ok=True)

# List of patterns to ignore
ignore_patterns = [
    "*Achievements*",
    "*Animals*",
    "*Collections*",
    "*Emails*",
    "*Events*",
    "*General*",
    "*Items*",
    "*Locations*",
    "*Quests*",
    "*UI*",
    "*Upgrades*",
    "*TBD*"
]

for filename in os.listdir(input_folder):
    if any(fnmatch.fnmatch(filename, pattern) for pattern in ignore_patterns):
        continue  # Skip processing this file

    if filename.endswith(".txt"):
        input_filepath = os.path.join(input_folder, filename)
        
        # Read the file with UTF-8 encoding
        with open(input_filepath, 'r', encoding='utf-8') as file:
            data = file.read()

        # Parse the content and write debug info to a file with UTF-8 encoding
        debug_output_path = 'debug_output.txt'
        with open(debug_output_path, 'w', encoding='utf-8') as debug_file:
            npc_name, dialogues = parse_npc_file(data, debug_file)

        # Format the dialogues
        formatted_dialogues = format_dialogues(npc_name, dialogues)

        # Write the output to a file named after the NPC with _Dialogue appended
        output_filename = f"{npc_name}_Dialogue.txt"
        output_filepath = os.path.join(output_folder, output_filename)
        with open(output_filepath, 'w', encoding='utf-8') as output_file:
            for line in formatted_dialogues:
                output_file.write(line + '\n')
