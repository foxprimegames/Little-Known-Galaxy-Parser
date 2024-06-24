import os
import re

def find_files_with_section(directory, section_name):
    """
    Finds files in the specified directory containing the specified section.

    Args:
        directory (str): The path to the directory containing .asset files.
        section_name (str): The name of the section to search for.

    Returns:
        list: A list of filenames containing the specified section.
    """
    files_with_section = []

    for filename in os.listdir(directory):
        if filename.endswith(".asset"):
            with open(os.path.join(directory, filename), 'r') as file:
                data = file.read()
                if re.search(rf'{section_name}:\n', data, re.DOTALL):
                    files_with_section.append(filename)

    return files_with_section

def parse_production_recipes(directory, files_list, guid_mapping, machine_quantities, debug_file, output_file):
    """
    Parses the machine production recipes from the specified files and writes the output to a file.

    Args:
        directory (str): The path to the directory containing .asset files.
        files_list (list): A list of filenames to process.
        guid_mapping (dict): A dictionary mapping GUIDs to item details.
        machine_quantities (dict): A dictionary mapping machine names to required amounts.
        debug_file (file object): The file object to write debug information to.
        output_file (file object): The file object to write the parsed recipes to.

    Returns:
        None
    """
    recipes = {}

    for filename in files_list:
        filepath = os.path.join(directory, filename)
        with open(filepath, 'r') as file:
            data = file.read()
            debug_file.write(f"\nProcessing file: {filename}\n{data}\n")

            # Extract item name for the ingredient
            item_name_match = re.search(r'itemName:\s*(.*)', data)
            item_name = item_name_match.group(1).strip() if item_name_match else "unknown_item"

            # Extract machine production guide details
            production_matches = re.findall(r'- machineType: (\d+).*?produceDuration: (\d+).*?itemToDrop: \{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}.*?amtToGive:\s*\n\s*minimumNum: (\d+)\n\s*maxiumNum: (\d+)', data, re.DOTALL)
            for machine_type, produce_duration, item_to_drop_guid, min_num, max_num in production_matches:
                product_info = guid_mapping.get(item_to_drop_guid, {'name': 'unknown_item'})
                product_name = product_info['name']
                min_num = int(min_num)
                max_num = int(max_num)
                yield_amount = "1" if min_num == 0 and max_num == 0 else f"{min_num}-{max_num}" if min_num != max_num else str(min_num)
                machine_name = machine_type_to_name(int(machine_type))
                quantity = machine_quantities.get(machine_name.lower(), 1)

                debug_file.write(f"itemName: {item_name}, machineType: {machine_name}, produceDuration: {produce_duration}, itemToDrop: {product_name} (GUID: {item_to_drop_guid}), yield: {yield_amount}\n")

                if product_name not in recipes:
                    recipes[product_name] = []
                recipes[product_name].append(
                    f"{{{{Recipe|product = {product_name} |machine = {machine_name} |time = {produce_duration}hr |id = |recipeSource =\n|ingredients = {item_name}*{quantity} |yield = {yield_amount} }}}}"
                )

    sorted_products = sorted(recipes.items())

    for product, product_recipes in sorted_products:
        output_file.write(f"# {product}\n")
        for idx, recipe in enumerate(product_recipes, start=1):
            output_file.write(recipe.replace("|id = ", f"|id = {idx} ") + "\n")
        output_file.write("\n")

def machine_type_to_name(machine_type):
    machine_type_mapping = {
        1: "Canning Pot",
        2: "Dehydrator",
        3: "Fermentation tank",
        4: "Fiber spinner",
        5: "Freezer",
        6: "Dark matter refiner",
        7: "Furnace",
        9: "Juicer",
        10: "Medicine machine",
        12: "Press",
        15: "Carbon converter",
        16: "Recycler",
        19: "Compost machine",
        20: "Microbe compost machine",
        21: "Advanced furnace",
        22: "Advanced dark matter refiner"
    }
    return machine_type_mapping.get(machine_type, f"Unknown machine ({machine_type})")

# Define the input and output file paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_lookup_path = 'Output/guid_lookup.txt'
debug_output_path = '.hidden/debug_output/machine_recipe_debug_output.txt'
output_file_path = 'Output/Recipes/machine_recipes.txt'
files_list_path = 'Output/Recipes/files_with_machine_production.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)

# Find files with the specified section
files_with_section = find_files_with_section(input_directory, 'machineProductionGuide')

# Write the output to a new file
with open(files_list_path, 'w') as files_list_file:
    files_list_file.write('\n'.join(files_with_section))

print(f"Files with machineProductionGuide section have been written to {files_list_path}")

# Load the GUID mapping
guid_mapping = {}
with open(guid_lookup_path, 'r') as file:
    for line in file:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            guid_mapping[parts[0]] = {'name': parts[3], 'filename': parts[1]}

# Load the machine quantities
machine_quantities = {}
for guid, info in guid_mapping.items():
    if info['name'].lower() in ['canning pot', 'dehydrator', 'fermentation tank', 'fiber spinner', 'freezer', 'dark matter refiner', 'furnace', 'juicer', 'medicine machine', 'press', 'carbon converter', 'recycler', 'compost machine', 'microbe compost machine', 'advanced furnace', 'advanced dark matter refiner']:
        machine_file = os.path.join(input_directory, info['filename'] + '.asset')
        with open(machine_file, 'r') as file:
            data = file.read()
            amt_items_required_match = re.search(r'amtItemsRequiredToRun:\s*(\d+)', data)
            if amt_items_required_match:
                machine_quantities[info['name'].lower()] = int(amt_items_required_match.group(1))

# Open the debug file and output file for writing
with open(debug_output_path, 'w') as debug_file, open(output_file_path, 'w') as output_file:
    # Parse the production recipes
    parse_production_recipes(input_directory, files_with_section, guid_mapping, machine_quantities, debug_file, output_file)

print(f"Debug information has been written to {debug_output_path}")
print(f"Parsed machine recipes have been written to {output_file_path}")
