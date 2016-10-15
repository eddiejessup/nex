from collections import deque
from os import path


class EndOfFile(Exception):
    pass


def tex_file_to_chars(file_name):
    end = path.extsep + 'tex'
    if not file_name.endswith(end):
        file_name += end
    with open(file_name, 'rb') as f:
        return [chr(b) for b in f.read()]


class ReaderBuffer(object):

    def __init__(self, file_name):
        self.i = -1
        self.chars = tex_file_to_chars(file_name)

        self.line_nr = 1
        self.col_nr = 1

    @property
    def at_last_char(self):
        return self.i == len(self.chars) - 1

    def peek_ahead(self, n):
        if n < 0:
            raise ValueError('Cannot peek backwards')
        if n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        i_peek = self.i + n
        try:
            return self.chars[i_peek]
        except IndexError:
            raise EndOfFile

    def increment_loc(self):
        self.i += 1
        c = self.peek_ahead(0)
        if c == '\n':
            self.line_nr += 1
            self.col_nr = 0
        else:
            self.col_nr += 1


class Reader(object):

    def __init__(self, file_name):
        self.buffer_stack = deque()
        self.append_file(file_name)

    def append_file(self, file_name):
        self.buffer_stack.appendleft(ReaderBuffer(file_name))

    def insert_file(self, file_name):
        self.buffer_stack.append(ReaderBuffer(file_name))

    @property
    def current_buffer(self):
        return self.buffer_stack[-1]

    @property
    def current_chars(self):
        return self.current_buffer.chars

    @property
    def line_nr(self):
        return self.current_buffer.line_nr

    @property
    def col_nr(self):
        return self.current_buffer.col_nr

    @property
    def char_nr(self):
        return self.current_buffer.i

    @property
    def next_char(self):
        c = self.advance_loc()
        return c

    def peek_ahead(self, n=1):
        if n < 0:
            raise ValueError('Cannot peek backwards')
        if n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        n_to_do = n
        # Look at each buffer we are reading from, in reading order.
        for read_buffer in reversed(self.buffer_stack):
            # Try to read further ahead, up to our aimed distance.
            for n_to_try in range(n_to_do + 1):
                try:
                    char = read_buffer.peek_ahead(n_to_try)
                except EndOfFile:
                    break
            # Subtract as many units as we could read.
            n_to_do -= n_to_try
            # If we have read our aimed distance, then we have our peeked
            # character, and can return.
            if n_to_do == 0:
                return char
        raise EndOfFile

    def increment_loc(self):
        self.current_buffer.increment_loc()
        if self.current_buffer.at_last_char:
            try:
                self.buffer_stack.pop()
            except IndexError:
                raise EndOfFile

    def advance_loc(self, n=1):
        if n > 2:
            raise ValueError('Advancing so far is forbidden')
        if n <= 0:
            raise ValueError('Cannot advance backwards or not at all')
        for _ in range(n):
            self.increment_loc()
        return self.peek_ahead(0)
