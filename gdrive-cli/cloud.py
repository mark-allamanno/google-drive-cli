from pathlib import Path
from typing import List

from prompt_toolkit import ANSI
from prompt_toolkit.shortcuts import print_formatted_text, prompt
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from pydrive2.files import GoogleDriveFile

from exceptions import RemotePathNotFound

# A dictionary linking all file extensions to their corresponding export endpoints
SUPPORTED_FILE_TYPES = {
    '.html': 'text/html',
    '.txt': 'plain_text',
    '.rtf': 'application/rtf',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.epub': 'application/epub+zip',
    '.pdf': 'application/pdf',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ods': 'application/x-vnd.oasis.opendocument.spreadsheet',
    '.tsv': 'text/tab-separated-values',
    '.csv': 'text/csv',
    '.jpg': 'images/jpeg',
    '.png': 'images/png',
    '.svg': 'images/svg+xml',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.odp': 'application/vnd.oasis.opendocument.presentation',
    '.json': 'application/vnd.google-apps.script+json'
}


class RemoteDriveInterface:
    """A class to encapsulate all interactions with the Google Drive API"""

    def __init__(self) -> None:

        # Create and authenticate the user
        self.auth = GoogleAuth(settings_file='config/settings.yaml')

        # Then create a new google drive instance and cache all of the files in the drive
        self.drive = GoogleDrive(self.auth)
        self.files = {file['id']: file for file in self.drive.ListFile({'q': "trashed=false"}).GetList()}
        self.trash = {file['id']: file for file in self.drive.ListFile({'q': "trashed=true"}).GetList()}

    @property
    def drive_root(self) -> GoogleDriveFile:
        """
        Get the root parent reference of the user's Google Drive. It is important to remember this is technically not a
        full google drive file as no such file is possible, we instead only get the parent reference which has the id
        of the root which is what we really want.

        Returns:
            parent (GoogleDriveFile): The parent reference to the root node in the google drive
        """

        # We cannot technically access the root normally so we must look at all parent references
        all_parents = [parent for file in self.files.values() for parent in file['parents']]

        # Go through all parent references until we find the one that identifies as the root
        for parent in all_parents:
            if parent['isRoot']:
                return parent

    def update_file_manifest(self) -> None:
        """Updates the local file cache with all remote files. Just queries the API to get the files listings"""

        self.files = {file['id']: file for file in self.drive.ListFile({'q': "trashed=false"}).GetList()}
        self.trash = {file['id']: file for file in self.drive.ListFile({'q': "trashed=true"}).GetList()}

    @staticmethod
    def resolve_mnemonic_conflict(matching_filenames: List[GoogleDriveFile]) -> GoogleDriveFile:
        """
        A function to ask the user to resolve any mnemonic conflicts that can arise because of how google drive
        works. Since Google drive has display names that are not unique since we want to use traditional file pathing
        as much as possible it is possible that a filename may correspond to many different files. In that case we
        need to ask the user which one they meant to reference with their query

        Parameters:
            matching_filenames (List[GoogleDriveFile]): A list of all google drive files matched the query by the user

        Returns:
            file_ids[response] (GoogleDriveFile): The GoogleDriveFile whose ID was entered by the user when prompted
        """

        # Cache a dictionary linking all file ids to their corresponding file objects
        file_ids = {file['id']: file for file in matching_filenames}

        while 1:

            # let the user know what is going wrong before anything else
            print_formatted_text(ANSI("\x1b[31mThere are multiple files with the same filename given!\n"))

            # Until the user provides the info we want keep printing the matching files
            for file in matching_filenames:
                pretty_date = file['modifiedDate'][:file['modifiedDate'].index('.')].replace('T', ' ')
                print_formatted_text(ANSI(f"\x1b[36mDisplay Name: \x1b[37m{file['title']} \x1b[36mLast Modified: "
                                          f"\x1b[37m{pretty_date} \x1b[36mFile ID: \x1b[37m{file['id']}"))

            # Newline for terminal readability and prompt the user to resolve the conflict
            print_formatted_text("")
            response = prompt(ANSI('\x1b[31mPlease copy/paste the ID of the file to which you were referring: '))

            # If the user's response is a valid key then return the associated file
            if response in file_ids.keys():
                return file_ids[response]

    @staticmethod
    def resolve_file_conversion(remote_file: GoogleDriveFile) -> str:
        """
        A function to take in a document type aka one of the keys given from SUPPORTED_FILE_TYPES and along with a
        remote file and return to the caller a string that represents the file extension to use for this file. This
        exists to let users who may not know what conversion are available see all options that are available to them
        given a document type

        Parameters:
            remote_file (GoogleDriveFile): The remote file who we are attempting to get the conversion for

        Returns:
            conversion_opts[user_input] (str): The file extension we are converting this file to
        """

        while 1:

            # Print the helpful prompt on what the user is choosing and cache the supported conversions list for this
            # file
            print_formatted_text(
                ANSI(f"\x1b[36mWhat file type would you like to convert \"{remote_file['title']}\" to?"))
            conversion_opts = [ext for ext, link in SUPPORTED_FILE_TYPES.items() if link in remote_file['exportLinks']]

            # Print out all of the possible conversion's for this document and their associated number
            for choice, conversion in enumerate(conversion_opts):
                print_formatted_text(f"{choice + 1}: {conversion}")

            try:
                # Prompt the user for their choice of the file types printed out above
                user_input = int(prompt(ANSI(f'\x1b[36mChoose [1-{len(conversion_opts)}]: '))) - 1

                # If the user input a valid index then return the conversion extension they desire
                if 0 <= user_input < len(conversion_opts):
                    return conversion_opts[user_input]

            # If the user input a non integer cast-able value then inform them to use the numbers
            except ValueError:
                print_formatted_text(ANSI('\x1b[31mPlease input the number that corresponds to your desired file type'))

    def valid_remote_path(self, file: GoogleDriveFile, remote_path: str, search_trash=False):
        """
        Given a valid remote GoogleDriveFile and a semantic file path validate that using this path we could access
        this same file and if we can then return true if this file path cannot lead us to this file though return False

        Parameters:
            file (GoogleDriveFile): The GoogleDriveFile we are starting from to validate the path
            remote_path (str): The absolute path to the file that we are trying to validate
            search_trash (bool): Lets us know if we want to search for trashed files when validating this path

        Returns:
            A boolean to let us know if the given remote path is valid or not
        """

        # Get all the files to check against, the parent ids of the file, and create a new path 
        files_to_search = list(self.files.values()) + list(self.trash.values()) if search_trash else self.files.values()
        parent_ids = [parent['id'] for parent in file['parents']]
        to_validate = Path(remote_path)

        # If the title of the file is not the same as the last part of the given path then it is trivially false
        if file['title'] != to_validate.name:
            return False

        # If the file name matches the file path and the root node is a parent then it is trivially true
        elif self.drive_root['id'] in parent_ids:
            return True

        # We need to investigate further, look at all files and see if their id matches a parent and attempt to
        # validate them too if non validate correctly then return false
        for check in files_to_search:
            if check['id'] in parent_ids and self.valid_remote_path(check, to_validate.parent,
                                                                    search_trash=search_trash):
                return True

        return False

    def get_remote_file(self, filename: str, trashed=False) -> GoogleDriveFile:
        """
        Using a given file path search the Google Drive instance for any files matching that name and file path. If
        there are many instances of a files that match the given file path and name then prompt the user to specify
        which file they were attempting to access as we cannot determine this for ourselves at this point.

        Parameters:
            filename (str): The absolute remote path of the file we are searching for
            trashed (bool): Lets us know if we want to search the trash for this file

        Returns:
            Either a GoogleDriveFile if one was found that matches or None if no file matched the query
        """

        # Convert the filename to a file path for easier manipulation and create a list of matching file names
        full_path = Path(filename)
        files_to_check = self.trash.values() if trashed else self.files.values()
        matching_files = list()

        # Make sure that the file path is not the root before continuing
        if not full_path.name:
            return self.drive_root

        # Look over all files and if their filename matches the given one then validate that their full paths match
        for file in files_to_check:
            if file['title'] == full_path.name and self.valid_remote_path(file, filename, search_trash=trashed):
                matching_files.append(file)

        # If we match any files then we definitely found a file but may need to resolve a same name issue with user
        if num_matches := len(matching_files):
            return matching_files.pop() if num_matches == 1 else self.resolve_mnemonic_conflict(matching_files)
        else:
            return None

    def get_object_children(self, parent=None, trashed=False) -> List[GoogleDriveFile]:
        """
        Given a parent GoogleDriveFile return a list of all files who have that file in their parents list. This isn't
        particularly complex we just go over every file and add it to children if one of their parent ids is the id
        of the parent we were given. One important not is that if no parent is specified then the Google Drive root
        file will be used as a default.

        Parameters:
            parent (GoogleDriveFile): The parent to the google drive file we are searching for; defaults to root
            trashed (bool): Lets us know if we want to search the trash for children as well
        """

        # Get the files to search, the parent id, and create the list of children
        files_to_check = list(self.trash.values()) + list(self.files.values()) if trashed else self.files.values()
        parent = parent if parent is not None else self.drive_root['id']
        children = list()

        # Go over every file and see if the parents of that file contain the given node
        for file in files_to_check:
            if parent in map(lambda file_parents: file_parents['id'], file['parents']):
                children.append(file)

        return children

    def create_file(self, local_path: str, remote_path: str) -> None:
        """
        Creates a new file in the remote Google Drive server specified by remote_path and will upload the contents of
        local_path into the file. It is important to note that local_path must be a file or else this wont work.

        Parameters:
            local_path (str): The absolute path to the local file we are uploading to the Google Drive
            remote_path (str): The absolute path to the remote file we are creating
        """

        # Get the full path and the parent of the full path before starting
        full_path = Path(remote_path)

        if not full_path.is_file():
            return

        # If the file is not already present in the drive then create a new file and if it is then update it
        if not (duplicate := self.get_remote_file(remote_path)):

            parent = self.create_file_path(full_path.parent)

            # If the parent of the current file is null then dont assign it a parent else give it the current parent
            if parent is None:
                file = self.drive.CreateFile({'title': full_path.name})
            else:
                file = self.drive.CreateFile({'title': full_path.name, 'parents': [{'id': parent['id']}]})

        else:
            file = duplicate

        # Upload the contents of the local file to the remote file 
        file.SetContentFile(local_path)
        file.Upload()

        # Update our local cache to reflect this change
        self.update_file_manifest()

    def create_file_path(self, directory_path: str, recursed=False) -> GoogleDriveFile:
        """
        Creates a new folder in the remote Google Drive instance. Will also create parent directories if we are asked
        to make a subdirectory that doesnt currently exist

        Parameters:
            directory_path (str): The absolute file path we are creating
            recursed (bool): Lets us know whether we have recursed or not so we dont have too many api calls

        Returns:
            parent (GoogleDriveFile): Returns the most recent GoogleDriveFile created
        """

        full_path = Path(directory_path)

        if full_path.name:

            # Assuming the path is valid then create the full path to place this file
            parent = self.create_file_path(full_path.parent, recursed=True)

            # Standard options for creating a new folder in google drive
            file_options = {'title': full_path.name, 'mimeType': 'application/vnd.google-apps.folder'}

            # If the parent is not None then this folder needs a parent
            if parent is not None:
                file_options['parents'] = [{'id': parent['id']}]

            # Check if a folder already exists before creating another one
            if not (duplicate := self.get_remote_file(full_path)):
                folder = self.drive.CreateFile(file_options)
                folder.Upload()

            # Only update the file manifest at the very end
            if not recursed:
                self.update_file_manifest()

            return folder if not duplicate else duplicate

    def download_file(self, remote_path: Path, local_path: Path) -> None:
        """
        Creates a new local copy, with the path local_path, of the remote file remote_path. This function is a one to
        one download provided that the remote file exists. It will only every download the one remote file to the one
        local file.

        Parameters:
            remote_path (Path): The absolute path to the remote file that we are attempting to download
            local_path (Path): The absolute path to the location on the local disk to store the file to
        """

        if remote_file := self.get_remote_file(str(remote_path)):

            parent_dir = local_path.parent
            path_suffix = local_path.suffix

            # If the remote files exists then make sure we have a local dir to read to
            if not parent_dir.exists():
                parent_dir.mkdir()

            # If the remote file if not a proprietary google file then download normally otherwise we need to convert
            if not remote_file['mimeType'].startswith('application/vnd.google-apps.'):
                remote_file.GetContentFile(str(local_path))
            else:
                # Get the suffix of the file and use that to decipher what conversion mimetype to use

                if SUPPORTED_FILE_TYPES.get(path_suffix) in remote_file['exportLinks'].keys():
                    file_suffix = path_suffix
                else:
                    file_suffix = self.resolve_file_conversion(remote_file)
                    local_path = Path(str(local_path) + file_suffix)

                remote_file.GetContentFile(local_path, mimetype=SUPPORTED_FILE_TYPES[file_suffix])
        else:
            raise RemotePathNotFound(remote_path)

    def delete_remote_file(self, remote_item: str, delete_forever=False) -> None:
        """
        Attempts to delete or trash a given remote file whose path is given by remote_item. We will only permanently
        delete the item if the delete_forever flag is set otherwise we just want to send the file to the trash bin

        Parameters:
            remote_item (str): The absolute path to the remote file we want to delete from the Google Drive
            delete_forever (bool): A flag to tell us if we want to delete it permanently instead of trashing it
        """

        if remote_item := self.get_remote_file(remote_item):

            # Assuming the file exists then trash or delete it depending on user preferences
            if not delete_forever:
                remote_item.Trash()
            else:
                remote_item.Delete()

        else:
            raise RemotePathNotFound(remote_item)

        # Update our local cache to reflect this change
        self.update_file_manifest()

    def recover_remote_file(self, remote_item: str) -> None:
        """
        Attempt to recover a given remote file specified by remote_item from the user's Google Drive trash bin if it
        exists there.

        Parameters:
            remote_item (str): The absolute path to the remote file to pull from the trash
        """

        # Make sure the remote item is in the trash before trying to un-trash it
        if remote_item := self.get_remote_file(remote_item, trashed=True):
            remote_item.UnTrash()
        else:
            raise RemotePathNotFound(remote_item)

        # Update our local cache to reflect this change
        self.update_file_manifest()
