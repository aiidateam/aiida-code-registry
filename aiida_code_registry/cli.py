#!/usr/bin/env python
"""Export computing environment"""
import tempfile
import yaml
import requests
import jinja2
import click
from click.testing import CliRunner

from aiida.cmdline.utils import decorators
from aiida.cmdline.commands.cmd_computer import computer_setup
from config import REGISTRY_URL, REGISTRY_PATH

@click.group()
def computer():
    pass


@computer.command('setup')
@click.argument('LABEL', type=str)
@click.option('--local/--online', type=bool, default=False, 
help='Use local version of registry rather than online version (default: online).')
@click.option('--skip-codes/--include-codes', type=bool, default=False, 
help='Set up all codes known for this computer.')
@click.pass_context
#@decorators.with_dbenv()
def computer_setup(ctx, label, local, skip_codes):
    """Export computing environment (for import into another AiiDA profile).
    """
    from jinja2.meta import find_undeclared_variables

    yaml_path = f'{label}/default/computer-setup.yaml'

    if local:
        with open(REGISTRY_PATH / yaml_path ) as handle:
            template_str = handle.read()
    else:
        url = REGISTRY_URL + '/' + yaml_path
        r = requests.get(url, allow_redirects=True)
        template_str = r.content.decode()

    env = jinja2.Environment()
    template_vars = find_undeclared_variables(env.parse(template_str))

    template_vars_dict = { k: None for k in template_vars }
    for key in template_vars:  # loop over template_vars for ordering
        template_vars_dict[key] = click.prompt(key)

    template = env.from_string(template_str)


    print(template.render(**template_vars_dict))

    computer_setup_args = yaml.safe_load(template.render(**template_vars_dict))
    # TODO: invoke computer setup here
    #ctx.invoke(computer_setup, **computer_setup_args)
    #CliRunner().invoke(computer_setup, **computer_setup_args)

    # # TODO: by default, set up all codes provided for this computer
    # with tempfile.msktemp(mode='w') as handle:

    #     .




#     template = env.from_string(r.content.decode())

#     labels = [ COMP_ENV[key] for key in ['cp2k', 'ddec', 'zeopp', 'raspa']]
#     codes = [ load_code(label) for label in labels]
#     print(f"Exporting {labels}")
#     export(entities=codes, filename=output_file)
    

# if __name__ == '__main__':
#     cli()  #pylint: disable=no-value-for-parameter



# @verdi_computer.command('rename')
# @arguments.COMPUTER()
# @arguments.LABEL('NEW_NAME')
# @deprecated_command("This command has been deprecated. Please use 'verdi computer relabel' instead.")
# @click.pass_context
# @with_dbenv()
# def computer_rename(ctx, computer, new_name):
#     """Rename a computer."""
#     ctx.invoke(computer_relabel, computer=computer, label=new_name)

if __name__ == "__main__":
    computer()