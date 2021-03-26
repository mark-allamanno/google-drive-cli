from pathlib import Path
from typing import Dict

from fuzzywuzzy import fuzz
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.shortcuts.prompt import PromptSession

from cloud import RemoteDriveInterface
from exceptions import *

# Create a new drive instance, prompt instance, and remote path
DRIVE = RemoteDriveInterface()
SESSION = PromptSession()
REMOTE_FILE_PATH = Path('/')


def ansi_yes_no_prompt(prompt: str) -> str:
    """
    Print an red ANSI prompt (given by the caller) to the screen continuously until the user answers yes or no
    and return their response. Alternatively the user can also type in c to cancel the operation altogether which is
    interpreted the same way as an n but is clearer

    Parameters:
        prompt (str): The prompt to print to the user before taking yes/no input

    Returns:
        decision (str): The either 'y' or 'n' response the user gave to the console
    """

    while 1:

        # Prompt the user for a yes/no response and dont complete until they answer
        decision = SESSION.prompt(ANSI(f'\x1b[31m{prompt} '))

        if decision in 'ync':
            return decision


def change_directory(args: Dict) -> None:
    """

    Change the current working directory to the absolute or relative path given by the user.

    To use absolute pathing we must start the path with a '/' to let the program know we are starting from the root
    node as our reference and working our way down from there. Alternatively if the input does not start with '/' we
    will use relative pathing which means the reference will be the current working directory. Very similar to the bash
    cd command if you are familiar with that.

    Usage:
        cd (--remote=<PATH> | <PATH>)

    Options:
        -h, --help      Shows this screen
    """

    global REMOTE_FILE_PATH

    # Make sure the user did not type in an empty change directory
    if user_input_path := (args['<PATH>'] or args['--remote']):

        # If the user typed in cd / then move back to the root folder
        if user_input_path.startswith('/'):
            REMOTE_FILE_PATH = Path('/')
            user_input_path = user_input_path[1:]

        # If the user typed in cd ../ then move up one folder
        elif user_input_path.startswith('../'):
            REMOTE_FILE_PATH = Path(REMOTE_FILE_PATH.parent)
            user_input_path = user_input_path[3:]

        # Then compute the path we are validating and get the remote folder that represents this path
        path_to_follow = REMOTE_FILE_PATH / user_input_path
        folder = DRIVE.get_remote_file(path_to_follow)

        # If we found a matching folder and it isn't a file then "move" there otherwise print a help message
        if folder and (folder == DRIVE.drive_root or folder['mimeType'] == 'application/vnd.google-apps.folder'):
            REMOTE_FILE_PATH = path_to_follow

        # If no file path exists then the user is trying to go somewhere that doesnt exist
        elif not folder:
            raise RemotePathNotFound(path_to_follow)

        # Otherwise the object exists but is a file instead of a folder
        else:
            raise RemotePathIsFile(path_to_follow)

    else:
        raise PathNotSpecified()


