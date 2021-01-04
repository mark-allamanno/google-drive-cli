import getpass
import shlex

from docopt import docopt
from prompt_toolkit import ANSI
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.shortcuts.utils import print_formatted_text

import commands as cli
from exceptions import GoogleDriveCLIException

# A dictionary linking all string commands with their associated function
FUNCTION_COMMANDS = {
    'ls': cli.list_directory,
    'cd': cli.change_directory,
    'push': cli.upload_local_files,
    'pull': cli.download_remote_file,
    'rm': cli.remove_file,
    'mv': cli.move_remote_file,
    'recover': cli.recover_file,
    'info': cli.list_single_file_verbose,
    'share': cli.manage_permissions,
    'search': cli.search_remote_file,
    'clear': cli.clear_screen,
    'exit': cli.exit_shell,
}


def parse_user_input(user_input: str):
    """
    A function to parse user input into a friendly form using the docopt library. We firstly need to split the user
    input on spaces unless in quotation marks (files can have spaces in names) so we need to use shlex to do this and
    subsequently separate teh command given from the arguments. Then we can attempt to return the given command along
    with the arguments parsed out by docopt. We use a simply little trick where we get the get the function pointer for
    the given command and can use __doc__ to get the docstring for docopt parsing with the arguments being everything
    in the user input that is not the command.

    Parameters:
        user_input (str): The string representing the raw user input to the shell application
    """

    # Split the full command into its parts but ignore space in quotes
    full_command = shlex.split(user_input)
    command, arguments = full_command[0], full_command[1:]

    try:
        # Attempt to parse the arguments using docopt and a function pointer to their docstring
        return command, docopt(FUNCTION_COMMANDS[command].__doc__, argv=arguments)
    except (SystemExit, KeyError) as e:

        # If the error was caused by the user issuing a non-valid command then let them know
        if type(e) is KeyError:
            print_formatted_text(ANSI(f'\x1b[31mCommand "{command}" is not recognized as a valid command!'))

        # Otherwise check to make sure they user gave invalid arguments and not asking for help
        elif '-h' not in arguments and '--help' not in arguments:
            print_formatted_text(ANSI(f'\x1b[31mInvalid arguments for command "{command}" -> {arguments}'))

        # Return an empty dictionary to let execute_shell know we failed
        return command, dict()


def execute_shell():
    """
    A function to prompt the user for input and if the user gave valid input then attempt to parse it, if parsing was
    successful then attempt to execute the given command which means grabbing the function pointer from the the
    FUNCTION_COMMANDS dictionary and invoking it with the supplied arguments given that we have defined a function for
    the entered command.
    """

    try:
        # On an execution of the shell we want to prompt the user for input
        user_input = cli.SESSION.prompt(
            ANSI(f"\x1b[32m{getpass.getuser()}@google-drive\x1b[37m:\x1b[34m~{cli.REMOTE_FILE_PATH}\x1b[37m$"),
            auto_suggest=AutoSuggestFromHistory(),
            completer=PathCompleter())

        if user_input:

            # Then we want to parse that input using docopt assuming it was non zero
            command, arguments = parse_user_input(user_input)

            # Make sure that docopt didnt fail or the user asked for a help command and invoke the function
            if arguments:
                FUNCTION_COMMANDS[command](arguments)

    # If we try to create or access files that we are not allowed to then let the user know
    except PermissionError as e:
        print_formatted_text(ANSI(f"\x1b[31mCannot create or access file location '{e.filename}'. Permission denied!"))

    # If a GoogleDriveCLIException is raised then it will print an error message to the user and we can continue
    except GoogleDriveCLIException:
        pass


if __name__ == '__main__':

    cli.clear_screen({})

    while 1:
        execute_shell()
