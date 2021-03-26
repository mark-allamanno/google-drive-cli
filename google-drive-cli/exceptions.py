from prompt_toolkit import print_formatted_text, ANSI


class GoogleDriveCLIException(Exception):
    """Base exception class for all recoverable exceptions that can occur in our program"""
    pass


class RemotePathNotFound(GoogleDriveCLIException):
    """Exception class for when a path if not found on the remote server"""

    def __init__(self, remote_path):
        super(RemotePathNotFound, self).__init__()
        print_formatted_text(ANSI(f'\x1b[31mPath to remote file "{remote_path}" not found!'))


class UnsupportedFileType(GoogleDriveCLIException):
    """Exception class for when an unsupported file type conversion is attempted by the user when downloading a file"""

    def __init__(self, file_type, accepted_types):
        super(UnsupportedFileType, self).__init__()
        print_formatted_text(
            ANSI(f'\x1b[31mFile type "{file_type}" is an unsupported conversion at this time. Only conversions to '
                 f'{list(accepted_types.keys())} are supported!'))


class RemotePathIsFile(GoogleDriveCLIException):
    """Exception class for when the user thinks they can either path or change directory to a non folder remote file"""

    def __init__(self, remote_path):
        super(RemotePathIsFile, self).__init__()
        print_formatted_text(ANSI(f'\x1b[31mRemote path "{remote_path}"" is a file!'))


class LocalPathNotFound(GoogleDriveCLIException):
    """Exception class fow when the user specifies a local path that does not exist"""

    def __init__(self, local_path):
        super(LocalPathNotFound, self).__init__()
        print_formatted_text(ANSI(f'\x1b[31mLocal path "{local_path}" does not exist on the disk!'))


class PathNotSpecified(GoogleDriveCLIException):
    """Exception class for when the user enters a command that requires a path but none is supplied"""

    def __init__(self):
        super(PathNotSpecified, self).__init__()
        print_formatted_text(ANSI(f'\x1b[31mNo input path was specified!'))


class NoRoleSelected(GoogleDriveCLIException):
    """Exception class for if a file is attempting to be shared without a rule which isn't possible"""

    def __init__(self):
        super(NoRoleSelected, self).__init__()
        print_formatted_text(
            ANSI('No role was given for the command so cannot fulfill request. Use "share --help" to learn more'))


class PermissionNonExistent(GoogleDriveCLIException):
    """Exception class for when the user tries to remove a permission for a user that doesnt exist for a given file"""

    def __init__(self, user):
        super(PermissionNonExistent, self).__init__()
        print_formatted_text(ANSI(f'No permissions exist for the user "{user}" so cannot remove them!"'))


class NoTargetHostGiven(GoogleDriveCLIException):
    """Exception class for when the user tries to add someone to a document but doesnt specific who that should be"""

    def __init__(self):
        super(NoTargetHostGiven, self).__init__()
        print_formatted_text(ANSI('\x1b[31mNo email was given to share the document with and the ""--link" flag was '
                                  'not set'))