def list_directory(args: Dict) -> None:
    """

    List all files in a given directory as we would do in a typical bash shell environment. Typically we would just type
    in ls to list all of the files in a given directory but we also have some arguments to augment the feature set of
    this command.

    Short explanations are below but we can alternatively user --dir to specific an absolute or relative path of a
    directory to list the contents of. We can also use something like --verbose to list some more information about
    each file then would normally be displayed. You get the idea, once again it is quite similar to bash shell
    environment ls.

    Usage:
        ls [--remote=<PATH>] [options]

    Options:
        -l, --verbose   List all files with verbose information
        -a, --all       List all files in this directory even if they are trashed
        -s, --starred   Only list files who are marked as starred in google drive
        -h, --help      Show this screen
    """

    # Get all of the children of the parent and decode the line ending for formatted printing
    remote_path = args['--remote'] or REMOTE_FILE_PATH
    remote_file = DRIVE.get_remote_file(remote_path, trashed=args['--all'])
    all_children = DRIVE.get_object_children(remote_file['id'], trashed=args['--all'])

    for idx, obj in enumerate(all_children):

        # If the user only wants to list starred files and this one is not starred then skip
        if args['--starred'] and not obj['labels']['starred']:
            continue

        # Determine the end line character and the verbose info string for this iteration
        end_line = ' ' if (idx % 5 or idx == 0) and not args['--verbose'] else '\n'
        verbose_info = ''

        # If the user asked for verbose info then create the verbose info string and reassign it from the default
        if args['--verbose']:
            pretty_date = obj['modifiedDate'][:obj['modifiedDate'].index('.')].replace('T', ' ')
            verbose_info = f"\x1b[36mOwners: \x1b[37m{obj['ownerNames']} \x1b[36mModified: \x1b[37m{pretty_date} " \
                           f"\x1b[36mFile ID: \x1b[37m{obj['id']} "

        # If the filetype is a folder then print it as purple, files are cyan, and trashed are red (only for -a flag)
        if obj['labels']['trashed']:
            print_formatted_text(ANSI(f"{verbose_info}\x1b[31m{obj['title']:20s}"), end=end_line)

        elif obj['mimeType'] == 'application/vnd.google-apps.folder':
            print_formatted_text(ANSI(f"{verbose_info}\x1b[35m{obj['title']:20s}"), end=end_line)

        else:
            print_formatted_text(ANSI(f"{verbose_info}\x1b[36m{obj['title']:20s}"), end=end_line)

    # Then print a newline at the end for separation
    print_formatted_text("")


def upload_local_files(args: Dict, recursed=False) -> None:
    """

    Uploads a file present on the local disk specified by LOCAL to the remote Google Drive server in location REMOTE

    A couple important things to bear in mind is that when attempting to upload a folder it works but will requite the
    --folder flag. However even when doing this it will not upload any sub-folders unless '--recursive' is also set so
    we also upload sob-folders else only immediate files of the specified folder will be uploaded to the server.

    Usage:
        push [options] (--local=<LOCAL> | <LOCAL>) (--remote=<REMOTE> | <REMOTE>)

    Options:
        -f, --folder        Use this flag if we want to upload the contents of a folder
        -r, --recursive     Recurse down the directory and upload all sub-folders
        -h, --help          Shows this screen
    """

    remote = args['<REMOTE>'] or args['--remote']
    local = args['<LOCAL>'] or args['--local']

    # Use the absolute path if the user wants otherwise use the relative path from the cwd
    remote_path = Path(remote) if remote.startswith('/') else REMOTE_FILE_PATH / remote
    local_path = Path(local) if local.startswith('/') else Path.home() / local

    # Make sure the local path exists before attempting to upload it
    if not local_path.exists():
        raise LocalPathNotFound(local_path)

    # Then make sure the remote path exists or the user is okay with creating it
    if not DRIVE.get_remote_file(remote_path) and not recursed:
        if ansi_yes_no_prompt('Remote path does not exist. Create anyways (y/n/c)?') in 'nc':
            return

    if args['--folder'] and local_path.is_dir():  # Make sure that folder option is enabled with folders

        for file in local_path.iterdir():  # Iterate over all files in the source directory

            # Get the local and remote path's for the files to be placed
            absolute_local, absolute_remote = str(file), str(remote_path / file.name)

            # If the file is a directory and we are uploading recursively then recursively upload that folder
            if file.is_dir() and args['--recursive']:
                recur_args = args.copy()
                recur_args['<LOCAL'], recur_args['<REMOTE>'] = absolute_local, absolute_remote
                upload_local_files(recur_args, recursed=True)

            # Otherwise just upload the file like normal
            elif file.is_file():
                DRIVE.create_file(absolute_local, absolute_remote)

    # If the user wants to upload a single file then just upload it easily
    elif local_path.is_file():
        DRIVE.create_file(local_path, remote_path)

    # Otherwise the user is trying to upload a folder without the proper flag so let them know
    else:
        print_formatted_text(ANSI('\x1b[31mThe given local path is a directory, use the "--folder" option if you wish '
                                  'to upload a directories'))


