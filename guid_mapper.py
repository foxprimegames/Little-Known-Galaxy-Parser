import os
import re
import json

def load_guid_to_item_mapping(directory, english_items_file, debug_file):
    """
    Loads the GUID to item mapping from .meta files in the specified directory
    and extracts item names or m_Name from the corresponding asset files.

    Args:
        directory (str): The path to the directory containing .meta and .asset files.
        english_items_file (str): The path to the English_Items.txt file.
        debug_file (file object): The file object to write debug information to.

    Returns:
        list: A list of dictionaries mapping GUIDs to their corresponding information.
    """
    guid_mapping = []

    # Load itemKey to itemName mappings from English_Items.txt
    item_mapping = {}
    with open(english_items_file, 'r') as file:
        content = file.read()
        matches = re.findall(r'"itemKey": "(.*?)",\s*"itemName": "(.*?)"', content)
        for itemKey, itemName in matches:
            item_mapping[itemKey] = itemName

    # First, map GUIDs to file names
    for filename in os.listdir(directory):
        if filename.endswith(".asset.meta"):
            base_name = filename.replace('.asset.meta', '')
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                guid_match = re.search(r'guid: ([a-f0-9]{32})', data)
                if guid_match:
                    guid = guid_match.group(1)
                    guid_mapping.append({"guid": guid, "filename": base_name})
                    debug_file.write(f"Mapped GUID {guid} to file {base_name}\n")

    # Then, map file names to saveIDs and item names or m_Name
    for filename in os.listdir(directory):
        if filename.endswith(".asset"):
            base_name = filename.replace('.asset', '')
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                save_id_match = re.search(r'saveID:\s*(\w+)', data)
                item_name_match = re.search(r'itemName:\s*(.*)', data)
                name_match = re.search(r'm_Name:\s*(.*)', data)
                category_match = re.search(r'itemCategory:\s*(.*)', data)
                
                save_id = save_id_match.group(1).strip() if save_id_match else None
                item_name = item_name_match.group(1).strip() if item_name_match else None
                m_name = name_match.group(1).strip() if name_match else None
                item_category = category_match.group(1).strip() if category_match else 'unknown'

                if save_id:
                    if save_id.startswith("item_"):
                        mapped_name = item_mapping.get(save_id, "").strip()
                        if not mapped_name:
                            mapped_name = m_name
                        else:
                            mapped_name = mapped_name
                    else:
                        mapped_name = item_name if item_name else m_name

                    for entry in guid_mapping:
                        if entry["filename"] == base_name:
                            entry["save_id"] = save_id
                            entry["name"] = mapped_name
                            entry["category"] = item_category
                            debug_file.write(f"File {filename}: saveID={save_id}, name={mapped_name}, category={item_category}\n")
                else:
                    debug_file.write(f"File {filename}: No saveID found.\n")
    return guid_mapping

# Define the input and output file paths
input_directory = 'Input/Assets/MonoBehaviour'
english_items_file = 'Input/Assets/TextAsset/English_Items.txt'
output_file_path = 'Output/guid_lookup.json'
debug_output_path = '.hidden/debug_output/guid_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Open the debug file for writing
with open(debug_output_path, 'w') as debug_file:
    guid_mapping = load_guid_to_item_mapping(input_directory, english_items_file, debug_file)
    with open(output_file_path, 'w') as output_file:
        json.dump(guid_mapping, output_file, indent=2)
    print(f"GUID mapping has been written to {output_file_path}")
    print(f"Debug information has been written to {debug_output_path}")
