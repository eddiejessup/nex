import pytest

from nex.reader import Reader, ReaderBuffer

from common import (test_not_here_file_name, test_file_name, test_chars,
                    test_2_chars)


def test_buffer_init():
    """Check buffer works sensibly."""
    r = ReaderBuffer(test_chars)
    assert r.i == -1
    assert r.chars == test_chars


def test_next_char():
    """Check advancing through a file returns the correct characters."""
    r = Reader()
    r.insert_chars(test_chars)
    cs = [r.advance_loc() for _ in range(4)]
    assert cs == test_chars
    with pytest.raises(EOFError):
        r.advance_loc()


def test_init_missing_file():
    """Check inserting a non-existent file into a reader raises an error."""
    r = Reader()
    with pytest.raises(IOError):
        r.insert_file(test_not_here_file_name)


def test_init_file():
    """Check inserting a non-existent file into a reader raises an error."""
    r_direct = Reader()
    r_direct.insert_chars(test_chars)
    r_file = Reader()
    r_file.insert_file(test_file_name)
    assert list(r_direct.advance_to_end()) == list(r_file.advance_to_end())


def test_insert_start():
    """Check inserting a new file at the start reads from the second, then the
    first."""
    r = Reader()
    r.insert_chars(test_chars)
    r.insert_chars(test_2_chars)
    assert list(r.advance_to_end()) == test_2_chars + test_chars


def test_insert_middle():
    """Check inserting a new file halfway through reading a first, reads part
    of one, then the second, then the rest of the first."""
    r = Reader()
    r.insert_chars(test_chars)
    cs = [r.advance_loc()]
    r.insert_chars(test_2_chars)
    cs.extend(list(r.advance_to_end()))
    assert cs == ['a', 'd', 'e', 'f', '\n', 'b', 'c', '\n']


def test_insert_end():
    """Check inserting a new file after reading a first, reads the first then the second."""
    r = Reader()
    r.insert_chars(test_chars)
    cs = list(r.advance_to_end())
    r.insert_chars(test_2_chars)
    cs.extend(list(r.advance_to_end()))
    assert cs == test_chars + test_2_chars


def test_peek():
    """Test various errors and constraints on peeking."""
    r = Reader()
    r.insert_chars(test_chars)
    # Can't peek at start of buffer
    with pytest.raises(ValueError):
        r.peek_ahead(n=0)
    r.advance_loc()
    assert r.current_char == 'a'
    # Can't peek backwards, (especially because this would be end of buffer).
    with pytest.raises(ValueError):
        r.peek_ahead(n=-1)
    # Valid peeks.
    assert [r.peek_ahead(n=i) for i in range(4)] == test_chars
    # Can't peek too far ahead.
    with pytest.raises(ValueError):
        r.peek_ahead(n=4)
    r.advance_loc()
    assert r.current_char == 'b'
    # Can't peek past end of buffer.
    with pytest.raises(EOFError):
        r.peek_ahead(n=3)


def test_advance():
    """Test advancing through the reader on one buffer."""
    r = Reader()
    r.insert_chars(test_chars)
    cs = []
    for _ in range(4):
        r.advance_loc()
        cs.append(r.peek_ahead(0))
    assert cs == test_chars

# TODO: Line and column numbering.
# TODO: Peeking and advancing on buffers.