def download_remote_file(args: Dict, parent_folder=None, recursed=False) -> None:
    """

    Download a given remote file or folder specified by REMOTE and save it to a local location LOCAL

    Usage:
        pull [options] (--remote=<REMOTE> | <REMOTE>) (--local=<LOCAL> | <LOCAL>)

    Options:
        -f, --folder        Use this flag if we want to upload the contents of a folder
        -r, --recursive     Recurse down the folder and download all sub-folders
        -h, --help          Shows this screen
    """

    remote = args['<REMOTE>'] or args['--remote']
    local = args['<LOCAL>'] or args['--local']

    # Use the absolute path if the user starts from the root, otherwise use the relative path from the cwd
    remote_path = Path(remote) if remote.startswith('/') else REMOTE_FILE_PATH / remote
    local_path = Path(local) if local.startswith('/') else Path.home() / local
    remote_file = DRIVE.get_remote_file(remote_path) if parent_folder is None else parent_folder

    # Make sure the local path either exists or the user is okay with creating it
    if not local_path.parent.exists() and not recursed:
        if ansi_yes_no_prompt('Local path does not exist. Create anyways (y/n/c)?') in 'nc':
            return

    if remote_file:  # Make sure the remote file is present on the server before trying to download it

        if args['--folder'] and remote_file['mimeType'] == 'application/vnd.google-apps.folder':

            for drive_file in DRIVE.get_object_children(remote_file['id']):

                # Get the local and remote path's for the files
                absolute_local, absolute_remote = local_path / drive_file['title'], remote_path / drive_file['title']

                # If the file is a directory and we are uploading recursively then recursively download the folder
                if drive_file['mimeType'] == 'application/vnd.google-apps.folder' and args['--recursive']:
                    recur_args = args.copy()
                    recur_args['<LOCAL>'], recur_args['<REMOTE>'] = str(absolute_local), str(absolute_remote)
                    download_remote_file(recur_args, parent_folder=drive_file, recursed=True)

                # Otherwise just download the single file as normal
                else:
                    DRIVE.download_file(absolute_remote, absolute_local)

        # If the user is trying to download a folder without the proper flags then let them know
        elif remote_file['mimeType'] == 'application/vnd.google-apps.folder':
            print_formatted_text(ANSI('\x1b[31mThe given local path is a directory, use the "--folder" option if you '
                                      'wish to upload a directories'))

        # Otherwise just download the singular file as normal
        else:
            DRIVE.download_file(remote_path, local_path)

    # Otherwise let the user know they are trying to download an non-existent file
    else:
        raise RemotePathNotFound(remote_path)


