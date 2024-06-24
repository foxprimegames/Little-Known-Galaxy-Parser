import os
import re
import json

def load_guid_mapping(mapping_file_path):
    """
    Loads the GUID mapping from the specified JSON file.

    Args:
        mapping_file_path (str): The path to the GUID mapping file.

    Returns:
        list: A list of dictionaries mapping GUIDs to their corresponding information.
    """
    with open(mapping_file_path, 'r') as file:
        guid_mapping = json.load(file)
    return guid_mapping

def extract_price_and_restoration_info(directory, guid_mapping, sell_output_file_path, no_sell_output_file_path, debug_file_path):
    """
    Extracts price and restoration information from .asset files in the specified directory,
    combining information for normal, super, radiated, and super radiated versions of items.

    Args:
        directory (str): The path to the directory containing .asset files.
        guid_mapping (list): A list of dictionaries mapping GUIDs to their corresponding information.
        sell_output_file_path (str): The path to the file where the extracted information for sellable items will be written.
        no_sell_output_file_path (str): The path to the file where the extracted information for non-sellable items will be written.
        debug_file_path (str): The path to the file where debug information will be written.

    Returns:
        None
    """
    extracted_info = {}

    for filename in os.listdir(directory):
        if filename.endswith(".asset"):
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()

                save_id_match = re.search(r'saveID:\s*(\w+)', data)
                if save_id_match and "item" in save_id_match.group(1):
                    save_id = save_id_match.group(1).strip()
                    item_info = next((entry for entry in guid_mapping if entry.get('save_id') == save_id), {})
                    item_name = item_info.get('name', 'unknown')
                    item_category = item_info.get('category', 'unknown')
                    if item_category in ["Craft", "3D schematics"]:
                        continue  # Skip items with itemCategory = Craft or 3D schematics
                    buy_value = int(re.search(r'buyValue:\s*(\d+)', data).group(1)) if re.search(r'buyValue:\s*(\d+)', data) else 0
                    sell_value = int(re.search(r'sellValue:\s*(-?\d+)', data).group(1)) if re.search(r'sellValue:\s*(-?\d+)', data) else 0
                    health_gain = int(re.search(r'healthGain:\s*(\d+)', data).group(1)) if re.search(r'healthGain:\s*(\d+)', data) else 0
                    energy_gain = int(re.search(r'energyGain:\s*(\d+)', data).group(1)) if re.search(r'energyGain:\s*(\d+)', data) else 0

                    base_item_name = re.sub(r'(_super_rad|_super|_rad)$', '', filename.replace('.asset', ''))

                    if base_item_name not in extracted_info:
                        extracted_info[base_item_name] = {
                            "normal": {},
                            "super": {},
                            "radiated": {},
                            "super_radiated": {}
                        }

                    if '_super_rad' in filename:
                        extracted_info[base_item_name]["super_radiated"] = {
                            "sell_value": sell_value,
                            "health_gain": health_gain,
                            "energy_gain": energy_gain
                        }
                    elif '_super' in filename:
                        extracted_info[base_item_name]["super"] = {
                            "sell_value": sell_value,
                            "health_gain": health_gain,
                            "energy_gain": energy_gain
                        }
                    elif '_rad' in filename:
                        extracted_info[base_item_name]["radiated"] = {
                            "item_name": item_name,
                            "item_type": item_category,
                            "sell_value": sell_value,
                            "health_gain": health_gain,
                            "energy_gain": energy_gain
                        }
                    else:
                        extracted_info[base_item_name]["normal"] = {
                            "item_name": item_name,
                            "item_type": item_category,
                            "buy_value": buy_value,
                            "sell_value": sell_value,
                            "health_gain": health_gain,
                            "energy_gain": energy_gain
                        }

    with open(debug_file_path, 'w') as debug_file:
        for item, info in sorted(extracted_info.items(), key=lambda x: x[1]["normal"].get("item_name", "unknown_item")):
            debug_file.write(f"Extracted for {item}: {info}\n")

    with open(sell_output_file_path, 'w') as sell_output_file, open(no_sell_output_file_path, 'w') as no_sell_output_file:
        for item, info in sorted(extracted_info.items(), key=lambda x: x[1]["normal"].get("item_name", "unknown_item")):
            # Normal and Super versions
            normal = info.get("normal", {})
            super_info = info.get("super", {})
            item_name = normal.get("item_name", "unknown_item")
            item_type = normal.get("item_type", "unknown")
            sell_value = normal.get("sell_value", 0)
            health_gain = normal.get("health_gain", 0)
            energy_gain = normal.get("energy_gain", 0)
            sell_super = super_info.get("sell_value", '')
            health_gain_s = super_info.get("health_gain", 0)
            energy_gain_s = super_info.get("energy_gain", 0)

            if item_type in ['Accessory', 'Hair', 'Hat', 'Pants', 'Shirt']:
                item_type_str = f"|itemType    = Clothing\n|subType     = {item_type}"
            else:
                item_type_str = f"|itemType    = {item_type}"

            output_file = no_sell_output_file if sell_value == -1 else sell_output_file

            output_file.write(f"# {item_name}\n")
            output_file.write("{{infobox\n")
            if sell_value == -1:
                output_file.write("|sellValue   = <!-- this item cannot be sold, leave blank -->\n")
            else:
                output_file.write(f"|sellValue   = {sell_value}\n")
            if sell_super:
                output_file.write(f"|sellSuper   = {sell_super}\n")
            output_file.write(f"{item_type_str}\n")
            output_file.write(f"|energyGain  = {energy_gain}\n")
            output_file.write(f"|healthGain  = {health_gain}\n")
            if energy_gain_s or health_gain_s:
                output_file.write(f"|energyGainS = {energy_gain_s}\n")
                output_file.write(f"|healthGainS = {health_gain_s}\n")
            output_file.write("}}\n\n")

            # Radiated and Super Radiated versions
            radiated = info.get("radiated", {})
            super_radiated = info.get("super_radiated", {})
            item_name_rad = radiated.get("item_name", "unknown_item")
            item_type_rad = radiated.get("item_type", "unknown")
            sell_value_rad = radiated.get("sell_value", 0)
            health_gain_rad = radiated.get("health_gain", 0)
            energy_gain_rad = radiated.get("energy_gain", 0)
            sell_super_rad = super_radiated.get("sell_value", '')
            health_gain_sr = super_radiated.get("health_gain", 0)
            energy_gain_sr = super_radiated.get("energy_gain", 0)

            if item_type_rad in ['Accessory', 'Hair', 'Hat', 'Pants', 'Shirt']:
                item_type_rad_str = f"|itemType    = Clothing\n|subType     = {item_type_rad}"
            else:
                item_type_rad_str = f"|itemType    = {item_type_rad}"

            if radiated:
                output_file = no_sell_output_file if sell_value_rad == -1 else sell_output_file

                output_file.write(f"# {item_name_rad}\n")
                output_file.write("{{infobox\n")
                if sell_value_rad == -1:
                    output_file.write("|sellValue   = <!-- this item cannot be sold, leave blank -->\n")
                else:
                    output_file.write(f"|sellValue   = {sell_value_rad}\n")
                if sell_super_rad:
                    output_file.write(f"|sellSuper   = {sell_super_rad}\n")
                output_file.write(f"{item_type_rad_str}\n")
                output_file.write(f"|energyGain  = {energy_gain_rad}\n")
                output_file.write(f"|healthGain  = {health_gain_rad}\n")
                if energy_gain_sr or health_gain_sr:
                    output_file.write(f"|energyGainS = {energy_gain_sr}\n")
                    output_file.write(f"|healthGainS = {health_gain_sr}\n")
                output_file.write("}}\n\n")

# Define the input and output file paths
input_directory = 'Input/Assets/MonoBehaviour'
mapping_file_path = 'Output/guid_lookup.json'
sell_output_file_path = 'Output/Infobox/infobox.txt'
no_sell_output_file_path = 'Output/Infobox/infobox_no_sell.txt'
debug_file_path = '.hidden/debug_output/price_restoration_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(sell_output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(no_sell_output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_file_path), exist_ok=True)

# Load the GUID mapping
guid_mapping = load_guid_mapping(mapping_file_path)

# Extract the price and restoration information
extract_price_and_restoration_info(input_directory, guid_mapping, sell_output_file_path, no_sell_output_file_path, debug_file_path)

print(f"Price and restoration information has been written to {sell_output_file_path} and {no_sell_output_file_path}")
print(f"Debug information has been written to {debug_file_path}")
