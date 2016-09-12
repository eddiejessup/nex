from os import path


class EndOfFile(Exception):
    pass


def tex_file_to_chars(file_name):
    if not path.isfile(file_name):
        file_name += path.extsep + 'tex'
    with open(file_name, 'rb') as f:
        return [chr(b) for b in f.read()]


class Reader(object):

    def __init__(self, file_name):
        self.i = -1
        self.chars = []
        self.append_file(file_name)

    def append_file(self, file_name):
        self.chars.extend(tex_file_to_chars(file_name))

    @property
    def next_char(self):
        c = self.peek_ahead(n=0)
        self.i += 1
        return c

    def peek_ahead(self, n=1):
        try:
            char = self.chars[self.i + n]
        except IndexError:
            raise EndOfFile
        return char

    def advance_loc(self, n=1):
        self.i += n
