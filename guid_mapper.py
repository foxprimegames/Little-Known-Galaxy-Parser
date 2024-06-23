import os
import re

def load_guid_to_item_mapping(directory, debug_file):
    """
    Loads the GUID to item mapping from .meta files in the specified directory
    and extracts item names from the corresponding asset files.

    Args:
        directory (str): The path to the directory containing .meta and .asset files.
        debug_file (file object): The file object to write debug information to.

    Returns:
        dict: A dictionary mapping GUIDs (str) to item names (str).
    """
    guid_to_item = {}
    item_name_mapping = {}

    # First, map GUIDs to file names
    for filename in os.listdir(directory):
        if filename.endswith(".asset.meta"):
            base_name = filename.replace('.asset.meta', '')
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                guid_match = re.search(r'guid: ([a-f0-9]{32})', data)
                if guid_match:
                    guid = guid_match.group(1)
                    guid_to_item[guid] = base_name
                    debug_file.write(f"Mapped GUID {guid} to file {base_name}\n")

    # Then, map file names to item names
    for filename in os.listdir(directory):
        if filename.endswith(".asset"):
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                item_name_match = re.search(r'itemName:\s*(.*)', data)
                if item_name_match:
                    item_name = item_name_match.group(1).strip()
                    # Only capitalize the first letter
                    item_name = item_name[0].upper() + item_name[1:].lower()
                    item_name_mapping[filename.replace('.asset', '')] = item_name
                    debug_file.write(f"Mapped file {filename} to item name {item_name}\n")

    # Combine the two mappings
    for guid, base_name in guid_to_item.items():
        if base_name in item_name_mapping:
            guid_to_item[guid] = item_name_mapping[base_name]
        else:
            guid_to_item[guid] = base_name  # Fallback to the base name

    return guid_to_item