def list_single_file_verbose(args: Dict):
    """

    Prints out very verbose information about this remote file, which includes but is not limited to, the date last
    modified, date created, owner, various file information, and much more.

    Usage:
        info [options] (--remote=<REMOTE> | <REMOTE>)

    Options:
        -h, --help      Shows this screen
    """

    # Get the remote path of the file/folder to print out the verbose information for
    remote = args['<REMOTE>'] or args['--remote']
    remote_path = Path(remote) if remote.startswith('/') else REMOTE_FILE_PATH / remote

    if remote_file := DRIVE.get_remote_file(remote_path):  # Get the google drive file of this path

        file_permissions = remote_file.GetPermissions()

        # Print newline character to separate from input line for readability
        print_formatted_text("")

        # Preparse the modified and created dates into their pretty forms
        pretty_mod_date = remote_file['modifiedDate'][:remote_file['modifiedDate'].index('.')].replace('T', ' ')
        pretty_create_date = remote_file['createdDate'][:remote_file['createdDate'].index('.')].replace('T', ' ')

        # Then print the important identifying information about this file
        print_formatted_text(ANSI(f"\x1b[35mIdentifying Information"))
        print_formatted_text(ANSI(f"\x1b[36mDisplay Name: \x1b[37m{remote_file['title']}"))
        print_formatted_text(ANSI(f"\x1b[36mInternal File ID: \x1b[37m{remote_file['id']}"))
        print_formatted_text("")

        # Then print the labels that the file has attached to it that the end user would care about
        print_formatted_text(ANSI(f'\x1b[35mFile Labels'))

        for label, label_val in remote_file['labels'].items():
            if label_val:
                print_formatted_text(ANSI(f'\x1b[37m{label.title()}'), end=', ')

        if remote_file['copyable']:
            print_formatted_text(ANSI(f'\x1b[37mCopyable'), end=', ')

        if remote_file['editable']:
            print_formatted_text(ANSI(f'\x1b[37mEditable'), end=', ')

        print_formatted_text("\n")

        # Then print some metadata statistics about this file
        print_formatted_text(ANSI(f"\x1b[35mMetadata"))
        print_formatted_text(ANSI(f"\x1b[36mDate Created: \x1b[37m{pretty_create_date}"))
        print_formatted_text(ANSI(f"\x1b[36mLast Modified: \x1b[37m{pretty_mod_date}"))
        print_formatted_text(ANSI(f"\x1b[36mFile Type: \x1b[37m{remote_file['mimeType']}"))
        print_formatted_text("")

        # Then print all users who are in the owners group of this file
        print_formatted_text(ANSI("\x1b[35mOwners"))

        for user in remote_file['ownerNames']:
            print_formatted_text(ANSI(f"\x1b[37m{user}"), end=', ')

        print_formatted_text("\n")

        # Then print some simple sharing information about this file
        print_formatted_text(ANSI(f"\x1b[35mSharing Information"))
        print_formatted_text(ANSI(f"\x1b[36mShared With Others: \x1b[37m{remote_file['shared']}"))
        print_formatted_text(ANSI(f"\x1b[36mSharing Link Active: \x1b[37m"
                                  f"{'anyoneWithLink' in [perm['id'] for perm in file_permissions]}"))
        print_formatted_text(ANSI(f"\x1b[36mSharing Link: \x1b[37m{remote_file['alternateLink']}"))
        print_formatted_text("")

        # Finally print all users who have access to this file
        print_formatted_text(ANSI(f"\x1b[35mUser Permissions"))

        for user in file_permissions:
            if user['id'] != 'anyoneWithLink':
                print_formatted_text(ANSI(f"\x1b[36mName: \x1b[37m{user['name']} \x1b[36mEmail: \x1b[37m"
                                          f"{user['emailAddress']} \x1b[36mRole: \x1b[37m{user['role']}"))

        # Finally separate with newline from the following input line
        print_formatted_text("")


