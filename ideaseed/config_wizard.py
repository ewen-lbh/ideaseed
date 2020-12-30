from ideaseed.dumb_utf8_art import ask_text
from os import getenv
from os import path
from os.path import isfile
from typing import *
import shlex


class UnknownShellError(Exception):
    """The current login shell is not known"""


def get_shell_name() -> str:
    """
    Gets the shell name.
    """
    executable_path = getenv("SHELL")
    if not executable_path:
        return ""
    shell_name = path.split(executable_path)[1]
    return shell_name


SHELL_NAMES_TO_RC_PATHS = {
    "fish": "~/.config/fish/config.fish",
    "bash": "~/.bashrc",
    "zsh": "~/.zshrc",
    "csh": "~/.cshrc",
    "ksh": "~/.kshrc",
    "tcsh": "~/.tcshrc",
}


def reverse_docopt(program_name: str, args_map: Dict[str, Any]) -> str:
    """
    Turns a docopt-style dict of arguments and flags into a string
    you would type into your shell (WIP)
    
    >>> reverse_docopt('prog', { '--ab': 4, '--bb': 'yes', '--cb': True, '--db': False, '--eb' ['5', 'fefez$$/./!**fe'], 'thingie': True, 'nothingie': False, 'SHOUT': ':thinking:' })
    'prog --ab --ab --ab --ab --bb=yes --cb --eb=5 --eb=5 --eb="fefez\\$\\$/./\\!\\*\\*fe" thingie :thinking:'
    """
    line = program_name

    for key, value in args_map.items():
        # Arguments
        if not key.startswith("--"):
            # Strings in the command that are either present or not
            if type(value) is bool and value:
                line += f" {key}"
            # Positional arguments
            elif type(value) is str:
                line += f" {value}"
            continue
        # Flag with a value, but is not specified
        if value is None:
            continue
        # Flags with a value
        elif type(value) is str:
            line += f" {key}={shlex.quote(value)}"
        # Count (repeated value-less flag)
        elif type(value) is int:
            line += f" {key}" * value
        # List (repeated flag with value)
        elif type(value) is list:
            for v in value:
                line += f" {key}={shlex.quote(str(v))}"
        # Boolean (value-less flag, ony present if `True`)
        elif type(value) is bool:
            if value:
                line += f" {key}"

    return line


def get_alias_command(args_map: Dict[str, Any], shortcut_name: str) -> str:
    """
    Returns the alias line, sth. like `idea='ideaseed --opt=value --opt2'`, 
    where ``shortcut_name`` is the alias' equation's LHS (`'idea'` in the example above)
    ``args_map`` is a map of options, docopt-style:
    {
        '--option': 'value'
    }
    """
    return (
        "alias "
        + shortcut_name
        + "="
        + "'"
        + reverse_docopt("ideaseed", args_map).replace("'", "\\'")
        + "'"
    )


def write_alias_to_rc_file(shell_name: str, alias_line: str):
    supported_shells = list(SHELL_NAMES_TO_RC_PATHS.keys())
    if shell_name not in supported_shells:
        raise UnknownShellError()

    rcfile_path = path.expandvars(path.expanduser(SHELL_NAMES_TO_RC_PATHS[shell_name]))
    if not isfile(rcfile_path):
        err = FileNotFoundError()
        err.filename = rcfile_path
        raise err

    with open(rcfile_path, "a") as file:
        print(f"Appending the following to {rcfile_path}:\n\n  {alias_line}\n")
        file.writelines([alias_line+'\n'])
        print("Restart your shell or source the file for the new alias to take effect, or execute the 'alias' line above")


def prompt_for_settings() -> Tuple[Dict[str, str], str]:
    """
    Return type: (settings, shortcut_name)
    """

    settings: Dict[str, Any] = {}

    settings["--user-project"] = ask_text(
        "What GitHub project do you use on your GitHub profile?", "--user-project="
    )
    settings["--user-keyword"] = ask_text(
        "What 'repository' name do you want to type to tell ideaseed to use your GitHub user profile's project instead?",
        "--user-keyword=",
    )
    settings["--no-auth-cache"] = (
        not ask_text("Cache credentials? (y/N)").lower().strip().startswith("y")
    )
    settings["--no-check-for-updates"] = (
        not ask_text("Check for updates? (y/N)").lower().strip().startswith("y")
    )
    settings["--no-self-assign"] = (
        not ask_text(
            "Assign yourself to issues if you don't assign anyone with -@ ? (y/N)"
        )
        .lower()
        .strip()
        .startswith("y")
    )
    print(
        """\

For the two following questions, you can use %(placeholders)s.
See https://github.com/ewen-lbh/ideaseed#available-placeholders-for---default--options
for the full list of available placeholders.

"""
    )
    settings["--default-project"] = (
        ask_text(
            "Enter the default value for the project name (default: %(repository)s)",
            "--default-project=",
        )
        or "%(repository)s"
    )
    settings["--default-column"] = (
        ask_text(
            "Enter the default value for the column name (default: To Do)",
            "--default-column=",
        )
        or "To Do"
    )

    return (
        settings,
        ask_text(
            "What name do you want to invoke your configured ideaseed with? (a good one is 'idea')"
        ),
    )


def run():
    settings, shortcut_name = prompt_for_settings()
    alias_command = get_alias_command(settings, shortcut_name)
    shell_name = get_shell_name()
    try_adding_manually_message = f"""\
Try adding the following command to whatever file your shell runs every time it starts:

    {alias_command}

"""
    try:
        write_alias_to_rc_file(shell_name, alias_command)
    except UnknownShellError:
        print(f"Hmm... Seems like I don't know your shell, {shell_name!r}.")
        print(try_adding_manually_message)
        return
    except FileNotFoundError as error:
        print(f"File {error.filename!r} not found.")
        print(try_adding_manually_message)
