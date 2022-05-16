"""
Utilities for dealing with a registry of computers and codes.

"""
import copy
import functools
import json
import logging
import os
from pathlib import Path
import pprint
from typing import Union

from frozendict import frozendict
import jinja2
from voluptuous import Any, Optional, Required, Schema
import yaml

from aiida import common, orm
from aiida.orm.utils.builders.code import CodeBuilder
from aiida.orm.utils.builders.computer import ComputerBuilder

THIS_DIR = Path(__file__).parent.absolute()
CONFIGURATIONS_DIR = THIS_DIR.parent / "configurations"

NUMBER = Any(float, int)

logger = logging.getLogger()

_JINJA_ENV = jinja2.Environment(loader=jinja2.BaseLoader)

# Code schemas
CODE_SETUP_SCHEMA = {
    "label": str,
    "description": str,
    "computer": str,
    "on_computer": bool,
    "remote_abs_path": str,
    Required("input_plugin"): str,
    Optional("use_double_quotes", default=False): bool,
    "prepend_text": str,
    "append_text": str,
}

# Computer schemas
COMPUTER_SETUP_SCHEMA = {
    "label": str,
    Required("hostname"): str,
    "description": str,
    Required("transport"): str,
    "scheduler": str,
    "work_dir": str,
    "append_text": str,
    "prepend_text": str,
    "shebang": str,
    Optional("use_double_quotes", default=False): bool,
    "mpirun_command": str,
    "mpiprocs_per_machine": int,
    Optional("default_memory_per_machine", default=None): Any(int, None),
    "extras": dict,
}

COMPUTER_CONFIGURE_SSH_SCHEMA = {
    "timeout": NUMBER,
    "safe_interval": NUMBER,
    "compress": bool,
    "key_policy": str,
}

COMPUTER_CONFIGURE_LOCAL_SCHEMA = {}

COMPUTER_CONFIGURE_SCHEMA = {
    "core.local": COMPUTER_CONFIGURE_LOCAL_SCHEMA,
    "core.ssh": COMPUTER_CONFIGURE_SSH_SCHEMA,
}


COMPUTER_SCHEMA = {
    Required("label"): str,
    Required("setup"): COMPUTER_SETUP_SCHEMA,
    "configure": COMPUTER_CONFIGURE_SCHEMA,
    "codes": [CODE_SETUP_SCHEMA],
}

# Registry schema
CODE_REGISTRY_SCHEMA = {
    Required("computers"): [COMPUTER_SCHEMA],
    "codes": [CODE_SETUP_SCHEMA],
}

SCHEMA = Schema(CODE_REGISTRY_SCHEMA, required=False)

@functools.lru_cache(maxsize=3)
def load_code_registry(directory: str) -> dict:
    """Load AiiDA code registry data from directory."""
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(
            f"{directory} is not a Path. Use the 'AIIDA_CODE_REGISTRY' variable to point to a directory."
        )

    yamls = list(directory.glob("*.yaml")) + list(directory.glob("*.yml"))

    if not yamls:
        raise ValueError(f"No YAML files found in {directory}.")

    registry = {}
    for yaml_path in yamls:
        with open(yaml_path, encoding="utf8") as handle:
            data = yaml.safe_load(handle)

        data = SCHEMA(data)
        registry[yaml_path.name] = data

    return registry


def _replace_template_vars(template, template_vars):
    """Replace template variables in JSON-serializable python object.

    Uses jinja2 templating mechanism plus intermediate serialization to json.
    """
    # render even if no template vars provided (will raise if unreplaced template is detected)
    if template_vars is None:
        template_vars = {}
    dict_str = json.dumps(template)
    jinja_template = _JINJA_ENV.from_string(dict_str)
    dict_str = jinja_template.render(**template_vars)

    return json.loads(dict_str)