def manage_permissions(args: Dict):
    """

    Manage the sharing permissions of a specific file

    Usage:
        share [--add | --delete] [--link] [--reader | --writer | --owner] (--remote=<REMOTE> | <REMOTE>) [EMAILS ...]

    Options:
        -a, --add       Adds permissions for some user's email or creates a new sharing link
        -d, --delete    Deletes a specific permission for a user or sharing link
        -l, --link      Creates a new sharing link for the given remote file
        -r, --reader    Set the permission for this email/link to be read access only
        -w, --writer    Set the permission for this email/link to be read/write access
        -o, --owner     Set the permission for this email/link to be full ownership
        -q, --quiet     Do not raise errors if we try and add invalid emails or remove non-existent permissions
        -h, --help      Shows this message
    """

    # Get the remote path of the file/folder to share with people
    remote = args['<REMOTE>'] or args['--remote']
    remote_path = Path(remote) if remote.startswith('/') else REMOTE_FILE_PATH / remote

    if remote_file := DRIVE.get_remote_file(remote_path):  # Make sure the object actually exists first

        if args['--add']:  # We are adding permissions to the file

            # If we are adding permissions then iterate over all of the args in items and set the role_input var to
            # whichever role_flag is set [-r, -w, -o]
            role_input = None

            for role, val in args.items():
                if val and role in ['--writer', '--reader', '--owner']:
                    role_input = role.replace('-', '')

            if role_input is not None:  # If we are adding a valid role then progress further

                # Get the sharing type and accessors depending on if we are trying to make a sharing link or share with
                # specific people
                share_type = 'anyone' if args['--link'] else 'user'
                who_can_access = ['anyone'] if args['--link'] else args['EMAILS']

                # Iterate over all emails in the accessors list and update the permissions to let them in
                for email in who_can_access:
                    remote_file.InsertPermission({
                        'type': share_type,
                        'value': email,
                        'role': role_input,
                        'withLink': args['--link']
                    })

                # If the list of accessors is empty then the user needs to be told they used the command wrong
                if not who_can_access and not args['--quiet']:
                    raise NoTargetHostGiven()

                # If the user is trying to make a sharing link then print it to the console
                if args['--link']:
                    print_formatted_text(ANSI(f"\x1b[36mSharable Link: {remote_file['alternateLink']}"))

            # If no role is given for the add command then we have a problem and cannot continue
            else:
                raise NoRoleSelected()

        elif args['--delete']:  # We are trying to delete a permissions from the file

            if not args['--link']:  # If we are only trying to remove certain people from the file then do so

                # If the user is not attempting to delete a sharing link then they should have input emails to delete
                # so iterate over the permissions to find them
                valid_users = set()

                for user in remote_file.GetPermissions():

                    # If we come across a user with the given email address then delete their permissions
                    if (email := user.get('emailAddress')) in args['EMAILS']:
                        remote_file.DeletePermission(user['id'])
                        valid_users.add(email)

                # If not all emails given are present in the permissions for the file then let the user know
                if not valid_users == set(args['EMAILS']) and not args['--quiet']:
                    raise PermissionNonExistent(set(args['EMAILS']) - valid_users)

            # Otherwise we know the user is trying to delete a share link and can skip iteration
            else:
                remote_file.DeletePermission('anyoneWithLink')

    else:
        raise RemotePathNotFound(remote_path)


def move_remote_file(args: Dict):
    """

    Moves a remote file to a different location on the server.

    Usage:
        mv [options] (--remote-source=<SOURCE> | <SOURCE>) (--remote-dest=<DEST> | <DEST>)

    Options:
        -h, --help      Shows this message
    """

    source = args['<SOURCE>'] or args['--remote-source']
    dest = args['<DEST>'] or args['--remote-dest']

    # Get the full path's for both the current file location and the destination location
    remote_source = Path(source) if source.startswith('/') else REMOTE_FILE_PATH / source
    remote_dest = Path(dest) if dest.startswith('/') else REMOTE_FILE_PATH / dest

    # Then get the actual google drive files for the parent of the current location and the destination parent
    source_parent = DRIVE.get_remote_file(remote_source.parent.name)
    dest_parent = DRIVE.get_remote_file(remote_dest.parent.name)

    if (remote_file := DRIVE.get_remote_file(remote_source)) and source_parent:

        # If we have a valid remote file but the destination parent doesnt exist yet then create it if the user wants
        if dest_parent is None:

            if ansi_yes_no_prompt('Remote destination does not exist. Create anyways (y/n/c)?') in 'nc':
                return

            dest_parent = DRIVE.create_file_path(remote_dest.parent)

        # Make sure the mimetype of the file is correct as we cannot parent to a non folder and update the metadata
        if dest_parent.get('mimeType', 'application/vnd.google-apps.folder') == 'application/vnd.google-apps.folder':

            parents = [{'id': parent['id']} for parent in remote_file['parents'] if parent['id'] != source_parent['id']]
            parents.append({'id': dest_parent['id']})

            remote_file['title'], remote_file['parents'] = remote_dest.name, parents
            remote_file.Upload()

        # If the remote destination was a non folder type then let the user know they cannot do that
        else:
            raise RemotePathIsFile(args['<DEST>'])

    # If the remote file is not found then let the user know that there is no such file
    else:
        raise RemotePathNotFound(remote_source)


