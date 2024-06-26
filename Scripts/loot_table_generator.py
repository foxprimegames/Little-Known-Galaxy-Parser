import os
import re

def find_loot_table_assets(input_directory, output_file_path):
    """
    Find asset files containing loot tables and write them to an output file.
    """
    loot_table_assets = []

    for filename in os.listdir(input_directory):
        if filename.endswith(".asset"):
            filepath = os.path.join(input_directory, filename)
            with open(filepath, 'r') as file:
                content = file.read()
                if "lootTable" in content:
                    loot_table_assets.append(filename)

    with open(output_file_path, 'w') as output_file:
        for asset in loot_table_assets:
            output_file.write(asset + '\n')

input_directory = 'Input/Assets/MonoBehaviour'
output_file_path = 'Output/Drops/loot_table_list.txt'

# Ensure the output directory exists
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Generate the loot table list
find_loot_table_assets(input_directory, output_file_path)

print(f"Loot table list has been written to {output_file_path}")
