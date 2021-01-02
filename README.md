
# Google Drive CLI

# Commands

### `search` - Searches for files that contain a given string 

    search [options] <TERM>

    Used for searching for files that contain or are the string TERM and can optionally use the option '--fuzzy' to 
    fuzzy match the strings so the TERM you give doesnt have to be perfect, only close.

### `pull` - Downloads a remote file to the local disk

    pull [options] <REMOTE> <LOCAL>

    Used for downloading remote files to the local disk from the remote Google Drive server. It is important to note 
    that the LOCAL path defaults to a relative path from the users HOME directory. You can of course still use absolute
    pathing if this is an issue but that is the default relative path if you dont not start your LOCAL save location 
    with '/'.

### `push` - Uploads a file from the local disk to the remote server

    push [options] <LOCAL> <REMOTE>

    Used for uploading a file from the local disk to the remote Google Drive server. As stated in the documentation for 
    'pull' the path given for LOCAL will be relative to the user's HOME directory unless it starts with a '/'. It is 
    almost identical to pull in many ways expect it downloads files from the server instead of uploading them.

### `rm` - Removes a file from the remote server and places it in the trash

    rm [options] <REMOTE>

    Used for removing a file from the remote Google Drive server, normally this means simply moving the file to the 
    trash bin so it can be recovered later if so desired but we can optionally fully delete the file with the -d flag.

### `mv` - Moves a file on the remote server

    mv [options] <START> <END>

### `ls` - Lists all files in a given directory of the remote server

    ls [options]

### `cd` - Changes the current working directory to a given path

    cd [options] <PATH>

### `recover` - Restores a remote file form the trash to its original location

    recover [options] <REMOTE>

    

### `info` - Prints very verbose information on a specific file in Google Drive

    info [options] <REMOTE>

    Will print very verbose information on a single file. This inlues things such as the file name, file id, all tags
    attached to it, sharing information, etc. If there is something you want to know about a file then it can likely 
    be determined through this command.

### `share` - Manages sharing permissions for a given remote file

    share [options] <REMOTE> [EMAIL...]

### `clear` - Clears the shell screen to its initial state

    clear [options]

    Completely clears the screen of all clutter and resets the CLI to the initalize state right after we loaded the 
    application.

### `exit` - Exits the application shell and returns to the normal terminal environment

    exit [options]

    Exits the application and returns the user to the terminal interface that they launched the application from. It
    will also clear the screen of all the clutter created by the application when exiting.

# External Dependencies

### PyDrive2 - `https://pypi.org/project/PyDrive2/`

### Prompt-toolkit - `https://pypi.org/project/prompt-toolkit/`

### FuzzyWuzzy - `https://pypi.org/project/fuzzywuzzy/`

### Python-Levenshtein - `https://pypi.org/project/python-Levenshtein/`
