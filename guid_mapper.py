import os
import re

def load_guid_to_item_mapping(directory, debug_file):
    """
    Loads the GUID to item mapping from .meta files in the specified directory
    and extracts item names or m_Name from the corresponding asset files.

    Args:
        directory (str): The path to the directory containing .meta and .asset files.
        debug_file (file object): The file object to write debug information to.

    Returns:
        dict: A dictionary mapping GUIDs to their corresponding information.
    """
    guid_mapping = {}

    # First, map GUIDs to file names
    for filename in os.listdir(directory):
        if filename.endswith(".asset.meta"):
            base_name = filename.replace('.asset.meta', '')
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                guid_match = re.search(r'guid: ([a-f0-9]{32})', data)
                if guid_match:
                    guid = guid_match.group(1)
                    guid_mapping[guid] = {'filename': base_name}
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
                    for guid, info in guid_mapping.items():
                        if info['filename'] == base_name:
                            guid_mapping[guid]['save_id'] = save_id
                            guid_mapping[guid]['name'] = item_name if item_name else m_name
                            guid_mapping[guid]['category'] = item_category
                            debug_file.write(f"File {filename}: saveID={save_id}, name={guid_mapping[guid]['name']}, category={item_category}\n")
                else:
                    debug_file.write(f"File {filename}: No saveID found.\n")
    return guid_mapping

# Define the input and output file paths
input_directory = 'Input/Assets/MonoBehaviour'
output_file_path = 'Output/guid_lookup.txt'
debug_output_path = '.hidden/debug_output/guid_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Open the debug file for writing
with open(debug_output_path, 'w') as debug_file:
    guid_mapping = load_guid_to_item_mapping(input_directory, debug_file)
    with open(output_file_path, 'w') as output_file:
        for guid, info in guid_mapping.items():
            output_file.write(f"{guid},{info['filename']},{info.get('save_id', 'unknown')},{info.get('name', 'unknown')}\n")
    print(f"GUID mapping has been written to {output_file_path}")
    print(f"Debug information has been written to {debug_output_path}")
