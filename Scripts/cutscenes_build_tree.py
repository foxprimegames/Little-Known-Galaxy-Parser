import os
import sys
import yaml
import json

# Add the Utilities directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'Utilities')))

from Utilities import guid_utils
from Utilities.unity_yaml_loader import add_unity_yaml_constructors, preprocess_yaml_content

# Add Unity YAML constructors
add_unity_yaml_constructors()

# Define paths
input_directory = 'Input/Assets/MonoBehaviour'
guid_lookup_path = 'Output/guid_lookup.json'
output_file_path = 'Output/Cutscenes/cine_tree.txt'
debug_output_path = '.hidden/debug_output/cine_tree_debug.txt'

# Ensure output directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Cines to focus on for debugging
debug_cines = ["CineRequestOceanKing", "CineRequestOceanCure", "CineStartAnimals", "CineRoBuyIntro"]

def extract_cine_data(asset_file_path, mappings):
    with open(asset_file_path, 'r') as file:
        raw_content = file.read()
        clean_content = preprocess_yaml_content(raw_content)
        data = yaml.safe_load(clean_content)
        mono_behaviour = data.get('MonoBehaviour', {})
        
        cine_data = {
            "name": os.path.splitext(os.path.basename(asset_file_path))[0],
            "save_id": mono_behaviour.get("saveID", ""),
            "activateAfterDays": mono_behaviour.get("activateAfterDays", ""),
            "dayOfWeekRequired": mono_behaviour.get("dayOfWeekRequired", ""),
            "cineScenesToAdd": [guid_utils.get_name_from_guid(cine.get('guid', ''), mappings) for cine in mono_behaviour.get("cineScenesToAdd", [])]
        }
        
        return cine_data

def build_tree(cine_data_list):
    tree = {}
    cines_without_predecessors = set()

    # Build a map of cine name to its data for quick lookup
    cine_map = {cine["name"]: cine for cine in cine_data_list}

    # Build the tree
    for cine in cine_data_list:
        if cine["name"] not in tree:
            tree[cine["name"]] = {"data": cine, "children": []}
        
        for child_cine in cine["cineScenesToAdd"]:
            if child_cine != "Unknown":
                if child_cine not in tree:
                    tree[child_cine] = {"data": cine_map.get(child_cine, {}), "children": []}
                tree[cine["name"]]["children"].append(child_cine)
                cines_without_predecessors.discard(child_cine)
        
        if cine["name"] not in cines_without_predecessors:
            cines_without_predecessors.add(cine["name"])

    return tree, cines_without_predecessors

def print_tree(tree, cine_name, output_file, depth=0):
    indent = "    " * depth
    cine_data = tree[cine_name]["data"]
    activation_info = []
    if cine_data["activateAfterDays"]:
        activation_info.append(f"activateAfterDays: {cine_data['activateAfterDays']}")
    if cine_data["dayOfWeekRequired"] != -1:
        activation_info.append(f"dayOfWeekRequired: {cine_data['dayOfWeekRequired']}")
    activation_str = " --- " + ", ".join(activation_info) if activation_info else ""
    output_file.write(f"{indent}|-- {cine_name}{activation_str}\n")
    for child in tree[cine_name]["children"]:
        print_tree(tree, child, output_file, depth + 1)

def main():
    try:
        # Load the GUID lookup and create mappings
        guid_lookup = guid_utils.load_guid_lookup(guid_lookup_path)
        mappings = guid_utils.create_mappings(guid_lookup)

        # Collect all cine data
        cine_data_list = []
        for filename in os.listdir(input_directory):
            if filename.endswith(".asset"):
                asset_file_path = os.path.join(input_directory, filename)
                cine_data = extract_cine_data(asset_file_path, mappings)
                if cine_data["save_id"].startswith("cine_"):
                    cine_data_list.append(cine_data)
        
        # Build the tree
        tree, cines_without_predecessors = build_tree(cine_data_list)

        # Print the tree and the list of orphaned cines
        with open(output_file_path, 'w') as output_file, open(debug_output_path, 'a') as debug_file:
            # Focused debug information
            for cine in debug_cines:
                if cine in tree:
                    debug_file.write(f"Debug tree for {cine}: {tree[cine]}\n")
            
            for root_cine in cines_without_predecessors:
                try:
                    print_tree(tree, root_cine, output_file)
                except KeyError as e:
                    debug_file.write(f"Error printing tree for root cine '{root_cine}': {str(e)}\n")
                    if root_cine in tree:
                        debug_file.write(f"Debug tree for {root_cine}: {tree[root_cine]}\n")
                    else:
                        debug_file.write(f"{root_cine} not found in tree.\n")
            
            output_file.write("\nCines without predecessors:\n")
            for cine in cines_without_predecessors:
                output_file.write(f"{cine}\n")

        # Print success message to terminal
        print("Cine tree has been successfully written to 'cine_tree.txt'.")

    except Exception as e:
        with open(debug_output_path, 'a') as debug_file:
            debug_file.write(f"An error occurred: {str(e)}\n")
        print("An error occurred. Check the debug output for details.")

if __name__ == "__main__":
    main()
