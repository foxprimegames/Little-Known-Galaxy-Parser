import json
import os
import re
import yaml

input_file_path = 'Input/Assets/TextAsset/English_Quests.txt'
guid_lookup_path = 'Output/guid_lookup.json'
mono_behaviour_path = 'Input/Assets/MonoBehaviour/'
output_file_path = 'Output/Missions/mission_infobox.txt'
debug_output_path = '.hidden/debug_output/mission_infobox_debug.txt'

def load_guid_lookup(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def get_filename_from_guid(guid, lookup):
    for entry in lookup:
        if entry.get('guid') == guid:
            return entry['filename']
    return guid

def get_name_from_guid(guid, lookup):
    for entry in lookup:
        if entry.get('guid') == guid:
            return entry['name']
    return guid

def get_filename_from_save_id(save_id, lookup):
    for entry in lookup:
        if entry.get('save_id') == save_id:
            return entry['filename']
    return None

def preprocess_yaml_content(content):
    content = re.sub(r'!u!\d+ &\d+', '', content)
    return content

def parse_mono_behaviour(file_path, lookup):
    debug_info = []
    if not os.path.exists(file_path):
        debug_info.append(f"File not found: {file_path}")
        return None, debug_info
    
    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            content = file.read()
            content = preprocess_yaml_content(content)
            yaml_content = yaml.safe_load(content)
            mono_behaviour = yaml_content.get('MonoBehaviour', {})
            add_items_on_complete = mono_behaviour.get('addItemsOnComplete', [])
            rewards = []
            for item in add_items_on_complete:
                item_data = item.get('itemData', {}).get('guid', 'None')
                amount_of_item = item.get('amountOfItem', 'N/A')
                if item_data != 'None':
                    item_name = get_name_from_guid(item_data, lookup)
                    rewards.append(f"{item_name}*{amount_of_item}")
                else:
                    rewards.append(f"{item_data}*{amount_of_item}")

            expires_in_days = mono_behaviour.get('expiresInDays', 'N/A')
            if isinstance(expires_in_days, dict) and expires_in_days.get('fileID') == 0:
                expires_in_days = "Unlimited"

            quest_type_mapping = {0: "Primary", 1: "Crew", 2: "BB"}
            quest_type = mono_behaviour.get('questType', 'N/A')
            quest_type = quest_type_mapping.get(quest_type, quest_type)

            unlock_store_items_at_complete = '; '.join(
                get_filename_from_guid(item.get('guid', 'None'), lookup) for item in mono_behaviour.get('unlockStoreItemsAtComplete', [])
            )

            add_emails = '; '.join(
                get_filename_from_guid(email.get('guid', 'None'), lookup) for email in mono_behaviour.get('addEmails', [])
            )

            data = {
                'questType': quest_type,
                'npcOwner': mono_behaviour.get('npcOwner', {}).get('guid', file_path),
                'goalsList': '; '.join(goal.get('guid', file_path) for goal in mono_behaviour.get('goalsList', [])),
                'expiresInDays': expires_in_days,
                'unlockStoreItemsAtComplete': unlock_store_items_at_complete,
                'addItemsOnComplete': '; '.join(rewards),
                'unlockQuests': '; '.join(quest.get('guid', file_path) for quest in mono_behaviour.get('unlockQuests', [])),
                'addEmails': add_emails
            }
            debug_info.append(f"Parsed data from {file_path}: {data}")
        except yaml.YAMLError as e:
            debug_info.append(f"Error parsing YAML in {file_path}: {e}")
            return None, debug_info
    return data, debug_info

def parse_goal(file_path, lookup):
    debug_info = []
    requires = []
    if not os.path.exists(file_path):
        debug_info.append(f"File not found: {file_path}")
        return requires, debug_info

    with open(file_path, 'r', encoding='utf-8') as file:
        try:
            content = file.read()
            content = preprocess_yaml_content(content)
            yaml_content = yaml.safe_load(content)
            goal_data = yaml_content.get('MonoBehaviour', {})
            item_to_collect = goal_data.get('itemToCollect', {}).get('guid')
            if item_to_collect:
                item_name = get_name_from_guid(item_to_collect, lookup)
                required_amount = goal_data.get('requiredAmount', 'N/A')
                quality_required = goal_data.get('itemQuery', {}).get('qualityRequired', 0)

                if quality_required == 1:
                    if item_name.lower().startswith("super "):
                        item_name = item_name[6:]
                    requires.append(f"{item_name}*{required_amount}/1")
                else:
                    requires.append(f"{item_name}*{required_amount}")
            else:
                filename = os.path.basename(file_path).replace('.asset', '')
                requires.append(filename)

            debug_info.append(f"Parsed goal from {file_path}: {requires}")

        except yaml.YAMLError as e:
            debug_info.append(f"Error parsing YAML in {file_path}: {e}")
            return requires, debug_info
    return requires, debug_info

def parse_quests(file_path):
    debug_info = []
    quests = []
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        regions = re.findall(r'//#region\s+([^#]+?)\s+\.*?\s*\n(.*?)\n\s*//#endregion', content, re.DOTALL)
        for region_name, region_content in regions:
            quest_key = re.search(r'"questKey":\s*"([^"]+)"', region_content)
            quest_name = re.search(r'"questName":\s*"([^"]+)"', region_content)
            quest_description = re.search(r'"questDescription":\s*"([^"]+)"', region_content)
            if quest_key and quest_name and quest_description:
                quests.append({
                    'region': region_name.strip().replace(' ', '_'),
                    'key': quest_key.group(1),
                    'name': quest_name.group(1),
                    'description': quest_description.group(1)
                })
                debug_info.append(f"Parsed quest: {quest_name.group(1)}")
            else:
                debug_info.append(f"Failed to parse quest in region: {region_name.strip()}")
    return quests, debug_info

def replace_guids_with_filenames(text, lookup):
    items = text.split('; ')
    replaced = []
    for item in items:
        if '*' in item:
            guid, amount = item.split('*')
            name = get_name_from_guid(guid, lookup)
            replaced.append(f"{name}*{amount}")
        else:
            name = get_name_from_guid(item, lookup)
            replaced.append(name)
    return '; '.join(replaced)

def format_quest_info(quests, guid_lookup):
    formatted_quests = []
    debug_info = []
    for quest in quests:
        mono_file_name = get_filename_from_save_id(quest['key'], guid_lookup)
        if mono_file_name:
            mono_file_path = os.path.join(mono_behaviour_path, f"{mono_file_name}.asset")
            mono_data, mono_debug_info = parse_mono_behaviour(mono_file_path, guid_lookup)
            debug_info.extend(mono_debug_info)

            requires = []
            if mono_data:
                for goal_guid in mono_data['goalsList'].split('; '):
                    goal_filename = get_filename_from_guid(goal_guid, guid_lookup)
                    goal_path = os.path.join(mono_behaviour_path, f"{goal_filename}.asset")
                    goal_requires, goal_debug_info = parse_goal(goal_path, guid_lookup)
                    if goal_requires:
                        requires.extend(goal_requires)
                    else:
                        requires.append(os.path.basename(goal_filename))
                    debug_info.extend(goal_debug_info)

                next_quests = replace_guids_with_filenames(mono_data['unlockQuests'], guid_lookup)
                unlock_store_items = replace_guids_with_filenames(mono_data['unlockStoreItemsAtComplete'], guid_lookup)

                formatted_quests.append(
                    f"## {quest['name']} - {quest['key']}\n"
                    f"{{{{Mission infobox\n"
                    f"|name     = {quest['name']}\n"
                    f"|id       = {quest['region']}\n"
                    f"|obj      = {quest['description']}\n"
                    f"|type     = {mono_data['questType']}\n"
                    f"|time     = {mono_data['expiresInDays']}\n"
                    f"|location = \n"
                    f"|prereq   = \n"
                    f"|requires = {'; '.join(requires)}\n"
                    f"|rewards  = {replace_guids_with_filenames(mono_data['addItemsOnComplete'], guid_lookup)}\n"
                    f"|npcs     = {get_name_from_guid(mono_data['npcOwner'], guid_lookup)}\n"
                    f"|prev     = \n"
                    f"|next     = {next_quests}\n"
                    f"}}}}\n"
                    f"Unlock Store Items at Complete GUID: {unlock_store_items}\n"
                    f"Send Email: {replace_guids_with_filenames(mono_data['addEmails'], guid_lookup)}\n"
                )
            else:
                formatted_quests.append(
                    f"## {quest['name']} - {quest['key']}\n"
                    f"{{{{Mission infobox\n"
                    f"|name     = {quest['name']}\n"
                    f"|id       = {quest['region']}\n"
                    f"|obj      = {quest['description']}\n"
                    f"|type     = N/A\n"
                    f"|time     = N/A\n"
                    f"|location = \n"
                    f"|prereq   = \n"
                    f"|requires = \n"
                    f"|rewards  = \n"
                    f"|npcs     = \n"
                    f"|prev     = \n"
                    f"|next     = \n"
                    f"}}}}\n"
                    f"Unlock Store Items at Complete GUID: \n"
                    f"Send Email: \n"
                )
        else:
            debug_info.append(f"No filename found for save_id: {quest['key']}")
    return formatted_quests, debug_info

def write_to_file(quests, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        for quest in quests:
            file.write(quest + "\n")

def write_debug_info(debug_info, file_path):
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        for info in debug_info:
            file.write(info + "\n")

def main():
    debug_info = []
    
    try:
        guid_lookup = load_guid_lookup(guid_lookup_path)
        debug_info.append(f"Loaded GUID lookup from: {guid_lookup_path}")
    except Exception as e:
        debug_info.append(f"Failed to load GUID lookup: {e}")
        write_debug_info(debug_info, debug_output_path)
        return

    try:
        quests, parse_quests_debug_info = parse_quests(input_file_path)
        debug_info.append(f"Parsed quests from file: {input_file_path}")
        debug_info.extend(parse_quests_debug_info)
    except Exception as e:
        debug_info.append(f"Failed to parse quests: {e}")
        write_debug_info(debug_info, debug_output_path)
        return

    try:
        formatted_quests, format_quest_debug_info = format_quest_info(quests, guid_lookup)
        debug_info.extend(format_quest_debug_info)
        write_to_file(formatted_quests, output_file_path)
        debug_info.append(f"Wrote formatted quests to: {output_file_path}")
    except Exception as e:
        debug_info.append(f"Failed to format/write quests: {e}")

    write_debug_info(debug_info, debug_output_path)
    print("Mission infoboxes have been generated and written to the output file.")

if __name__ == "__main__":
    main()
