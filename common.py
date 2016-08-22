from ply.lex import LexToken


ascii_characters = ''.join(chr(i) for i in range(128))


class Token(LexToken):

    def __init__(self, type_, value):
        self.type = type_
        self.value = value
        self.lineno = None
        self.lexpos = None

    def __repr__(self):
        return "<Token: %r %r>" % (self.type, self.value)

    def __str__(self):
        return self.__repr__()


class TerminalToken(Token):

    pass
