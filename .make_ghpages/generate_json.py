import os
import yaml
import json

from pathlib import Path

# Define the parent folder location
folder_path = Path(__file__).parent.absolute()
library_path = folder_path.parent

# Extract all the data.

YAML_SUFFIX = '.yaml'

# Get all the available domains.
final_dict = {dmn:{} for dmn in os.listdir(library_path) if os.path.isdir(library_path/dmn) and not dmn.startswith('.')}

def parse_yaml_files_in_folder(folder_path, exclude=None):
    if not os.path.isdir(folder_path):
        raise TypeError(f"{folder_path} must point to an existing folder.")

    result = {}

    if exclude:
        file_list = [ fname for fname in os.listdir(folder_path) if fname not in exclude ]
    else:
        file_list = os.listdir(folder_path)

    for fname in file_list:
        with open(folder_path/fname) as yaml_file:
            if fname.endswith(YAML_SUFFIX):
                fname = fname[:-len(YAML_SUFFIX)]
            else:
                raise ValueError(f"The file {fname} has unsupported extension. Please use '{YAML_SUFFIX}'")

            result[fname] = yaml.load(yaml_file, Loader=yaml.FullLoader)

    return result


# Loop over the available domains and extract the computes available under them.
for domain in final_dict:
    final_dict[domain] = {cmp:{} for cmp in os.listdir(library_path/domain) if os.path.isdir(library_path/domain/cmp) and not cmp in ['default', 'codes']}

    # Loop over the defined computers, and extract their setup and setup codes defined on them.
    for computer in final_dict[domain]:
        final_dict[domain][computer] = parse_yaml_files_in_folder(library_path/domain/computer, exclude=["README"])
        final_dict[domain][computer].update(parse_yaml_files_in_folder(library_path/domain/"codes"))

    # Extract the default computer.
    link = os.readlink(library_path/domain/'default')
    final_dict[domain]['default'] = str(Path(link))

# Store the extracted information as a single JSON file.
os.mkdir(folder_path/'out')
with open(folder_path/'out/database.json', 'w') as filep:
    json.dump(final_dict, filep, indent=4)


