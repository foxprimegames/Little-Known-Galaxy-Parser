import os
import re

def parse_email_assets(directory, guid_to_item, debug_file):
    """
    Parses the .asset files in the given directory to extract item information for each saveID.

    Args:
        directory (str): The path to the directory containing .asset files.
        guid_to_item (dict): A dictionary mapping GUIDs to item names.
        debug_file (file object): The file object to write debug information to.

    Returns:
        dict: A dictionary mapping saveIDs (str) to a list of tuples containing (item_name, amount).
    """
    email_assets = {}
    for filename in os.listdir(directory):
        if filename.endswith(".asset") and "email" in filename.lower():
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                debug_file.write(f"\nProcessing file: {filename}\n{data}\n")
                save_id_match = re.search(r'saveID: (\w+)', data)
                if save_id_match:
                    save_id = save_id_match.group(1)
                    items = []
                    # Extract itemsToAttach section
                    items_section_match = re.search(r'itemsToAttach:\n(.*?)(\n[a-zA-Z]|$)', data, re.DOTALL)
                    if items_section_match:
                        items_section = items_section_match.group(1)
                        # Extract GUIDs and amounts from the itemsToAttach section
                        items_match = re.findall(r'guid: ([a-f0-9]{32}).*?amountOfItem: (\d+)', items_section, re.DOTALL)
                        for guid, amount in items_match:
                            item_name = guid_to_item.get(guid, 'unknown_item')
                            debug_file.write(f"Item: {item_name} (GUID: {guid}), Amount: {amount}\n")
                            items.append((item_name, amount))
                    email_assets[save_id] = items
                    debug_file.write(f"Processed {filename}: saveID={save_id}, items={items}\n")
                else:
                    debug_file.write(f"Warning: saveID not found in {filename}\n")
    return email_assets
