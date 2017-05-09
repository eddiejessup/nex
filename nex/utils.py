import os
from os import path as opath
import base64
import uuid


ascii_characters = ''.join(chr(i) for i in range(128))


def get_unique_id():
    raw = uuid.uuid4()
    compressed = base64.urlsafe_b64encode(raw.bytes).decode("utf-8")
    sanitised = compressed.rstrip('=\n').replace('/', '_')
    return sanitised


class NoSuchControlSequence(Exception):

    def __init__(self, name):
        self.name = name


class ExecuteCommandError(Exception):

    def __init__(self, command, exception):
        self.command = command
        self.exception = exception


class TidyEnd(Exception):
    pass


def get_default_font_paths():
    return [
        os.getcwd(),
        opath.join(os.getcwd(), 'fonts'),
    ]


def strep(s):
    return (s
            .replace(' ', '␣')
            .replace('\n', '⏎ ')
            .replace('\t', '⇥')
            )


def csep(args):
    args = [a for a in args if a != '' and a is not None]
    return ', '.join(args)


def clsn(obj):
    return obj.__class__.__name__


def drep(obj, a):
    return f'{clsn(obj)}({csep(a)})'


def sum_infinities(ds):
    order_sums = [0]
    for d in ds:
        if isinstance(d, int):
            order_sums[0] += d
        else:
            order = d.value['number_of_fils']
            # Extend order sum list with zeros to accommodate this infinity.
            new_length_needed = order + 1 - len(order_sums)
            order_sums.extend(0 for _ in range(new_length_needed))
            order_sums[order] += d.value['factor']
    return order_sums


def ensure_extension(path, extension):
    """Add a file extension if it is not already present."""
    end = opath.extsep + extension
    if not path.endswith(end):
        path += end
    return path


def find_file(file_name, search_paths=None):
    """Resolve a file name or path to an absolute path, optionally searching a
    sequence of directories."""
    # If file_name is already a full path, just use that.
    supplied_dirname = opath.dirname(file_name)
    if supplied_dirname != '':
        return file_name
    # Otherwise, search some directories for the file name.
    if search_paths is None:
        search_paths = []
    for search_path in search_paths:
        test_path = opath.join(search_path, file_name)
        if opath.exists(test_path):
            return opath.abspath(test_path)
    raise FileNotFoundError


def file_path_to_chars(file_path):
    """Return the characters in a file at the given path."""
    with open(file_path, 'rb') as f:
        return [chr(b) for b in f.read()]
