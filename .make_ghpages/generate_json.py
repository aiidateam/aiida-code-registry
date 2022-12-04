import os
import yaml
import json
import copy
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

# Prepare the config db for aiida 2.x data type entry points compatibility
def update_to_v2_entry_points(comp_setup: dict) -> dict:
    """
    v1 -> v2 with attach `core.` in front for transport and scheduler.
    This is a mutate function will change the value of argument `comp_setup`
    """
    new_comp_setup = {}
    for key, value in comp_setup.items():
        if key in ['transport', 'scheduler']:
            new_comp_setup[key] = f"core.{value}"
        else:
            new_comp_setup[key] = value
            
    return new_comp_setup
            

final_dict_v2 = copy.deepcopy(final_dict)

# Loop over or the fields and update to compatible with aiida 2.x entry points name
for domain in final_dict_v2:
    for computer in final_dict_v2[domain]:
        if computer != 'default':
            final_dict_v2[domain][computer]["computer-setup"] = update_to_v2_entry_points(final_dict_v2[domain][computer]["computer-setup"])
            
# Prepare the config db for aiida 2.1 data type entry points compatibility
def update_to_v2_1_entry_points(code_setup: dict) -> dict:
    """
    v2 -> v2.1
    orm.Code to orm.InstalledCode setup.
    """
    # New parameters of InstalledCode setup
    new_code_setup = {}
    for key, value in code_setup.items():
        if key == "input_plugin":
            new_code_setup["default_calc_job_plugin"] = value
        elif key == "on_computer":
            continue
        elif key == "remote_abs_path":
            new_code_setup["filepath_executable"] = value
        else:
            new_code_setup[key] = value
            
    return new_code_setup

final_dict_v2_1 = copy.deepcopy(final_dict_v2)

# Loop over or the fields and update to compatible with aiida 2.x entry points name
for domain in final_dict_v2_1:
    for computer in final_dict_v2_1[domain]:
        if computer != 'default':
            for key in final_dict_v2_1[domain][computer]:
                if key not in ['computer-setup', 'computer-configure']:
                    final_dict_v2_1[domain][computer][key] = update_to_v2_1_entry_points(final_dict_v2_1[domain][computer][key])

# Store the extracted information as a single JSON file.
os.mkdir(folder_path/'out')
with open(folder_path/'out/database.json', 'w') as filep:
    json.dump(final_dict, filep, indent=4)

# Store the v2 compatible entry points
with open(folder_path/'out/database_v2.json', 'w') as filep:
    json.dump(final_dict_v2, filep, indent=4)

# Store the v2.1 compatible code data
with open(folder_path/'out/database_v2_1.json', 'w') as filep:
    json.dump(final_dict_v2_1, filep, indent=4)
