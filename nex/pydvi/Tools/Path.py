import os
import types


def to_absolute_path(path):

    # Expand ~ . and Remove trailing '/'

    return os.path.abspath(os.path.expanduser(path))


def parent_directory_of(file_name, step=1):

    directory = file_name
    for i in range(step):
        directory = os.path.dirname(directory)
    return directory


def find(file_name, directories):

    if isinstance(directories, bytes):
        directories = (directories,)
    for directory in directories:
        for directory_path, sub_directories, file_names in os.walk(directory):
            if file_name in file_names:
                return os.path.join(directory_path, file_name)

    raise NameError("File %s not found in directories %s" %
                    (file_name, str(directories)))
