import os
import re
import yaml
import math
import json

# Define paths
input_folder = 'Input/Assets/MonoBehaviour'
output_folder = 'Output/Shops'
guid_lookup_file = 'Output/guid_lookup.json'
debug_output_file = '.hidden/debug_output/shop_debug_output.txt'

# Ensure output directories exist
os.makedirs(output_folder, exist_ok=True)
os.makedirs(os.path.dirname(debug_output_file), exist_ok=True)

# Initialize debug log
with open(debug_output_file, 'w') as debug_log:
    debug_log.write("Debugging Information:\n")

# Function to remove custom Unity tags from YAML content
def preprocess_yaml_content(content):
    return re.sub(r'!u![\d]+ &[\d]+', '', content)

# Function to load GUID to filename and item name mappings
def load_guid_lookup(guid_lookup_file):
    with open(guid_lookup_file, 'r') as file:
        guid_mapping = json.load(file)
    return guid_mapping

# Load the GUID mappings
guid_mapping = load_guid_lookup(guid_lookup_file)

# Process each file in the input folder
for filename in os.listdir(input_folder):
    if filename.startswith('_StoreCatalog') and not filename.endswith('.meta'):
        # Read the file
        file_path = os.path.join(input_folder, filename)
        try:
            with open(file_path, 'r') as file:
                raw_content = file.read()
                clean_content = preprocess_yaml_content(raw_content)
                data = yaml.safe_load(clean_content)
            
            # Extract the store name, removing the '_StoreCatalog' part
            store_name = data.get('MonoBehaviour', {}).get('m_Name', '').replace('_StoreCatalog', '')
            if not store_name:
                raise ValueError("Store name not found in the file.")
                
            markup_percent = float(data.get('MonoBehaviour', {}).get('markupPercent', 1))
            store_sets = data.get('MonoBehaviour', {}).get('storeSets', [])
            
            # Process each store set
            store_sets_details = []
            for store_set in store_sets:
                guid = store_set.get('guid')
                if guid:
                    store_set_detail = next((entry for entry in guid_mapping if entry['guid'] == guid), None)
                    if store_set_detail:
                        store_set_filename = store_set_detail['filename']
                        store_set_path = os.path.join(input_folder, store_set_filename + '.asset')
                        if not os.path.exists(store_set_path):
                            with open(debug_output_file, 'a') as debug_log:
                                debug_log.write(f"Store set file not found: {store_set_path}\n")
                            continue
                        with open(store_set_path, 'r') as store_set_file:
                            store_set_content = store_set_file.read()
                            store_set_data = yaml.safe_load(preprocess_yaml_content(store_set_content))
                            store_set_detail.update({
                                'rndRollActive': store_set_data.get('MonoBehaviour', {}).get('rndRollActive', False),
                                'rndRollAmount': store_set_data.get('MonoBehaviour', {}).get('rndRollAmount', 'N/A'),
                                'storeItemsInSet': store_set_data.get('MonoBehaviour', {}).get('storeItemsInSet', [])
                            })
                            store_sets_details.append(store_set_detail)
            
            # Prepare the output
            output_file_path = os.path.join(output_folder, f'{store_name}.txt')
            with open(output_file_path, 'w') as output_file:
                output_file.write(f"Store Name: {store_name}\n")
                output_file.write(f"Markup Percent: {markup_percent}\n")
                for store_set_detail in store_sets_details:
                    if store_set_detail['rndRollActive']:
                        output_file.write(f"\nStore Set: {store_set_detail['filename']} - Roll Amount: {store_set_detail['rndRollAmount']}\n")
                    else:
                        output_file.write(f"\nStore Set: {store_set_detail['filename']}\n")
                    for item in store_set_detail['storeItemsInSet']:
                        item_guid = item.get('guid', 'unknown')
                        item_detail = next((entry for entry in guid_mapping if entry['guid'] == item_guid), None)
                        if item_detail:
                            item_filename = item_detail['filename']
                            item_path = os.path.join(input_folder, item_filename + '.asset')
                            if not os.path.exists(item_path):
                                with open(debug_output_file, 'a') as debug_log:
                                    debug_log.write(f"Item file not found: {item_path}\n")
                                continue
                            with open(item_path, 'r') as item_file:
                                item_content = item_file.read()
                                item_data = yaml.safe_load(preprocess_yaml_content(item_content))
                                item_for_sale_guid = item_data.get('MonoBehaviour', {}).get('itemForSale', {}).get('guid', 'unknown')
                                limited_purchase = item_data.get('MonoBehaviour', {}).get('limitedPurchase', 0)
                                item_for_sale_detail = next((entry for entry in guid_mapping if entry['guid'] == item_for_sale_guid), None)
                                if item_for_sale_detail:
                                    item_for_sale_filename = item_for_sale_detail['filename']
                                    item_for_sale_path = os.path.join(input_folder, item_for_sale_filename + '.asset')
                                    if not os.path.exists(item_for_sale_path):
                                        with open(debug_output_file, 'a') as debug_log:
                                            debug_log.write(f"Item for sale file not found: {item_for_sale_path}\n")
                                        continue
                                    with open(item_for_sale_path, 'r') as item_for_sale_file:
                                        item_for_sale_content = item_for_sale_file.read()
                                        item_for_sale_data = yaml.safe_load(preprocess_yaml_content(item_for_sale_content))
                                        buy_value = float(item_for_sale_data.get('MonoBehaviour', {}).get('buyValue', 0))
                                        item_name = item_for_sale_detail['name'].capitalize()
                                        sell_price = math.ceil(buy_value * markup_percent)
                                        output_line = f"{{{{shop|{item_name}|{sell_price}"
                                        if limited_purchase == 1:
                                            output_line += "|note = limited quantity item. The player can only purchase one."
                                        output_line += "}}\n"
                                        output_file.write(output_line)
            
            # Log debugging information
            with open(debug_output_file, 'a') as debug_log:
                debug_log.write(f"Processed file: {filename}\n")
                debug_log.write(f"Store Name: {store_name}\n")
                debug_log.write(f"Markup Percent: {markup_percent}\n")
                for store_set_detail in store_sets_details:
                    if store_set_detail['rndRollActive']:
                        debug_log.write(f"\nStore Set: [{store_set_detail['guid']}] - {store_set_detail['filename']} - Roll Amount: {store_set_detail['rndRollAmount']}\n")
                    else:
                        debug_log.write(f"\nStore Set: [{store_set_detail['guid']}] - {store_set_detail['filename']}\n")
                    for item in store_set_detail['storeItemsInSet']:
                        item_guid = item.get('guid', 'unknown')
                        item_detail = next((entry for entry in guid_mapping if entry['guid'] == item_guid), None)
                        if item_detail:
                            item_filename = item_detail['filename']
                            item_path = os.path.join(input_folder, item_filename + '.asset')
                            if not os.path.exists(item_path):
                                debug_log.write(f"Item file not found: {item_path}\n")
                                continue
                            with open(item_path, 'r') as item_file:
                                item_content = item_file.read()
                                item_data = yaml.safe_load(preprocess_yaml_content(item_content))
                                item_for_sale_guid = item_data.get('MonoBehaviour', {}).get('itemForSale', {}).get('guid', 'unknown')
                                limited_purchase = item_data.get('MonoBehaviour', {}).get('limitedPurchase', 0)
                                item_for_sale_detail = next((entry for entry in guid_mapping if entry['guid'] == item_for_sale_guid), None)
                                if item_for_sale_detail:
                                    item_for_sale_filename = item_for_sale_detail['filename']
                                    item_for_sale_path = os.path.join(input_folder, item_for_sale_filename + '.asset')
                                    if not os.path.exists(item_for_sale_path):
                                        debug_log.write(f"Item for sale file not found: {item_for_sale_path}\n")
                                        continue
                                    with open(item_for_sale_path, 'r') as item_for_sale_file:
                                        item_for_sale_content = item_for_sale_file.read()
                                        item_for_sale_data = yaml.safe_load(preprocess_yaml_content(item_for_sale_content))
                                        buy_value = float(item_for_sale_data.get('MonoBehaviour', {}).get('buyValue', 0))
                                        item_name = item_for_sale_detail['name'].capitalize()
                                        sell_price = math.ceil(buy_value * markup_percent)
                                        output_line = f"{{{{shop|{item_name}|{sell_price}"
                                        if limited_purchase == 1:
                                            output_line += "|note = limited quantity item. The player can only purchase one."
                                        output_line += "}}\n"
                                        debug_log.write(output_line)
                debug_log.write("\n")
        
        except yaml.YAMLError as e:
            with open(debug_output_file, 'a') as debug_log:
                debug_log.write(f"Error decoding YAML from file: {filename} - {e}\n")
        except Exception as e:
            with open(debug_output_file, 'a') as debug_log:
                debug_log.write(f"Error processing file {filename}: {e}\n")

print(f"Debug information has been written to {debug_output_file}")
print(f"Parsed shop catalogs have been written to {output_folder}")