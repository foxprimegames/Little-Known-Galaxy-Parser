import os
import json
import yaml
import re

# Paths
input_directory = 'Input/Assets/MonoBehaviour/'
guid_lookup_path = 'Output/guid_lookup.json'
output_file_path = 'Output/Gifts/npc_gift_overrides.txt'
debug_output_path = '.hidden/debug_output/npc_gift_overrides_debug.txt'

# Ensure output directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

def log_debug(message):
    with open(debug_output_path, 'a', encoding='utf-8') as debug_file:
        debug_file.write(message + '\n')

# Load GUID lookup table
try:
    with open(guid_lookup_path, 'r') as f:
        guid_lookup = json.load(f)
    log_debug(f"Loaded GUID lookup from: {guid_lookup_path}")
except Exception as e:
    log_debug(f"Failed to load GUID lookup: {e}")
    print("An error occurred. Check the debug output for details.")
    exit()

# Filter GUID lookup for entries with save_id starting with "npc_"
npc_entries = [entry for entry in guid_lookup if entry.get('save_id', '').startswith('npc_')]
log_debug(f"Filtered {len(npc_entries)} entries with save_id starting with 'npc_'")

# Extract filenames associated with these entries and add .asset extension
npc_filenames = [f"{entry['filename']}.asset" for entry in npc_entries]
log_debug(f"List of NPC filenames: {', '.join(npc_filenames)}")

# Function to find item name by GUID and convert it to sentence case
def find_item_name_by_guid(guid):
    for entry in guid_lookup:
        if entry['guid'] == guid:
            return entry.get('name', 'unknown_item').capitalize()
    return 'unknown_item'

# Function to extract and replace item overrides from an asset file
def extract_and_replace_item_overrides(asset_file):
    with open(asset_file, 'r', encoding='utf-8') as f:
        content = f.read()
    content = re.sub(r'!u![\d]+ &[\d]+', '', content)
    log_debug(f"Preprocessed content for {asset_file}: {content[:200]}...")  # Log a snippet of the content for verification
    data = yaml.safe_load(content)
    
    # Navigate the nested structure to get item overrides and replace GUIDs with names
    try:
        npc_name = data['MonoBehaviour']['m_Name']
        items_love = [find_item_name_by_guid(item['guid']) for item in data['MonoBehaviour'].get('itemsLoveOverride', [])]
        items_like = [find_item_name_by_guid(item['guid']) for item in data['MonoBehaviour'].get('itemsLikeOverride', [])]
        items_neutral = [find_item_name_by_guid(item['guid']) for item in data['MonoBehaviour'].get('itemsNeutralOverride', [])]
        items_dislike = [find_item_name_by_guid(item['guid']) for item in data['MonoBehaviour'].get('itemsDislikeOverride', [])]
    except KeyError as e:
        log_debug(f"KeyError accessing item overrides in {asset_file}: {e}")
        return None, None, None, None, None

    return npc_name, items_love, items_like, items_neutral, items_dislike

# Main script
output = []

for filename in npc_filenames:
    asset_path = os.path.join(input_directory, filename)
    if not os.path.exists(asset_path):
        log_debug(f"Asset file does not exist: {asset_path}")
        continue
    try:
        log_debug(f"Processing file: {asset_path}")
        npc_name, items_love, items_like, items_neutral, items_dislike = extract_and_replace_item_overrides(asset_path)
        
        if npc_name is None:
            log_debug(f"Skipping {filename} due to missing item overrides.")
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
        log_debug(f"Error processing {filename}: {e}")

# Save results
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print(f"Results have been written to {output_file_path}")
print(f"Debug information has been written to {debug_output_path}")
