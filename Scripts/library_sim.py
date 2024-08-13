import re
import os

# Function to convert a string to Title Case and remove underscores
def to_title_case(s):
    return s.replace("_", " ").title()

# Function to clean the header
def clean_header(header):
    # Remove "Topic" and trailing dots
    header = header.replace("Topic", "").strip()
    header = re.sub(r'\.{3,}', '', header).strip()
    return header

# Function to clean the body text, removing <style=Item> and </style> tags
def clean_body_text(text):
    # Remove <style=Item> and </style> tags, keeping the content inside
    text = re.sub(r'<style=Item>(.*?)</style>', r'\1', text)
    return text.replace("\\n", "<br>")  # Convert \n to <br>

# Function to determine the correct data title based on the presence of a colon
def get_data_title(library_subtopic):
    if ":" in library_subtopic:
        return library_subtopic.split(":")[1].strip()
    return library_subtopic

def process_library_file(input_file, output_file, debug_file):
    try:
        with open(input_file, 'r', encoding='utf-8') as infile, open(output_file, 'w', encoding='utf-8') as outfile, open(debug_file, 'w', encoding='utf-8') as debugfile:
            # Log initial info to the debug file
            debugfile.write("Starting file processing...\n")
            
            current_header = ""
            
            for line in infile:
                # Log the line being processed
                debugfile.write(f"Processing line: {line.strip()}\n")
                
                # Match a new header region
                header_match = re.search(r'#region (.+)', line)
                if header_match:
                    raw_header = header_match.group(1).strip()
                    current_header = clean_header(to_title_case(raw_header))
                    debugfile.write(f"Captured header: {current_header}\n")
                    continue
                
                # Match a library item entry
                if line.strip().startswith('{'):
                    # Attempt to read the key, title, and body
                    library_key = ""
                    library_subtopic = ""
                    library_body = ""
                    
                    # Read the following lines for key, subtopic, and body
                    while True:
                        next_line = infile.readline().strip()
                        if not next_line:
                            break
                        
                        debugfile.write(f"Reading line: {next_line}\n")
                        
                        if '"libraryKey":' in next_line:
                            library_key_match = re.search(r'"libraryKey": "(.+?)",', next_line)
                            if library_key_match:
                                library_key = library_key_match.group(1)
                            debugfile.write(f"Captured libraryKey: {library_key}\n")
                        
                        if '"librarySubtopic":' in next_line:
                            library_subtopic_match = re.search(r'"librarySubtopic": "(.+?)",', next_line)
                            if library_subtopic_match:
                                library_subtopic = library_subtopic_match.group(1)
                            debugfile.write(f"Captured librarySubtopic: {library_subtopic}\n")
                        
                        if '"libraryBody":' in next_line:
                            library_body_match = re.search(r'"libraryBody": "(.+?)"', next_line, re.DOTALL)
                            if library_body_match:
                                library_body = library_body_match.group(1)
                            debugfile.write(f"Captured libraryBody: {library_body}\n")
                        
                        if library_key and library_subtopic and library_body:
                            break
                    
                    # If all required parts were captured, write the formatted book entry
                    if library_key and library_subtopic and library_body:
                        formatted_body = clean_body_text(library_body)
                        outfile.write(f'{{{{Book|collapsed=false\n')
                        outfile.write(f'|header={current_header}\n')
                        outfile.write(f'|title={library_subtopic}\n')
                        outfile.write(f'|{formatted_body}}}}}\n\n')
                        debugfile.write(f"Processed entry: {library_subtopic} with header: {current_header}\n")
                    else:
                        debugfile.write(f"Skipped entry due to missing data. Key: {library_key}, Subtopic: {library_subtopic}, Body: {library_body}\n")

        print(f"Processing complete. Formatted output saved to {output_file}.")
    except Exception as e:
        print(f"An error occurred: {e}")
        with open(debug_file, 'a', encoding='utf-8') as debugfile:
            debugfile.write(f"Error: {e}\n")

# Paths
input_directory = 'Input/Assets/TextAsset/English_Library.txt'
output_file_path = 'Output/LIBRARY_sim.txt'  # Output to a .txt file
debug_output_path = '.hidden/debug_output/lib_sim_debug.txt'

# Ensure output directories exist
os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
os.makedirs(os.path.dirname(debug_output_path), exist_ok=True)

# Run the processing function
process_library_file(input_directory, output_file_path, debug_output_path)
