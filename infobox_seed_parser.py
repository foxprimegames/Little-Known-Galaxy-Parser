import os
import re
import json

def load_guid_mapping(mapping_file_path):
    with open(mapping_file_path, 'r') as file:
        guid_mapping = json.load(file)
    return guid_mapping

def convert_guid_to_name(guid, guid_mapping):
    for entry in guid_mapping:
        if entry.get('guid') == guid:
            return entry.get('name', 'unknown').capitalize()  # Convert to sentence case
    return 'Unknown'

def extract_seed_data(data, guid_mapping):
    seed_info = {}
    seed_info["planet"] = re.search(r'planet:\s*(\w+)', data).group(1).capitalize() if re.search(r'planet:\s*(\w+)', data) else ''
    
    produces_items = re.findall(r'itemToDrop:\s*\{[^}]*guid:\s*([\w\d]+)', data)
    produces_names = [convert_guid_to_name(guid, guid_mapping) for guid in produces_items]
    
    # Filter out "super" versions
    filtered_produces = [name for name in produces_names if "Super " not in name]

    seed_info["produces"] = filtered_produces
    seed_info["produceDuration"] = re.search(r'produceDuration:\s*(\d+)', data).group(1) if re.search(r'produceDuration:\s*(\d+)', data) else ''
    seed_info["maxProductionCycles"] = re.search(r'maxProductionCycles:\s*(\d+)', data).group(1) if re.search(r'maxProductionCycles:\s*(\d+)', data) else ''
    pick_amount = int(re.search(r'pickAmount:\s*(\d+)', data).group(1)) if re.search(r'pickAmount:\s*(\d+)', data) else 0
    extra_pick_percent = float(re.search(r'extraPickPercent:\s*([\d.]+)', data).group(1)) if re.search(r'extraPickPercent:\s*([\d.]+)', data) else 0
    seed_info["cropYield"] = pick_amount + extra_pick_percent
    seed_info["produceDurationAfterMature"] = re.search(r'produceDurationAfterMature:\s*(\d+)', data).group(1) if re.search(r'produceDurationAfterMature:\s*(\d+)', data) else ''
    
    sell_value_match = re.search(r'sellValue:\s*(-?\d+)', data)
    seed_info["sellValue"] = sell_value_match.group(1) if sell_value_match else ''
    
    return seed_info

def extract_seed_info(directory, guid_mapping, seed_output_file_path, debug_file_path):
    extracted_info = {}

    for filename in os.listdir(directory):
        if filename.endswith(".asset"):
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()

                save_id_match = re.search(r'saveID:\s*(\w+)', data)
                if save_id_match and "item" in save_id_match.group(1):
                    save_id = save_id_match.group(1).strip()
                    item_info = next((entry for entry in guid_mapping if entry.get('save_id') == save_id), {})
                    item_name = item_info.get('name', 'unknown').capitalize()
                    item_category = item_info.get('category', 'unknown').capitalize()
                    if item_category not in ["Seeds", "Tree seeds"]:
                        continue  # Skip non-seed items

                    item_type = int(re.search(r'itemType:\s*(\d+)', data).group(1)) if re.search(r'itemType:\s*(\d+)', data) else 0
                    seed_info = extract_seed_data(data, guid_mapping)

                    base_item_name = filename.replace('.asset', '')
                    extracted_info[base_item_name] = {
                        "item_name": item_name,
                        "item_category": "Tree seed" if item_category == "Tree seeds" else "Seed",
                        "item_type": item_type,
                        "seed_info": seed_info
                    }

    with open(debug_file_path, 'w') as debug_file:
        for item, info in sorted(extracted_info.items(), key=lambda x: x[1].get("item_name", "Unknown item")):
            debug_file.write(f"Extracted for {item}: {info}\n")

    with open(seed_output_file_path, 'w') as seed_output_file:
        for item, info in sorted(extracted_info.items(), key=lambda x: x[1].get("item_name", "Unknown item")):
            item_name = info.get("item_name", "Unknown item")
            item_category = info.get("item_category", "Seed")
            item_type = info.get("item_type", 0)
            seed_info = info.get("seed_info", {})

            produces_names = '; '.join(seed_info.get('produces', []))
            sell_value = seed_info.get("sellValue", "")

            seed_output_file.write(f"# {item_name}\n")
            seed_output_file.write("{{infobox\n")
            seed_output_file.write(f"|sellValue   = {sell_value}\n")
            seed_output_file.write(f"|itemCategory = {item_category}\n")
            seed_output_file.write(f"|subCategory = \n")
            seed_output_file.write(f"|itemType    = {item_type}\n")
            seed_output_file.write(f"|planet      = {seed_info.get('planet', '')}\n")
            seed_output_file.write(f"|produces    = {produces_names}\n")
            if item_category == "Tree seed":
                seed_output_file.write(f"|treeSeed    = 1\n")
            seed_output_file.write("<!-- Growth Data -->\n")
            seed_output_file.write(f"|growth      = {seed_info.get('produceDuration', '')}\n")
            seed_output_file.write(f"|maxHarvest  = {seed_info.get('maxProductionCycles', '')}\n")
            seed_output_file.write(f"|cropYield   = {seed_info.get('cropYield', '')}\n")
            seed_output_file.write(f"|regrowth    = {seed_info.get('produceDurationAfterMature', '')}\n")
            seed_output_file.write("}}\n\n")

# Define the input and output file paths
input_directory = 'Input/Assets/MonoBehaviour'
mapping_file_path = 'Output/guid_lookup.json'
seed_output_file_path = 'Output/Infobox/seed_infobox.txt'
debug_file_path = '.hidden/debug_output/seed_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(seed_output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_file_path), exist_ok=True)

# Load the GUID mapping
guid_mapping = load_guid_mapping(mapping_file_path)

# Extract the seed information
extract_seed_info(input_directory, guid_mapping, seed_output_file_path, debug_file_path)

print(f"Seed information has been written to {seed_output_file_path}")
print(f"Debug information has been written to {debug_file_path}")
