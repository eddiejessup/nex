from os import path


class EndOfFile(Exception):
    pass


def tex_file_to_chars(file_name):
    end = path.extsep + 'tex'
    if not file_name.endswith(end):
        file_name += end
    with open(file_name, 'rb') as f:
        return [chr(b) for b in f.read()]


class Reader(object):

    def __init__(self, file_name):
        self.i = -1

        self.line_nr = 0
        self.col_nr = 0

        self.chars = []
        self.append_file(file_name)

    def append_file(self, file_name):
        self.chars.extend(tex_file_to_chars(file_name))

    def insert_file(self, file_name):
        self.chars[self.i + 1:self.i + 1] = tex_file_to_chars(file_name)

    @property
    def next_char(self):
        return self.advance_loc()

    def peek_ahead(self, n=1):
        i_peek = self.i + n
        if i_peek < 0 or n < 0:
            raise ValueError('Cannot peek before file start')
        if n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        try:
            char = self.chars[self.i + n]
        except IndexError:
            raise EndOfFile
        return char

    def advance_loc(self, n=1):
        if n > 2:
            raise ValueError('Advancing so far is forbidden')
        if n <= 0:
            raise ValueError('Cannot advance backwards or not at all')
        for _ in range(n):
            self.i += 1
            c = self.peek_ahead(0)
            if c == '\n':
                self.line_nr += 1
                self.col_nr = 0
            else:
                self.col_nr += 1
        # Check position is valid.
        return self.peek_ahead(0)
