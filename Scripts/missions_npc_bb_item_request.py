import os
import re
import json

input_folder = 'Input/Assets/MonoBehaviour/'
output_folder = 'Output/Missions/'
debug_output_path = '.hidden/debug_output/missions_npc_bb_request_debug.txt'
guid_lookup_path = 'Output/guid_lookup.json'
npc_text_asset_folder = 'Input/Assets/TextAsset/'


def load_guid_lookup(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def get_name_and_filename_from_guid(guid, lookup):
    for entry in lookup:
        if entry.get('guid') == guid:
            return entry['name'].capitalize(), entry.get('filename')
    return 'Unknown item', None


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
                item_name, filename = get_name_and_filename_from_guid(guid, guid_lookup)
                buy_value = find_buy_value(filename) if filename else 'None'
                items_info.append({'name': item_name, 'min_num': min_num, 'max_num': max_num, 'buy_value': buy_value})
                debug_logs.append(f"Extracted item info - GUID: {guid}, Name: {item_name}, Min: {min_num}, Max: {max_num}, BuyValue: {buy_value} from file {file_path}")

    except Exception as e:
        debug_logs.append(f"Error extracting items from file {file_path}: {e}")

    return items_info, debug_logs


def find_buy_value(filename):
    if not filename:
        return 'None'

    file_path = os.path.join(input_folder, f"{filename}.asset")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'buyValue: (\d+)', content)
            if match:
                return match.group(1)
    except Exception as e:
        return 'None'
    return 'None'


def fetch_quest_info(npc_name):
    quest_info = {}
    debug_logs = []

    npc_file_path = os.path.join(npc_text_asset_folder, f"English_{npc_name}.txt")
    if not os.path.exists(npc_file_path):
        debug_logs.append(f"NPC text asset file not found: {npc_file_path}")
        return quest_info, debug_logs

    try:
        with open(npc_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            pattern = re.compile(
                r'//#region T_BRING ITEMS.*?\{(.*?)//#endregion',
                re.DOTALL
            )
            matches = pattern.findall(content)
            for match in matches:
                quest_content = match
                quest_key_match = re.search(r'"questKey": "([^"]+)"', quest_content)
                quest_name_match = re.search(r'"questName": "([^"]+)"', quest_content)
                quest_description_match = re.search(r'"questDescription": "([^"]+)"', quest_content)
                bulletin_text_match = re.search(r'"key": "Bulletin",.*?"text": "([^"]+)"', quest_content, re.DOTALL)
                active_text_match = re.search(r'"key": "Active",.*?"text": "([^"]+)"', quest_content, re.DOTALL)
                completed_text_match = re.search(r'"key": "Completed",.*?"text": "([^"]+)"', quest_content, re.DOTALL)

                if quest_key_match and quest_name_match and quest_description_match and bulletin_text_match and active_text_match and completed_text_match:
                    quest_key = quest_key_match.group(1)
                    quest_name = quest_name_match.group(1)
                    quest_description = quest_description_match.group(1)
                    bulletin_text = bulletin_text_match.group(1).replace('\\n', '<br>')
                    active_text = active_text_match.group(1).replace('\\n', '<br>')
                    completed_text = completed_text_match.group(1).replace('\\n', '<br>')
                    quest_info[quest_key] = {
                        'name': quest_name,
                        'description': quest_description,
                        'bulletin': bulletin_text,
                        'active': active_text,
                        'completed': completed_text,
                        'content': quest_content
                    }
                    debug_logs.append(f"Extracted quest info - Key: {quest_key}, Name: {quest_name}, Description: {quest_description}, Bulletin: {bulletin_text}, Active: {active_text}, Completed: {completed_text} from file {npc_file_path}")

    except Exception as e:
        debug_logs.append(f"Error extracting quest info from file {npc_file_path}: {e}")

    return quest_info, debug_logs


def write_output(assets_info, output_folder, debug_logs, debug_output_path):
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for asset_info in assets_info:
            npc_name = os.path.basename(asset_info['file']).split('.')[0]
            debug_logs.append(f"Processing NPC name: {npc_name}")
            quest_info, quest_debug_logs = fetch_quest_info(npc_name)
            debug_logs.extend(quest_debug_logs)
            for quest_key, quest_details in quest_info.items():
                item_list = "; ".join([item['name'] for item in asset_info['items']])
                requires_text = "; ".join([f"{item['name']}*{item['min_num']}-{item['max_num']}" for item in asset_info['items']])
                quest_file_path = os.path.join(output_folder, f"mission_bb_request_{quest_details['name'].replace(' ', '_')}.txt")
                with open(quest_file_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(f"### {quest_details['name']}\n")
                    output_file.write(f"{{{{Mission infobox\n")
                    output_file.write(f"|name     = {quest_details['name']}\n")
                    output_file.write(f"|id       = T_BRING_ITEMS_{quest_details['name'].replace(' ', '_').upper()}\n")
                    output_file.write(f"|obj      = {quest_details['description']}\n")
                    output_file.write(f"|type     = bb\n")
                    output_file.write(f"|time     = 2-5 days\n")
                    output_file.write(f"|location = \n")
                    output_file.write(f"|prereq   = \n")
                    output_file.write(f"|requires = {item_list}\n")
                    output_file.write(f"|requiresText = {npc_name} will request one of the following:{{{{icon list|{requires_text}}}}}\n")
                    output_file.write(f"|rewards  = Credits\n")
                    output_file.write(f"|npcs     = {npc_name}\n")
                    output_file.write(f"|prev     = \n")
                    output_file.write(f"|next     = }}}}\n\n")
                    output_file.write(f"===Bulletin Board===\n")
                    output_file.write(f"When this mission is selected, the player will see a generic bulletin request that says:\n")
                    output_file.write(f"{{{{quote|{quest_details['bulletin']}}}}}\n\n")
                    output_file.write(f"{{{{bulletin mission table\n")
                    for i, item in enumerate(asset_info['items'], start=1):
                        output_file.write(f"|item{i} = {item['name']}\n")
                        output_file.write(f"   |buyValue{i} = {item['buy_value']}\n")
                        output_file.write(f"   |min{i} = {item['min_num']}\n")
                        output_file.write(f"   |max{i} = {item['max_num']}\n")
                    output_file.write(f"}}}}\n\n")
                    output_file.write(f"===Active===\n")
                    output_file.write(f"If the player speaks with {npc_name} while this mission is active, they will say:<br>\n")
                    output_file.write(f"{{{{Dialogue|npc={npc_name}|{quest_details['active']}}}}}\n\n")
                    output_file.write(f"===Turn In===\n")
                    output_file.write(f"Once the player has obtained the requested item(s), they need to return to {npc_name}. When the player speaks with them, the quest will automatically turn in and they will say:<br>\n")
                    output_file.write(f"{{{{Dialogue|npc={npc_name}|{quest_details['completed']}}}}}\n\n")

                    # Dump the entire content of the quest region at the bottom of the file
                    output_file.write(f"\n\n#region T_BRING ITEMS\n")
                    output_file.write(f"{quest_details['content']}\n")
                    output_file.write(f"#endregion\n")

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

    write_output(assets_info, output_folder, all_debug_logs, debug_output_path)
