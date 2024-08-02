import os
import re
from Utilities import guid_utils

# Paths
input_directory = 'Input/Assets/MonoBehaviour/'
output_file_path = 'Output/friendship_points.txt'
debug_output_path = '.hidden/debug_output/friendship_points_debug.txt'
mapping_file_path = 'Output/guid_lookup.json'

# Ensure the debug output directory exists
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

def log_debug(message):
    with open(debug_output_path, 'a') as debug_file:
        debug_file.write(message + '\n')

def filter_content(content):
    log_debug("Filtering content...")
    # Regex to match the lines to remove
    pattern = re.compile(r"^(%YAML 1\.1|%TAG !u! tag:unity3d\.com,2011:|--- !u!114 &11400000|MonoBehaviour:|  m_ObjectHideFlags: 0|  m_CorrespondingSourceObject: {fileID: 0}|  m_PrefabInstance: {fileID: 0}|  m_PrefabAsset: {fileID: 0}|  m_GameObject: {fileID: 0}|  m_Enabled: 1|  m_EditorHideFlags: 0|  m_Script: {fileID: 11500000, guid: 75d018639740c96f72f68400654af916, type: 3}|  m_Name: friendshipPointsTable|  m_EditorClassIdentifier:)")
    filtered_lines = [line for line in content.split('\n') if not pattern.match(line)]
    filtered_content = '\n'.join(filtered_lines)
    log_debug(f"Filtered content: {filtered_content}")
    return filtered_content

def replace_guids_with_names(content, mappings):
    log_debug("Replacing GUIDs with names...")

    # Specific handling for giftsThatHaveBonus section
    gifts_pattern = re.compile(r'- itemThatHasBonus: {fileID: \d+, guid: ([0-9a-fA-F]{32}), type: \d+}')

    def replace_gift_guid(match):
        guid = match.group(1)
        name = guid_utils.get_name_from_guid(guid, mappings)
        log_debug(f"Replacing gift GUID {guid} with name {name}")
        return f'- itemThatHasBonus: {name}'

    content = gifts_pattern.sub(replace_gift_guid, content)

    log_debug(f"Content after replacing GUIDs: {content}")
    return content

def main():
    try:
        # Clear the debug file at the beginning of each run
        open(debug_output_path, 'w').close()

        # Load GUID lookup data
        log_debug("Loading GUID lookup data...")
        guid_lookup_data = guid_utils.load_guid_lookup(mapping_file_path)
        mappings = guid_utils.create_mappings(guid_lookup_data)
        log_debug(f"Loaded mappings: {mappings}")

        # Read the friendshipPointsTable.asset file
        input_file_path = os.path.join(input_directory, 'friendshipPointsTable.asset')
        log_debug(f"Reading file: {input_file_path}")
        with open(input_file_path, 'r') as input_file:
            friendship_data = input_file.read()
        log_debug(f"Original content: {friendship_data}")

        # Filter the content
        filtered_content = filter_content(friendship_data)

        # Replace GUIDs with names
        final_content = replace_guids_with_names(filtered_content, mappings)

        # Add the specified text at the top of the output
        header_text = "### Any changes to this output need to be updated on the https://lkg.wiki.gg/wiki/Relationships page\n\n"
        final_content = header_text + final_content

        # Write the final content to the output file
        with open(output_file_path, 'w') as output_file:
            output_file.write(final_content)

        # Print success message
        print(f"Friendship point information has been successfully extracted, formatted, and written to '{output_file_path}'.")

    except Exception as e:
        log_debug(f'An error occurred: {str(e)}')
        print(f"An error occurred. Check the debug output for details: '{debug_output_path}'.")

if __name__ == "__main__":
    main()
