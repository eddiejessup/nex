import os

import pytest

from nex.reader import Reader, ReaderBuffer, EndOfFile, tex_file_to_chars

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')
test_2_file_name = os.path.join(test_file_dir_path, 'test_2.tex')
test_not_here_file_name = os.path.join(test_file_dir_path, 'not_here.tex')

test_chars = ['a', 'b', 'c', '\n']
test_2_chars = ['d', 'e', 'f', '\n']


def test_file_to_chars():
    """
    Test utility to add an extension to TeX file names if it is not supplied.
    """
    cs_with_ext = tex_file_to_chars(test_file_name)
    cs_without_ext = tex_file_to_chars(test_file_name[:-4])
    assert cs_with_ext == cs_without_ext == test_chars


def test_buffer_init():
    """Check buffer works sensibly."""
    r = ReaderBuffer(test_file_name)
    assert r.i == -1
    assert r.chars == test_chars


def test_next_char():
    """Check advancing through a file returns the correct characters."""
    r = Reader(test_file_name)
    cs = [r.advance_loc() for _ in range(4)]
    assert cs == test_chars
    with pytest.raises(EndOfFile):
        r.advance_loc()


def test_init_missing_file():
    """Check making either a buffer or reader with a non-existent file raises
    an error."""
    with pytest.raises(IOError):
        ReaderBuffer(test_not_here_file_name)
    with pytest.raises(IOError):
        Reader(test_not_here_file_name)


def test_insert_start():
    """Check inserting a new file at the start reads from the second, then the
    first."""
    r = Reader(test_file_name)
    r.insert_file(test_2_file_name)
    assert list(r.advance_to_end()) == test_2_chars + test_chars


def test_insert_middle():
    """Check inserting a new file halfway through reading a first, reads part
    of one, then the second, then the rest of the first."""
    r = Reader(test_file_name)
    cs = [r.advance_loc()]
    r.insert_file(test_2_file_name)
    cs.extend(list(r.advance_to_end()))
    assert cs == ['a', 'd', 'e', 'f', '\n', 'b', 'c', '\n']


def test_insert_end():
    """Check inserting a new file after reading a first, reads the first then the second."""
    r = Reader(test_file_name)
    cs = list(r.advance_to_end())
    r.insert_file(test_2_file_name)
    cs.extend(list(r.advance_to_end()))
    assert cs == test_chars + test_2_chars


def test_peek():
    """Test various errors and constraints on peeking."""
    r = Reader(test_file_name)
    # Can't peek at start of file
    with pytest.raises(ValueError):
        r.peek_ahead(n=0)
    # After this we should be on 'a'.
    r.advance_loc()
    # Can't peek backwards, (especially because this would be end of file).
    with pytest.raises(ValueError):
        r.peek_ahead(n=-1)
    # Valid peeks.
    assert [r.peek_ahead(n=i) for i in range(4)] == test_chars
    # Can't peek too far ahead.
    with pytest.raises(ValueError):
        r.peek_ahead(n=4)
    # After this we should be on 'b'.
    r.advance_loc()
    # Can't peek past end of file.
    with pytest.raises(EndOfFile):
        r.peek_ahead(n=3)


def test_advance():
    """Test advancing through the reader on one file."""
    r = Reader(test_file_name)
    cs = []
    for _ in range(4):
        r.advance_loc()
        cs.append(r.peek_ahead(0))
    assert cs == test_chars

# TODO: Line and column numbering.
# TODO: Peeking and advancing on buffers.
