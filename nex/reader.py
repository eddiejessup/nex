from os import path

from .utils import get_unique_id


class EndOfFile(Exception):
    pass


def tex_file_to_chars(file_name):
    """Return the characters in the file indicated by the input file-name, with
    the "tex" file extension added if it is not already present."""
    end = path.extsep + 'tex'
    if not file_name.endswith(end):
        file_name += end
    with open(file_name, 'rb') as f:
        return [chr(b) for b in f.read()]


# TODO: Would it be good to extend some built-in class, like a file class?
# TODO: Would be nice to support non-file buffer interfaces, like stdin and
# network things. \input{http://mysite.com/tex_preamble.tex} would be nice.
class ReaderBuffer:
    """Abstraction around a file, which tracks line and column numbers.
    Note that the buffer's position begins at '-1', not '0',
    so that viewing each value from 'increment_loc` will not skip the first
    character. The alternative might be less error-prone, but I'm sticking
    with this for now."""

    def __init__(self, file_name):
        self.i = -1
        self.chars = tex_file_to_chars(file_name)

        self.line_nr = 1
        self.col_nr = 1

    @property
    def at_last_char(self):
        """Whether the buffer is at its final character."""
        return self.i == len(self.chars) - 1

    @property
    def current_char(self):
        return self.peek_ahead(0)

    def peek_ahead(self, n):
        """Get a character `n` places from the current position, without
        changing the buffer's current position.
        `n < 0` is not allowed because in a TeX context it is not meaningful:
        many characters may have been read between the current character
        and one five places back, from other buffers.
        `n > 3` is not allowed, because peeking too far is dangerous: beyond
        a point, the characters' meanings might change the correct buffers to
        point, the characters' meanings might change the correct buffers to
        read from.
        `n = 0` returns the current position.
        If the buffer's position has not been advanced, so it is not 'on' any
        character, ValueError is raised.
        If the offset would spill past the end of the buffer, EndOfFile is
        raised."""
        if n < 0:
            raise ValueError('Cannot peek backwards')
        if n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        i_peek = self.i + n
        if i_peek < 0:
            raise ValueError('Cannot peek before beginning of buffer')
        try:
            return self.chars[i_peek]
        except IndexError:
            raise EndOfFile

    def increment_loc(self):
        """Advance the current position in the buffer by one character."""
        self.i += 1
        c = self.peek_ahead(0)
        if c == '\n':
            self.line_nr += 1
            self.col_nr = 0
        else:
            self.col_nr += 1
        return c


class Reader:
    """Provides an abstract interface to a stack of buffers (at the moment
    always files). A new buffer can be added to the stack, from where
    characters will be read off until it is exhausted, at which point the
    previous buffer will be read from, and so on.
    """

    def __init__(self, file_name):
        # This implementation is a bit lazy: there's a big map of hashes to
        # reader buffers, and a stack to hold hashes representing the active
        # buffers. I think the true structure is an ordered tree, but I can't
        # be bothered doing this. This method keeps around old buffers for
        # debugging purposes.
        self.active_buffer_hash_stack = []
        self.buffer_map = {}
        self.insert_file(file_name)

    def make_new_buffer(self, file_name):
        """Make a new buffer, assign it a unique key, and return this so it can
        be accessed again later. The key is a combination of the file name and
        a unique hash, so that duplicate file names do not collide"""
        new_hash = (file_name, get_unique_id())
        self.buffer_map[new_hash] = ReaderBuffer(file_name)
        return new_hash

    def get_buffer(self, file_hash):
        """Access a buffer by its hash."""
        return self.buffer_map[file_hash]

    def insert_file(self, file_name):
        """Make a new buffer, and add it to the active stack."""
        self.active_buffer_hash_stack.append(self.make_new_buffer(file_name))

    @property
    def current_hash(self):
        """The hash of the buffer currently being read."""
        return self.active_buffer_hash_stack[-1]

    @property
    def current_buffer(self):
        """The buffer currently being read."""
        return self.buffer_map[self.current_hash]

    @property
    def current_chars(self):
        """The characters in the buffer currently being read."""
        return self.current_buffer.chars

    @property
    def line_nr(self):
        """The line number of the current character in the current
        buffer."""
        return self.current_buffer.line_nr

    @property
    def col_nr(self):
        """The column number of the current character in the current
        buffer."""
        return self.current_buffer.col_nr

    @property
    def char_nr(self):
        """The index of the current character in the current
        buffer, relative to the start of that buffer."""
        return self.current_buffer.i

    @property
    def active_buffers_read_order(self):
        """An iterator over the buffers either being read, or still to be fully
        read, in order from current to last to be read."""
        for buffer_hash in reversed(self.active_buffer_hash_stack):
            yield self.get_buffer(buffer_hash)

    @property
    def current_char(self):
        return self.peek_ahead(0)

    def peek_ahead(self, n=1):
        """Get a character `n` places from the current position, without
        changing the reader's current position.
        `n < 0` is not possible, because read history is not kept.
        `n > 3` is not allowed, because peeking too far is dangerous: beyond a
        point, the characters' meanings might change the correct buffers to
        read from.
        `n = 0` returns the current position.
        This function will peek between buffer boundaries if necessary."""
        if n < 0:
            raise ValueError('Cannot peek backwards')
        elif n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        elif n == 0:
            return self.current_buffer.peek_ahead(0)
        n_to_do = n
        # Look at each buffer we are reading from, in reading order.
        for read_buffer in self.active_buffers_read_order:
            # Try to read successively further ahead, up to our aimed distance.
            # Don't try zero, because it might fail at the start of a buffer.
            for n_to_try in range(1, n_to_do + 1):
                try:
                    char = read_buffer.peek_ahead(n_to_try)
                except EndOfFile:
                    break
            # If we have read our aimed distance, then we have our peeked
            # character, and can return.
            else:
                return char
            # We can only get here by a `break` caused by an end-of-file.
            # Subtract as many units as we could read.
            # The last value of `n_to_try` is what failed, so we successfully
            # read one less than this.
            n_to_do -= n_to_try - 1
        raise EndOfFile

    def increment_loc(self):
        """Increment the reader's position, changing the current buffer if
        necessary."""
        if self.current_buffer.at_last_char:
            self.active_buffer_hash_stack.pop()
        # If that was the last buffer, we are done.
        if not self.active_buffer_hash_stack:
            raise EndOfFile
        return self.current_buffer.increment_loc()

    def advance_loc(self, n=1):
        """Advance the reader's position by `n` places, changing the current
        buffer if necessary, and return the new current character, for
        convenience.
        `n < 0` is not possible, because read history is not kept.
        `n > 2` is not allowed, because advancing too far is dangerous: beyond
        a point, the characters' meanings might change the correct buffers to
        read from."""
        if n > 2:
            raise ValueError('Advancing so far is forbidden')
        if n < 0:
            raise ValueError('Cannot advance backwards')
        for _ in range(n):
            self.increment_loc()
        return self.peek_ahead(0)

    def advance_to_end(self):
        """Return an iterator over the reader's characters, until all buffers
        are exhausted. Use with care, as the characters' meanings, when acted
        on, may change the correct buffers that should be read."""
        while True:
            try:
                yield self.advance_loc()
            except EndOfFile:
                break
