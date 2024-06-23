import os
import re

def load_guid_to_item_mapping(directory, debug_file):
    """
    Loads the GUID to item mapping from .meta files in the specified directory.

    Args:
        directory (str): The path to the directory containing .meta files.
        debug_file (file object): The file object to write debug information to.

    Returns:
        dict: A dictionary mapping GUIDs (str) to item names (str).
    """
    guid_to_item = {}
    for filename in os.listdir(directory):
        if filename.endswith(".asset.meta"):
            base_name = filename.replace('.asset.meta', '')
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                guid_match = re.search(r'guid: ([a-f0-9]{32})', data)
                if guid_match:
                    guid = guid_match.group(1)
                    guid_to_item[guid] = base_name
                    debug_file.write(f"Mapped GUID {guid} to item {base_name}\n")
                else:
                    debug_file.write(f"No GUID found in {filename}\n")
    return guid_to_item
