import os
import re
import fnmatch

# Function to parse a single NPC file
def parse_npc_file(data, debug_file):
    npc_name = None
    dialogues = []
    current_section = None
    in_section = False
    text_set = None

    lines = data.splitlines()
    last_text_line = None

    for line in lines:
        # Extract NPC name
        if '"name":' in line:
            npc_name_match = re.search(r'"name":\s*"([^"]+)"', line)
            if npc_name_match:
                npc_name = npc_name_match.group(1)
                debug_file.write(f"NPC Name: {npc_name}\n")

        # Check for region start
        region_start_match = re.search(r'#region\s*(.+?)\s*\.*', line)
        if region_start_match:
            in_section = True
            current_section = region_start_match.group(1).strip()
            debug_file.write(f"Entering section: {current_section}\n")

        # Check for region end
        if "#endregion" in line:
            in_section = False
            debug_file.write(f"Exiting section: {current_section}\n")
            current_section = None

        # Extract dialogues within a section
        if in_section and '"textSet"' in line:
            text_set = []
            continue

        if in_section and text_set is not None:
            text_match = re.search(r'"text":\s*"([^"]+)"', line)
            expression_match = re.search(r'"expression":\s*"([^"]+)"', line)

            if text_match:
                if last_text_line is not None:
                    text_set.append(last_text_line)
                dialogue_line = {"text": text_match.group(1)}
                debug_file.write(f"Found text: {dialogue_line['text']}\n")
                last_text_line = dialogue_line

            if expression_match:
                if last_text_line is not None:
                    last_text_line["emote"] = expression_match.group(1)
                    debug_file.write(f"Found emote: {last_text_line['emote']} for line: {last_text_line['text']}\n")
                else:
                    pending_expression = expression_match.group(1)
                    debug_file.write(f"Emote found without preceding text line: {pending_expression}\n")

            # End of textSet
            if ']' in line:
                if last_text_line is not None:
                    text_set.append(last_text_line)
                dialogues.append({"section": current_section, "lines": text_set})
                debug_file.write(f"Captured dialogue set in section: {current_section}\n")
                text_set = None  # Reset text_set
                last_text_line = None

    return npc_name, dialogues

# Function to format dialogues
def format_dialogues(npc_name, dialogues):
    formatted_dialogues = {}
    section_names_map = {
        "S": "Stranger",
        "A": "Acquaintance",
        "F": "Friend",
        "G": "Good Friend",
        "B": "Best Friend",
        "E": "Engaged",
        "M": "Married"
    }

    for dialogue in dialogues:
        section = dialogue["section"]
        formatted_section = section_names_map.get(section, section)  # Use mapped section name if available

        if formatted_section not in formatted_dialogues:
            formatted_dialogues[formatted_section] = []
        
        formatted_line = f"{{{{Dialogue|npc={npc_name}"
        for i, line in enumerate(dialogue["lines"]):
            formatted_line += f"|{line['text']}"
            if "emote" in line:
                if i == 0:
                    formatted_line += f"|emote={line['emote']}"
                else:
                    formatted_line += f"|emote{i+1}={line['emote']}"
        formatted_line += "}}"
        
        formatted_dialogues[formatted_section].append(formatted_line)
    
    return formatted_dialogues

# Main script to process all files in Input/TextAsset folder
input_folder = "Input/TextAsset"
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
        with open('debug_output.txt', 'w', encoding='utf-8') as debug_file:
            npc_name, dialogues = parse_npc_file(data, debug_file)

        # Format the dialogues
        formatted_dialogues = format_dialogues(npc_name, dialogues)

        # Write the output to a file named after the NPC with _Dialogue appended
        output_filename = f"{npc_name}_Dialogue.txt"
        output_filepath = os.path.join(output_folder, output_filename)
        with open(output_filepath, 'w', encoding='utf-8') as output_file:
            for section, lines in formatted_dialogues.items():
                # Ensure proper case and formatting of section header
                proper_case_section = ' '.join(word.capitalize() for word in section.split())
                output_file.write(f"=== {proper_case_section} ===\n")
                for line in lines:
                    output_file.write(line + '\n')
