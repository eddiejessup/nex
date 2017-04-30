from nex.utils import ensure_extension, file_path_to_chars

from common import (test_file_name, test_chars)


def test_ensure_extension():
    """
    Test utility to add an extension to TeX file names if it is not supplied.
    """
    assert (ensure_extension('hello', 'tex') ==
            ensure_extension('hello.tex', 'tex'))
    assert (ensure_extension('/absolute/path/hello', 'tex') ==
            ensure_extension('/absolute/path/hello.tex', 'tex'))
    assert (ensure_extension('relative/path/hello', 'tex') ==
            ensure_extension('relative/path/hello.tex', 'tex'))


def test_file_to_chars():
    """
    Test utility to add an extension to TeX file names if it is not supplied.
    """
    assert file_path_to_chars(test_file_name) == test_chars
