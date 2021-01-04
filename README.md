
# Google Drive CLI

# Commands

#### `search` - Searches for files that contain a given string 

    search [options] <TERM>

    Used for searching for files that contain or are the string TERM and can optionally use the 
    option '--fuzzy' to fuzzy match the strings so the TERM you give doesnt have to be perfect, 
    only close.

#### `pull` - Downloads a remote file to the local disk

    pull [options] <REMOTE> <LOCAL>

    Used for downloading remote files to the local disk from the remote Google Drive server. It
    is important to note that the LOCAL path defaults to a relative path from the users HOME 
    directory. You can of course still use absolute pathing if this is an issue but that is the
    default relative path if you dont not start your LOCAL save location with '/'.

#### `push` - Uploads a file from the local disk to the remote server

    push [options] <LOCAL> <REMOTE>

    Used for uploading a file from the local disk to the remote Google Drive server. As stated 
    in the documentation for 'pull' the path given for LOCAL will be relative to the user's HOME
    directory unless it starts with a '/'. It is almost identical to pull in many ways expect it
    downloads files from the server instead of uploading them.

#### `rm` - Removes a file from the remote server and places it in the trash

    rm [options] <REMOTE>

    Used for removing a file from the remote Google Drive server, normally this means simply 
    moving the file to the trash bin so it can be recovered later if so desired but we can 
    optionally fully delete the file with the -d flag.

#### `mv` - Moves a file on the remote server

    mv [options] <START> <END>

    Used for moving a file from a starting destination to an ending destination. It works almost
    exactly like the bahs shell mv, so it os not only used for moving files to other directories
    but can also be used as a way to rename files by moving a source file to the same directory
    under a different name.

#### `ls` - Lists all files in a given directory of the remote server

    ls [options]

    Lists all of the files in the current working drectory, this can optionally be a verbose output
    but by default will only print the file names and can also list the contents of another directory
    than the CWD but you will need to use --dir with the absolute path to the folder you want to list.

#### `cd` - Changes the current working directory to a given path

    cd [options] <PATH>

    Used for when we wan tto change the current working directory on the remote server so that we 
    can then use shorter relative paths from there instead of putting in longer absokute paths from
    the root.

#### `recover` - Restores a remote file form the trash to its original location

    recover [options] <REMOTE>

    Used for when we need to recover a file that has been placed in the trash on teh remote server.
    When recovered it will be placed in its original location on the server before it was trashed.

#### `info` - Prints very verbose information on a specific file in Google Drive

    info [options] <REMOTE>

    Will print very verbose information on a single file. This inlues things such as the 
    file name, file id, all tags attached to it, sharing information, etc. If there is something
    you want to know about a file then it can likely be determined through this command.

#### `share` - Manages sharing permissions for a given remote file

    share [options] <REMOTE> [EMAILS...]

    Used for managing permission of a single remote GoogleDriveFile, curently you can make a shareable
    link to send to others, or add specific emails to share the GoogleDriveFile with. When sharing you
    need to input -r, -o, or -w to let the command know if the person or link you are adding is for
    reading, writing or ownership permissions.

#### `clear` - Clears the shell screen to its initial state

    clear [options]

    Completely clears the screen of all clutter and resets the CLI to the initalize state
    right after we loaded the application.

#### `exit` - Exits the application shell and returns to the normal terminal environment

    exit [options]

    Exits the application and returns the user to the terminal interface that they launched 
    the application from. It will also clear the screen of all the clutter created by the 
    application when exiting.

# External Dependencies

#### PyDrive2 - `https://pypi.org/project/PyDrive2/`

#### Prompt-toolkit - `https://pypi.org/project/prompt-toolkit/`

#### FuzzyWuzzy - `https://pypi.org/project/fuzzywuzzy/`

#### Python-Levenshtein - `https://pypi.org/project/python-Levenshtein/`
