import os
import re
import json
from Utilities import guid_utils  # Assuming this is the correct import for the utility functions

def sentence_case(s):
    """
    Converts a string to sentence case.

    Args:
        s (str): The string to convert.

    Returns:
        str: The string in sentence case.
    """
    return s.capitalize()

def parse_recipe_assets(input_directory, guid_mapping, debug_file):
    """
    Parses the recipe asset files to map craft recipes to items and their ingredients.

    Args:
        input_directory (str): The path to the directory containing .asset files.
        guid_mapping (list): A list of dictionaries mapping GUIDs to item names and other information.
        debug_file (file object): The file object to write debug information to.

    Returns:
        list: A list of formatted recipe strings.
    """
    recipes = []

    for filename in os.listdir(input_directory):
        if filename.startswith("craft_") and filename.endswith(".asset"):
            try:
                with open(os.path.join(input_directory, filename), 'r') as file:
                    data = file.read()
                    debug_file.write(f"\nProcessing file: {filename}\n{data}\n")

                    # Extract product GUID
                    product_match = re.search(r'itemToCraft:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}', data)
                    product_guid = product_match.group(1) if product_match else ""

                    # Extract product item details
                    product_info = next((entry for entry in guid_mapping if entry['guid'] == product_guid), {})
                    product_name = sentence_case(product_info.get('name', 'unknown_item'))

                    # Extract product yield from purchaseBundleAmt
                    yield_match = re.search(r'purchaseBundleAmt:\s*(\d+)', data)
                    product_yield = yield_match.group(1) if yield_match else '1'

                    # Extract product item category
                    product_filename = product_info.get('filename', '')
                    product_category = 'unknown'

                    if product_filename:
                        product_asset_path = os.path.join(input_directory, f"{product_filename}.asset")
                        if os.path.exists(product_asset_path):
                            with open(product_asset_path, 'r') as product_file:
                                product_data = product_file.read()
                                category_match = re.search(r'itemCategory:\s*(.*)', product_data)
                                product_category = category_match.group(1).strip() if category_match else 'unknown'

                    # Translate category to machine
                    machine = 'unknown'
                    if product_category.lower() == 'food':
                        machine = 'Kitchen'
                    elif product_category.lower() in ['storage', 'decoration', 'machine']:
                        machine = 'Workbench'

                    # Extract craft materials
                    ingredients = []
                    materials_section = re.search(r'craftMaterials:\n(.*?)(\n[a-zA-Z]|$)', data, re.DOTALL)
                    materials = materials_section.group(1) if materials_section else ""
                    if materials:
                        materials_match = re.findall(r'itemData:\s*\{fileID: \d+, guid: ([a-f0-9]{32}), type: \d+\}.*?amountOfItem:\s*(\d+)', materials, re.DOTALL)
                        for material_guid, amount in materials_match:
                            material_info = next((entry for entry in guid_mapping if entry['guid'] == material_guid), {})
                            material_name = sentence_case(material_info.get('name', 'unknown_item'))
                            ingredients.append(f"{material_name}*{amount}")

                    ingredients_str = '; '.join(ingredients)

                    # Create the formatted recipe
                    recipe = f"# {product_name}\n{{{{Recipe|product = {product_name} |machine = {machine} |time = Instant |id = 1 |recipeSource = \n|ingredients = {ingredients_str} |yield = {product_yield} }}}}"
                    recipes.append(recipe)

                    # Debugging
                    debug_file.write(f"Processed {filename}: product_guid={product_guid}, product_name={product_name}, product_category={product_category}, machine={machine}, product_yield={product_yield}, ingredients={ingredients}\n")
            except Exception as e:
                debug_file.write(f"Error processing file {filename}: {e}\n")

    return recipes

# Define the input and output file paths
input_directory = 'Input/Assets/MonoBehaviour'
output_file_path = 'Output/Recipes/crafting_recipes.txt'
guid_lookup_path = 'Output/guid_lookup.json'
debug_output_path = '.hidden/debug_output/recipe_debug_output.txt'

# Ensure the output and debug directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Load the GUID mapping
try:
    guid_mapping = guid_utils.load_guid_lookup(guid_lookup_path)
    with open(debug_output_path, 'w') as debug_file:
        debug_file.write(f"GUID to Item Mapping: {guid_mapping}\n")

        # Parse the recipe assets and get the formatted content
        parsed_recipes = parse_recipe_assets(input_directory, guid_mapping, debug_file)

        # Write the output to a new file
        with open(output_file_path, 'w') as output_file:
            output_file.write('\n\n'.join(parsed_recipes))

    print(f"Parsed recipes have been written to {output_file_path}")
    print(f"Debug information has been written to {debug_output_path}")

except Exception as e:
    with open(debug_output_path, 'a') as debug_file:
        debug_file.write(f"Failed to load GUID mapping: {e}\n")
    print("An error occurred. Check the debug output for details.")
