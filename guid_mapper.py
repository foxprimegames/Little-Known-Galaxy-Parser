import os
import re

def load_guid_to_item_mapping(directory, debug_file):
    """
    Loads the GUID to item mapping from .meta files in the specified directory
    and extracts item names and item categories from the corresponding asset files.

    Args:
        directory (str): The path to the directory containing .meta and .asset files.
        debug_file (file object): The file object to write debug information to.

    Returns:
        dict: A dictionary mapping GUIDs (str) to tuples of item names (str) and item categories (str).
    """
    guid_to_item = {}
    guid_to_category = {}

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

    # Then, map file names to item names and item categories
    for filename in os.listdir(directory):
        if filename.endswith(".asset"):
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                item_name_match = re.search(r'itemName:\s*(.*)', data)
                item_category_match = re.search(r'itemCategory:\s*(\w+)', data)
                if item_name_match:
                    item_name = item_name_match.group(1).strip()
                    # Only capitalize the first letter
                    item_name = item_name[0].upper() + item_name[1:].lower()
                    guid = next((k for k, v in guid_to_item.items() if v == filename.replace('.asset', '')), None)
                    if guid:
                        guid_to_item[guid] = item_name
                    debug_file.write(f"Mapped file {filename} to item name {item_name}\n")
                if item_category_match:
                    item_category = item_category_match.group(1).strip().lower()
                    guid = next((k for k, v in guid_to_item.items() if v == filename.replace('.asset', '')), None)
                    if guid:
                        guid_to_category[guid] = item_category
                    debug_file.write(f"Mapped file {filename} to item category {item_category}\n")

    return guid_to_item, guid_to_category
