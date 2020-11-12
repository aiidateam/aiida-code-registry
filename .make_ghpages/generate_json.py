import os
import yaml
import json

from pathlib import Path

# Define the parent folder location
file_path = Path(__file__).parent.absolute()
library_path = file_path.parent

# Extract all the data. 

# Get all the available domains.
final_dict = {dmn:{} for dmn in os.listdir(library_path) if os.path.isdir(library_path/dmn) and not dmn.startswith('.')}

# Loop over the available domains and extract the computes available under them.
for domain in final_dict:
    final_dict[domain] = {cmp:{} for cmp in os.listdir(library_path/domain) if os.path.isdir(library_path/domain/cmp) and not cmp == 'default'}

    # Loop over the defined computers, and extract their setup and setup codes defined on them.
    for computer in final_dict[domain]:
        for configuration in os.listdir(library_path/domain/computer):
        	with open(library_path/domain/computer/configuration) as yaml_file:
        		final_dict[domain][computer][configuration] = yaml.load(yaml_file, Loader=yaml.FullLoader)

    # Extract the default computer.
    link = os.readlink(library_path/domain/'default')
    final_dict[domain]['default'] = link[2:] 

# Store the extracted information as a single JSON file.
with open(library_path/'database.json', 'w') as filep:
    json.dump(final_dict, filep, indent=4)


