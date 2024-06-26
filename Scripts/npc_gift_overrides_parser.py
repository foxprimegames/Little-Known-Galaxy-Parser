import os
import json
import yaml
import re

# Paths
input_directory = 'Input/Assets/MonoBehaviour/'
guid_lookup_path = 'Output/guid_lookup.json'
output_file_path = 'Output/Gifts/npc_gift_overrides.txt'
debug_output_path = '.hidden/debug_output/npc_gift_overrides_debug.txt'

# Load GUID lookup table
with open(guid_lookup_path, 'r') as f:
    guid_lookup = json.load(f)

# Filter GUID lookup for entries with save_id starting with "npc_"
npc_entries = [entry for entry in guid_lookup if entry.get('save_id', '').startswith('npc_')]
debug_info = [f"Filtered {len(npc_entries)} entries with save_id starting with 'npc_'"]

# Extract filenames associated with these entries and add .asset extension
npc_filenames = [f"{entry['filename']}.asset" for entry in npc_entries]
debug_info.append(f"List of NPC filenames: {', '.join(npc_filenames)}")

# Custom function to preprocess YAML content and remove Unity-specific tags
def preprocess_yaml_content(content):
    content = re.sub(r'%TAG !u!.*', '', content)
    content = re.sub(r'!u![0-9]+ &[0-9]+', '', content)
    return content

# Function to find item name by GUID and convert it to sentence case
def find_item_name_by_guid(guid, debug_info):
    for entry in guid_lookup:
        if entry['guid'] == guid:
            name = entry.get('name')
            if name:
                return name.capitalize()
    debug_info.append(f"GUID not found: {guid}")
    return None

# Function to extract and replace item overrides from an asset file
def extract_and_replace_item_overrides(asset_file, debug_info):
    with open(asset_file, 'r') as f:
        content = f.read()
    content = preprocess_yaml_content(content)
    debug_info.append(f"Preprocessed content for {asset_file}: {content[:200]}...")  # Log a snippet of the content for verification
    data = yaml.safe_load(content)
    
    # Navigate the nested structure to get item overrides and replace GUIDs with names
    try:
        npc_name = data['MonoBehaviour']['m_Name']
        items_love = [find_item_name_by_guid(item['guid'], debug_info) for item in data['MonoBehaviour']['itemsLoveOverride']]
        items_like = [find_item_name_by_guid(item['guid'], debug_info) for item in data['MonoBehaviour']['itemsLikeOverride']]
        items_neutral = [find_item_name_by_guid(item['guid'], debug_info) for item in data['MonoBehaviour']['itemsNeutralOverride']]
        items_dislike = [find_item_name_by_guid(item['guid'], debug_info) for item in data['MonoBehaviour']['itemsDislikeOverride']]
    except KeyError as e:
        debug_info.append(f"KeyError accessing item overrides: {e}")
        return None, None, None, None, None

    return npc_name, items_love, items_like, items_neutral, items_dislike

# Main script
output = []

for filename in npc_filenames:
    asset_path = os.path.join(input_directory, filename)
    if not os.path.exists(asset_path):
        debug_info.append(f"Asset file does not exist: {asset_path}")
        continue
    try:
        debug_info.append(f"Processing file: {asset_path}")
        npc_name, items_love, items_like, items_neutral, items_dislike = extract_and_replace_item_overrides(asset_path, debug_info)
        
        if npc_name is None:
            debug_info.append(f"Skipping {filename} due to missing item overrides.")
            continue
        
        npc_output = f"""
# {npc_name}
{{{{NPC gift preferences
|love       = {';'.join(items_love) if items_love else ''}
|loveGroups =

|like       = {';'.join(items_like) if items_like else ''}
|likeGroups = [[:Category:Item universally liked|Universally Liked Items]]

|neutral       = {';'.join(items_neutral) if items_neutral else ''}
|neutralGroups = [[:Category:Item universally neutral|Universally Neutral Items]]

|dislike       = {';'.join(items_dislike) if items_dislike else ''}
|dislikeGroups = [[:Category:Item universally disliked|Universally Disliked Items]]
}}}}
"""
        output.append(npc_output)
    except Exception as e:
        debug_info.append(f"Error processing {filename}: {e}")

# Save results
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
with open(output_file_path, 'w') as f:
    f.write('\n'.join(output))

# Save debug information
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)
with open(debug_output_path, 'w') as f:
    f.write('\n'.join(debug_info))

print(f"Results have been written to {output_file_path}")
print(f"Debug information has been written to {debug_output_path}")
