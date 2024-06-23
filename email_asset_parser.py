import os
import re
import json

def parse_email_assets(directory, guid_to_item, debug_file):
    """
    Parses the email asset files to map saveIDs to items and their quantities.

    Args:
        directory (str): The path to the directory containing .asset files.
        guid_to_item (dict): A dictionary mapping GUIDs to item names.
        debug_file (file object): The file object to write debug information to.

    Returns:
        dict: A dictionary mapping saveIDs (email keys) to a list of tuples (item name, quantity).
    """
    email_assets = {}

    for filename in os.listdir(directory):
        if filename.startswith("Email_") and filename.endswith(".asset"):
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                debug_file.write(f"\nProcessing file: {filename}\n{data}\n")

                # Extract saveID
                save_id_match = re.search(r'saveID:\s*(\w+)', data)
                save_id = save_id_match.group(1) if save_id_match else ""

                # Extract items to attach
                items_to_attach = []
                items_section = re.search(r'itemsToAttach:\n(.*?)(\n[a-zA-Z]|$)', data, re.DOTALL)
                items = items_section.group(1) if items_section else ""
                if items:
                    materials_match = re.findall(r'itemData:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}.*?amountOfItem:\s*(\d+)', items, re.DOTALL)
                    for material_guid, amount in materials_match:
                        material_name = guid_to_item.get(material_guid, 'unknown_item')
                        items_to_attach.append((material_name, amount))
                
                email_assets[save_id] = items_to_attach
                debug_file.write(f"Mapped saveID {save_id} to items {items_to_attach}\n")
    
    return email_assets
