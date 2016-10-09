import os

import pytest

from nex.reader import Reader, EndOfFile, tex_file_to_chars

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')
test_2_file_name = os.path.join(test_file_dir_path, 'test_2.tex')
test_not_here_file_name = os.path.join(test_file_dir_path, 'not_here.tex')

test_chars = ['a', 'b', 'c', '\n']
test_2_chars = ['d', 'e', 'f', '\n']


def test_file_to_chars():
    cs_with_ext = tex_file_to_chars(test_file_name)
    cs_without_ext = tex_file_to_chars(test_file_name[:-4])
    assert cs_with_ext == cs_without_ext == test_chars


def test_init():
    r = Reader(test_file_name)
    assert r.i == -1
    assert r.chars == ['a', 'b', 'c', '\n']


def test_next_char():
    r = Reader(test_file_name)
    cs = [r.next_char for _ in range(4)]
    assert cs == ['a', 'b', 'c', '\n']
    with pytest.raises(EndOfFile):
        r.next_char


def test_init_missing_file():
    with pytest.raises(IOError):
        Reader(test_not_here_file_name)


def test_append():
    r = Reader(test_file_name)
    r.append_file(test_2_file_name)
    assert r.chars == test_chars + test_2_chars


def test_insert_start():
    r = Reader(test_file_name)
    r.insert_file(test_2_file_name)
    assert r.chars == test_2_chars + test_chars


def test_insert_middle():
    r = Reader(test_file_name)
    r.next_char
    r.insert_file(test_2_file_name)
    assert r.chars == ['a', 'd', 'e', 'f', '\n', 'b', 'c', '\n', ]


def test_insert_end():
    r = Reader(test_file_name)
    [r.next_char for _ in range(4)]
    r.insert_file(test_2_file_name)
    assert r.chars == ['a', 'b', 'c', '\n', 'd', 'e', 'f', '\n']


def test_peek():
    r = Reader(test_file_name)
    # Can't peek at start of file
    with pytest.raises(ValueError):
        r.peek_ahead(n=0)
    r.next_char
    # Can't peek backwards
    with pytest.raises(ValueError):
        r.peek_ahead(n=-1)
    # Valid peeks.
    assert [r.peek_ahead(n=i) for i in range(4)] == test_chars
    # Can't peek too far ahead.
    with pytest.raises(ValueError):
        r.peek_ahead(n=4)
    r.next_char
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
