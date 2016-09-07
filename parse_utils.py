from state import GlobalState
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher


class LexWrapper(object):

    def __init__(self, file_name):
        self.state = GlobalState()
        self.file_name = file_name
        self.r = Reader(file_name)
        self.lex = Lexer(self.r, self.state)
        self.b = Banisher(self.lex, wrapper=self)
        self.in_recovery_mode = False

    def __next__(self):
        try:
            return self.b.next_token
        except EndOfFile:
            return None