class CodeRegistry:
    """Code registry with convenience functions."""

    @classmethod
    def from_directory(cls, directory: Union[str, Path]):
        """Load AiiDA code registry from directory."""
        return cls(raw=load_code_registry(directory))

    @classmethod
    def from_env(cls):
        """Load AiiDA code registry from environment.

        Precedence:
        - Value of 'AIIDA_CODE_REGISTRY' environment variable
        - ../configurations
        """
        directory = os.getenv("AIIDA_CODE_REGISTRY")

        if directory is None:
            directory = CONFIGURATIONS_DIR

        return cls.from_directory(directory)

    def __init__(self, raw: dict):
        """Create AiiDA code registry data from raw dict."""
        self._raw = raw

        # now merge the raw yaml data
        computers = {}
        for _file_name, file_content in copy.deepcopy(raw).items():
            data = file_content

            for computer in data["computers"]:
                label = computer["label"]
                if label in computers:
                    logger.warning(
                        "Computer '%s' found in registry multiple times, overwriting.",
                        label,
                    )

                # label is optional in 'setup' to avoid duplication
                if "label" not in computer["setup"]:
                    computer["setup"]["label"] = label

                if "codes" not in computer:
                    computer["codes"] = []

                # codes specified at top level are added to each computer
                if "codes" in data:
                    computer["codes"] += data["codes"]

                # make sure codes specify the correct computer (can be left out in yaml)
                for code in computer["codes"]:
                    code["computer"] = label

                # transform codes into dictionary
                computer["codes"] = {code["label"]: code for code in computer["codes"]}

                computers[label] = computer

        self.computers = computers

    @property
    def computer_list(self) -> list:
        """Return list of available computers."""
        return list(self.computers.keys())

    def get_computer(self, label) -> dict:
        """Return configuration for given computer."""
        return self.computers[label]

    @property
    def code_list(self) -> list:
        """Return list of available codes."""
        code_labels = []
        for computer_label, computer in self.computers.items():
            for code_label in computer["codes"]:
                code_labels.append(f"{code_label}@{computer_label}")

        return code_labels

    def get_code(self, label) -> dict:
        """Return configuration for given code.

        Note: Label needs to be of form 'code@computer'.
        """
        if "@" not in label:
            raise ValueError(f"Label '{label}' is not of form 'code@computer'.")

        code_label, computer_label = label.split("@")
        return self.computers[computer_label]["codes"][code_label]

    def render(self, template_vars: dict):
        """Return copy of registry where template variables have been replaced."""
        if not template_vars:
            return self

        return self.__class__(raw=_replace_template_vars(self._raw, template_vars))


AIIDA_CODE_REGISTRY = CodeRegistry.from_env()


def load_computer(label: str, template_vars: dict = None) -> orm.Computer:
    """Load computer; create if it does not exist.

    :param label: computer label
    :param template_vars: dictionary with template variables to be replaced
    """
    try:
        return orm.load_computer(label=label)
    except common.NotExistent as exc:
        computer_list = AIIDA_CODE_REGISTRY.render(template_vars).computer_list
        if label not in computer_list:
            raise common.NotExistent(
                f"Computer '{label}' found neither in database nor in registry. Computers in registry: {pprint.pformat(computer_list)}"
            ) from exc

    cfg = AIIDA_CODE_REGISTRY.render(template_vars).get_computer(label)
    if "extras" in cfg["setup"]:
        # do custom setup...
        del cfg["setup"]["extras"]
    computer_builder = ComputerBuilder(**cfg["setup"])
    logger.info("Setting up computer '%s'.", label)
    computer = computer_builder.new().store()

    user = orm.User.collection.get_default()

    try:
        configure_dict = cfg["configure"][cfg["setup"]["transport"]]
    except KeyError as exc:
        raise KeyError(
            f"Computer '{label}' is missing configure info for transport '{cfg['setup']['transport']}'."
        ) from exc

    logger.info(
        "Configuring computer '%s' for '%s' transport.",
        label,
        cfg["setup"]["transport"],
    )
    computer.configure(user=user, **configure_dict)

    return computer


def load_code(label: str, template_vars: dict = None) -> orm.Code:
    """Load code; create if it does not exist.

    :param label: code label
    :param template_vars: dictionary with template variables to be replaced
    """
    try:
        return orm.load_code(label=label)
    except common.NotExistent as exc:
        code_list = AIIDA_CODE_REGISTRY.render(template_vars).code_list
        if label not in code_list:
            raise common.NotExistent(
                f"Code '{label}' found neither in database nor in registry. Codes in registry: {pprint.pformat(code_list)}"
            ) from exc

    setup_dict = AIIDA_CODE_REGISTRY.render(template_vars).get_code(label).copy()
    if setup_dict.pop("on_computer"):
        setup_dict["code_type"] = CodeBuilder.CodeType.ON_COMPUTER
    else:
        setup_dict["code_type"] = CodeBuilder.CodeType.STORE_AND_UPLOAD

    # create computer, if it does not exist
    setup_dict["computer"] = load_computer(
        label=setup_dict["computer"], template_vars=template_vars
    )

    code_builder = CodeBuilder(**setup_dict)

    return code_builder.new().store()
