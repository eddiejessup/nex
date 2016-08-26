class EndOfFile(Exception):
    pass


class Reader(object):

    def __init__(self, file_name):
        self.i = -1
        self.file_name = file_name
        with open(file_name, 'rb') as f:
            self.chars = [chr(b) for b in f.read()]

    @property
    def next_char(self):
        c = self.chars[self.i]
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
