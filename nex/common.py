from .rply.token import Token as RToken


ascii_characters = ''.join(chr(i) for i in range(128))


class Token(RToken):

    def __init__(self, type_, value):
        self.type = type_
        self.value = value
        self.lineno = None
        self.lexpos = None

    def gettokentype(self):
        return self.type

    def getsourcepos(self):
        return None

    def __repr__(self):
        return "<%s: %r %r>" % (self.__class__.__name__, self.type, self.value)

    def __str__(self):
        return self.__repr__()


class TerminalToken(Token):

    pass


class InternalToken(Token):

    pass
