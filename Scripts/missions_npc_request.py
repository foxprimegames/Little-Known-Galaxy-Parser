import os
import re
import json

input_folder = 'Input/Assets/MonoBehaviour/'
output_file_path = 'Output/Missions/missions_npc_request.txt'
debug_output_path = '.hidden/debug_output/missions_npc_request_debug.txt'
guid_lookup_path = 'Output/guid_lookup.json'


def load_guid_lookup(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def get_name_from_guid(guid, lookup):
    for entry in lookup:
        if entry.get('guid') == guid:
            return entry['name'].capitalize()
    return 'Unknown item'


def find_assets_with_items_can_request(input_folder):
    assets_with_items_can_request = []
    debug_logs = []

    for root, _, files in os.walk(input_folder):
        for file in files:
            if file.endswith('.asset'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if 'itemsCanRequest' in content:
                            assets_with_items_can_request.append(file_path)
                            debug_logs.append(f"'itemsCanRequest' found in: {file_path}")
                except Exception as e:
                    debug_logs.append(f"Error reading file {file_path}: {e}")

    return assets_with_items_can_request, debug_logs


def extract_items_can_request_info(file_path, guid_lookup):
    items_info = []
    debug_logs = []

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            pattern = re.compile(
                r'itemData: \{fileID: \d+, guid: ([a-f0-9]+), type: \d+\}\s+amtRangeOfItem:\s+minimumNum: (\d+)\s+maxiumNum: (\d+)',
                re.MULTILINE
            )
            matches = pattern.findall(content)
            for match in matches:
                guid, min_num, max_num = match
                item_name = get_name_from_guid(guid, guid_lookup)
                items_info.append({'name': item_name, 'min_num': min_num, 'max_num': max_num})
                debug_logs.append(f"Extracted item info - GUID: {guid}, Name: {item_name}, Min: {min_num}, Max: {max_num} from file {file_path}")

    except Exception as e:
        debug_logs.append(f"Error extracting items from file {file_path}: {e}")

    return items_info, debug_logs


def write_output(assets_info, output_file_path, debug_logs, debug_output_path):
    try:
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            for asset_info in assets_info:
                output_file.write(f"{asset_info['file']}\n")
                for item in asset_info['items']:
                    output_file.write(f"  Name: {item['name']}, Min: {item['min_num']}, Max: {item['max_num']}\n")

        with open(debug_output_path, 'w', encoding='utf-8') as debug_file:
            for log in debug_logs:
                debug_file.write(f"{log}\n")
    except Exception as e:
        with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
            debug_file.write(f"Error writing output files: {e}\n")


if __name__ == "__main__":
    guid_lookup = load_guid_lookup(guid_lookup_path)
    assets, initial_debug_logs = find_assets_with_items_can_request(input_folder)
    assets_info = []
    all_debug_logs = initial_debug_logs.copy()

    for asset in assets:
        items_info, extraction_logs = extract_items_can_request_info(asset, guid_lookup)
        if items_info:
            assets_info.append({'file': asset, 'items': items_info})
        all_debug_logs.extend(extraction_logs)

    write_output(assets_info, output_file_path, all_debug_logs, debug_output_path)
