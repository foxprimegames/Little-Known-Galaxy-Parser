import os
import re

# Paths
input_directory = 'Input/Assets/MonoBehaviour/'
output_file_path = 'Output/captain_rank_numbers.txt'
debug_output_path = '.hidden/debug_output/cptn_rank_debug.txt'
player_stat_path = 'Input/Assets/Scripts/Assembly-CSharp/PlayerStat.cs'

# List of asset filenames to look for
asset_filenames = [
    "CompletePrimaryQuest.asset",
    "CraftRecipe.asset",
    "EarnFriendshipPt.asset",
    "MicrobeCatch.asset",
    "ProduceCrop.asset",
    "ProduceFromAnimal.asset",
    "ProduceFromMachine.asset",
    "RestoreObj.asset",
    "UpgradeHouse.asset",
    "UpgradeShip.asset",
    "UpgradeTools.asset",
    "EvBonusNYCrew.asset",
    "EvBonusNYMicrobes.asset",
    "EvBonusNYProduction.asset",
    "EvBonusNYShip.asset"
]

# Function to log debug messages
def log_debug_message(message):
    os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)
    with open(debug_output_path, 'a') as debug_file:
        debug_file.write(message + '\n')

# Function to parse PlayerStat.cs to get stat-to-number mapping
def parse_player_stat(player_stat_file):
    stat_mapping = {}
    with open(player_stat_file, 'r') as file:
        content = file.read()
        matches = re.findall(r'\s*(\w+)\s*=\s*(\d+),?', content)
        for match in matches:
            stat_name, stat_number = match
            stat_mapping[int(stat_number)] = stat_name
            log_debug_message(f"Parsed stat: {stat_name} = {stat_number}")
    return stat_mapping

# Function to extract required fields from the asset content
def extract_fields(asset_content, stat_mapping):
    name_match = re.search(r'm_Name:\s*(.*)', asset_content)
    stat_match = re.search(r'statToAdjust:\s*(\d+)', asset_content)
    amount_match = re.search(r'amountToAdjust:\s*(.*)', asset_content)
    
    name = name_match.group(1).strip() if name_match else "N/A"
    stat_number = int(stat_match.group(1).strip()) if stat_match else "N/A"
    amount = amount_match.group(1).strip() if amount_match else "N/A"
    
    # Convert stat number to name using the stat mapping
    stat_name = stat_mapping.get(stat_number, "N/A")
    
    return name, stat_name, amount

# Function to read and dump asset files information
def dump_asset_information(input_dir, asset_files, output_file, stat_mapping):
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        header_text = "### Any changes to this output need to be updated on the https://lkg.wiki.gg/wiki/Captain_rank page\n\n"
        with open(output_file, 'w') as out_file:
            out_file.write(header_text)
            for file in asset_files:
                asset_path = os.path.join(input_dir, file)
                if os.path.exists(asset_path):
                    try:
                        with open(asset_path, 'r') as asset_file:
                            asset_content = asset_file.read()
                            name, stat_name, amount = extract_fields(asset_content, stat_mapping)
                            out_file.write(f"### {file}\n")
                            out_file.write(f"m_Name: {name}\n")
                            out_file.write(f"statToAdjust: {stat_name}\n")
                            out_file.write(f"amountToAdjust: {amount}\n\n")
                            log_debug_message(f"Successfully read {file}: {name}, {stat_name}, {amount}")
                    except Exception as e:
                        log_debug_message(f"Error reading {file}: {e}")
                else:
                    log_debug_message(f"File not found: {file}")
        
        log_debug_message("Asset information dumped successfully.")
        
        # Print success message
        print(f"Asset information has been successfully extracted and written to '{output_file_path}'")
    
    except Exception as e:
        log_debug_message(f'An error occurred: {str(e)}')
        print(f"An error occurred. Check the debug output for details: '{debug_output_path}'")

# Parse the PlayerStat.cs file to get stat mapping
stat_mapping = parse_player_stat(player_stat_path)

# Run the function
dump_asset_information(input_directory, asset_filenames, output_file_path, stat_mapping)