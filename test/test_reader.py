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


def test_init():
    r = ReaderBuffer(test_file_name)
    assert r.i == -1
    assert r.chars == ['a', 'b', 'c', '\n']


def test_next_char():
    r = Reader(test_file_name)
    cs = [r.advance_loc() for _ in range(4)]
    assert cs == ['a', 'b', 'c', '\n']
    with pytest.raises(EndOfFile):
        r.advance_loc()


def test_init_missing_file():
    with pytest.raises(IOError):
        ReaderBuffer(test_not_here_file_name)
    with pytest.raises(IOError):
        Reader(test_not_here_file_name)


def test_insert_start():
    r = Reader(test_file_name)
    r.insert_file(test_2_file_name)
    assert list(r.advance_to_end()) == test_2_chars + test_chars


def test_insert_middle():
    r = Reader(test_file_name)
    cs = [r.advance_loc()]
    r.insert_file(test_2_file_name)
    cs.extend(list(r.advance_to_end()))
    assert cs == ['a', 'd', 'e', 'f', '\n', 'b', 'c', '\n']


def test_insert_end():
    r = Reader(test_file_name)
    cs = list(r.advance_to_end())
    r.insert_file(test_2_file_name)
    cs.extend(list(r.advance_to_end()))
    assert cs == ['a', 'b', 'c', '\n', 'd', 'e', 'f', '\n']


def test_peek():
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
    r = Reader(test_file_name)
    cs = []
    for _ in range(4):
        r.advance_loc()
        cs.append(r.peek_ahead(0))
    assert cs == test_chars

# TODO: test line and column numbering.
