import os
import re
import yaml
import math

# Define paths
input_folder = 'Input/Assets/MonoBehaviour'
output_folder = 'Output/Shops'
guid_lookup_file = 'Output/guid_lookup.txt'
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
    guid_mapping = {}
    with open(guid_lookup_file, 'r') as file:
        for line in file:
            guid, filename, save_id, name = line.strip().split(',')
            guid_mapping[guid] = {'filename': filename, 'name': name}
    return guid_mapping

# Function to convert a string to sentence case
def to_sentence_case(s):
    return s.capitalize()

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
                if guid and guid in guid_mapping:
                    store_set_filename = guid_mapping[guid]['filename']
                    store_set_path = os.path.join(input_folder, store_set_filename + '.asset')
                    if not os.path.exists(store_set_path):
                        with open(debug_output_file, 'a') as debug_log:
                            debug_log.write(f"Store set file not found: {store_set_path}\n")
                        continue
                    with open(store_set_path, 'r') as store_set_file:
                        store_set_content = store_set_file.read()
                        store_set_data = yaml.safe_load(preprocess_yaml_content(store_set_content))
                        store_set_details = {
                            'guid': guid,
                            'filename': store_set_filename,
                            'rndRollActive': store_set_data.get('MonoBehaviour', {}).get('rndRollActive', False),
                            'rndRollAmount': store_set_data.get('MonoBehaviour', {}).get('rndRollAmount', 'N/A'),
                            'storeItemsInSet': store_set_data.get('MonoBehaviour', {}).get('storeItemsInSet', [])
                        }
                        store_sets_details.append(store_set_details)
                        with open(debug_output_file, 'a') as debug_log:
                            debug_log.write(f"Store set details: {store_set_details}\n")
            
            # Prepare the output
            output_file_path = os.path.join(output_folder, f'{store_name}.txt')
            with open(output_file_path, 'w') as output_file:
                output_file.write(f"Store Name: {store_name}\n")
                output_file.write(f"Markup Percent: {markup_percent}\n")
                for store_set_detail in store_sets_details:
                    if store_set_detail['rndRollActive']:
                        output_file.write(f"\nStore Set: [{store_set_detail['guid']}] - {store_set_detail['filename']} - Roll Amount: {store_set_detail['rndRollAmount']}\n")
                    else:
                        output_file.write(f"\nStore Set: [{store_set_detail['guid']}] - {store_set_detail['filename']}\n")
                    for item in store_set_detail['storeItemsInSet']:
                        item_guid = item.get('guid', 'unknown')
                        with open(debug_output_file, 'a') as debug_log:
                            debug_log.write(f"Processing item GUID: {item_guid}\n")
                        if item_guid in guid_mapping:
                            item_filename = guid_mapping[item_guid]['filename']
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
                                with open(debug_output_file, 'a') as debug_log:
                                    debug_log.write(f"Item for sale GUID: {item_for_sale_guid}, Limited purchase: {limited_purchase}\n")
                                if item_for_sale_guid in guid_mapping:
                                    item_for_sale_filename = guid_mapping[item_for_sale_guid]['filename']
                                    item_for_sale_path = os.path.join(input_folder, item_for_sale_filename + '.asset')
                                    if not os.path.exists(item_for_sale_path):
                                        with open(debug_output_file, 'a') as debug_log:
                                            debug_log.write(f"Item for sale file not found: {item_for_sale_path}\n")
                                        continue
                                    with open(item_for_sale_path, 'r') as item_for_sale_file:
                                        item_for_sale_content = item_for_sale_file.read()
                                        item_for_sale_data = yaml.safe_load(preprocess_yaml_content(item_for_sale_content))
                                        buy_value = float(item_for_sale_data.get('MonoBehaviour', {}).get('buyValue', 0))
                                        item_name = to_sentence_case(guid_mapping[item_for_sale_guid]['name'])
                                        sell_price = math.ceil(buy_value * markup_percent)
                                        output_line = f"{{{{shop|{item_name}|{sell_price}"
                                        if limited_purchase == 1:
                                            output_line += "|note = limited quantity item. The player can only purchase one."
                                        output_line += "}}\n"  # Ensure proper closing
                                        output_file.write(output_line)
                                        with open(debug_output_file, 'a') as debug_log:
                                            debug_log.write(f"Output line: {output_line}\n")
                                    with open(debug_output_file, 'a') as debug_log:
                                        debug_log.write(f"Processed item for sale file: {item_for_sale_filename}, Buy value: {buy_value}, Sell price: {sell_price}\n")
                                else:
                                    with open(debug_output_file, 'a') as debug_log:
                                        debug_log.write(f"Item for sale GUID {item_for_sale_guid} not found in guid_mapping\n")
                        else:
                            with open(debug_output_file, 'a') as debug_log:
                                debug_log.write(f"Item GUID {item_guid} not found in guid_mapping\n")
            
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
                        debug_log.write(f"Processed item GUID: {item_guid}\n")
                        if item_guid in guid_mapping:
                            item_filename = guid_mapping[item_guid]['filename']
                            item_path = os.path.join(input_folder, item_filename + '.asset')
                            if not os.path.exists(item_path):
                                debug_log.write(f"Item file not found: {item_path}\n")
                                continue
                            with open(item_path, 'r') as item_file:
                                item_content = item_file.read()
                                item_data = yaml.safe_load(preprocess_yaml_content(item_content))
                                item_for_sale_guid = item_data.get('MonoBehaviour', {}).get('itemForSale', {}).get('guid', 'unknown')
                                limited_purchase = item_data.get('MonoBehaviour', {}).get('limitedPurchase', 0)
                                debug_log.write(f"Item for sale GUID: {item_for_sale_guid}, Limited purchase: {limited_purchase}\n")
                                if item_for_sale_guid in guid_mapping:
                                    item_for_sale_filename = guid_mapping[item_for_sale_guid]['filename']
                                    item_for_sale_path = os.path.join(input_folder, item_for_sale_filename + '.asset')
                                    if not os.path.exists(item_for_sale_path):
                                        debug_log.write(f"Item for sale file not found: {item_for_sale_path}\n")
                                        continue
                                    with open(item_for_sale_path, 'r') as item_for_sale_file:
                                        item_for_sale_content = item_for_sale_file.read()
                                        item_for_sale_data = yaml.safe_load(preprocess_yaml_content(item_for_sale_content))
                                        buy_value = float(item_for_sale_data.get('MonoBehaviour', {}).get('buyValue', 0))
                                        item_name = to_sentence_case(guid_mapping[item_for_sale_guid]['name'])
                                        sell_price = math.ceil(buy_value * markup_percent)
                                        output_line = f"{{{{shop|{item_name}|{sell_price}"
                                        if limited_purchase == 1:
                                            output_line += "|note = limited quantity item. The player can only purchase one."
                                        output_line += "}}\n"  # Ensure proper closing
                                        debug_log.write(f"Output line: {output_line}\n")
                                    debug_log.write(f"Processed item for sale file: {item_for_sale_filename}, Buy value: {buy_value}, Sell price: {sell_price}\n")
                                else:
                                    debug_log.write(f"Item for sale GUID {item_for_sale_guid} not found in guid_mapping\n")
                        else:
                            debug_log.write(f"Item GUID {item_guid} not found in guid_mapping\n")
                debug_log.write("\n")
        
        except yaml.YAMLError as e:
            with open(debug_output_file, 'a') as debug_log:
                debug_log.write(f"Error decoding YAML from file: {filename} - {e}\n")
        except Exception as e:
            with open(debug_output_file, 'a') as debug_log:
                debug_log.write(f"Error processing file {filename}: {e}\n")
