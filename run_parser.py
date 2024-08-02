import subprocess
import os

# List of scripts to execute (relative paths using raw strings or forward slashes)
scripts = [
    r"Scripts\item_description_parser.py",
    r"Scripts\guid_mapper.py",
    r"Scripts\dialogue_parser.py",
    r"Scripts\email_parser.py",
    r"Scripts\infobox_item_parser.py",
    r"Scripts\infobox_seed_parser.py",
    r"Scripts\loot_table_generator.py",
    r"Scripts\loot_list_parser.py",
    r"Scripts\loot_table_parser.py",
    r"Scripts\mission_infobox.py",
    r"Scripts\missions_npc_bb_item_request.py",
    r"Scripts\npc_gift_overrides_parser.py",
    r"Scripts\npc_gifts_for_player_parser.py",
    r"Scripts\recipe_crafting_parser.py",
    r"Scripts\recipe_machine_production_parser.py",
    r"Scripts\shop_catalog_parser.py",
    r"Scripts\decoration_fixture_parser.py",
    r"Scripts\captain_rank_numbers.py",
    r"Scripts\friendship_points.py"
]

# Path to the debug output file
debug_output_path = os.path.join('.hidden', 'debug_output', 'run_parser_debug.txt')

# Ensure the debug output directory exists
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Function to execute a script
def execute_script(script_path):
    try:
        result = subprocess.run(["python", script_path], check=True, capture_output=True, text=True)
        with open(debug_output_path, 'a') as debug_file:
            debug_file.write(f"Executed {script_path} successfully.\n")
            debug_file.write(f"Output:\n{result.stdout}\n")
    except subprocess.CalledProcessError as e:
        error_message = f"Error executing {script_path}: {e}\nOutput:\n{e.output}\nErrors:\n{e.stderr}\n"
        with open(debug_output_path, 'a') as debug_file:
            debug_file.write(error_message)

# Change the working directory to the script's directory
os.chdir(os.path.dirname(__file__))

# Execute each script in order
for script in scripts:
    execute_script(script)
    print(f"Executed {script} successfully.")

# Provide a link to the debug file at the end
print(f"Debug information has been written to {debug_output_path}")