def search_remote_file(args: Dict):
    """

    Searches for a file with a given term present in its filename. So if I were to say 'search Mario' it would go
    through all files and print out the absolute paths to files who contain the keyword Mario in them.

    Alternatively you can also use the -f flag if you arent unsure of the name or sub-term of a file in which case it
    will use fuzzy string matching to attempt to find all files names who contain close but not absolutely the same
    string.

    Usage:
        search [options] <TERM>

    Options:
        -f, --fuzzy     Use fuzzy string matching if you arent sure of the exact name or sub-name
        -h, --help      Shows this message
    """

    # Define a quick function to return a list of all possible paths to a given file
    def determine_file_path(remote_file):

        paths = list()  # List to insert all paths into

        # If the remote file we are given is the root then we can simply return the root character in POSIX paths
        if remote_file['id'] == DRIVE.drive_root['id']:
            return ['/']

        # If we are a non-root file then we need to look at the paths for all parents and extend them with ourselves
        for parent in map(lambda f: DRIVE.files.get(f['id'], DRIVE.drive_root), remote_file['parents']):

            # Get all of the possible paths to this parent of our file and merge them with the current file
            for parent_path in determine_file_path(parent):
                partial_path = Path(parent_path, DRIVE.files[remote_file['id']]['title'])
                paths.append(partial_path.as_posix())

        # Return all of the paths to this file from all of its parents
        return paths

    # This function will use strict matching ie the input has to be the same
    def strict_match(user_input, title):
        return user_input in title

    # This function will use fuzzy matching ie the input has to be kinda close to the file name and it will catch it
    def fuzzy_match(user_input, title):
        return 80 <= fuzz.partial_token_sort_ratio(user_input, title)

    # Decide which kind of matching we want to use in our file search
    string_match_func = fuzzy_match if args['--fuzzy'] else strict_match

    # Then we want to look at all files and check for a potential match
    for file in DRIVE.files.values():

        # If we are determined to have matched then get all potential paths to this file and print them to the console
        if string_match_func(args['<TERM>'], file['title']):
            for potential_path in determine_file_path(file):
                print_formatted_text(ANSI(f'\x1b[36m{potential_path}'))


def remove_file(args: Dict):
    """

    Moves a given remote file into the trash bin, this action can be undone by using the restore command to pull it
    from the trash bin to its original location. If normally un-trashed we can recover as discussed before but if the
    -d flag is set the file is irrevocably deleted from the server and cannot be recovered so use with care.

    Usage:
        rm [options] (--remote=<REMOTE> | <REMOTE>)

    Options:

        -d, --delete    Do not just trash this file, delete it immediately forever
        -h, --help      Shows this message
    """

    # Get the remote path to a file and then use the drive to delete it
    remote = args['<REMOTE>'] or args['--remote']
    remote_path = Path(remote) if remote.startswith('/') else REMOTE_FILE_PATH / remote
    DRIVE.delete_remote_file(remote_path)


def recover_file(args: Dict):
    """

    Remove a file from the trash bin and restore it to its original place in the remote drive

    Usage:
        restore (--remote=<REMOTE> | <REMOTE>)

    Options:
        -h, --help      Shows this message
    """

    # Get the remote path to a file and then use the drive to un-delete it
    remote = args['<REMOTE>'] or args['--remote']
    remote_path = Path(remote) if remote.startswith('/') else REMOTE_FILE_PATH / remote
    DRIVE.recover_remote_file(remote_path)


def clear_screen(args: Dict):
    """

    Clears the screen and resets the prompt to the top left hand corner of the terminal just as in bash shell

    Usage:
        clear [options]
    
    Options:
        -h, --help      Shows this message
    """

    clear()  # Clear the screen with the built in macro


def exit_shell(args: Dict):
    """

    Exits the shell interface for Google Drive and return back to the normal OS environment. Also clears the screen
    on exit for convenience

    Usage:
        exit [options]
    
    Options:
        -h, --help
    """

    # Exit the program with exit code zero and clear the screen
    clear_screen(args)
    exit(0)
