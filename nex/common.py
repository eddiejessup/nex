from .rply.token import Token as RToken


ascii_characters = ''.join(chr(i) for i in range(128))


class Token(RToken):

    def __init__(self, type_, value, line_nr=None, col_nr=None):
        self.type = type_
        self.value = value
        self.lineno = line_nr
        self.col_nr = col_nr
        self.lexpos = None

    def gettokentype(self):
        return self.type

    def getsourcepos(self):
        return None

    def __repr__(self):
        return "<%s: %r %r>" % (self.__class__.__name__, self.type, self.value)

    def __str__(self):
        return self.__repr__()

    def copy(self):
        return self.__class__(self.type, self.value.copy())

    def equal_contents_to(self, other):
        if self.type != other.type:
            return False
        if self.value.keys() != other.value.keys():
            return False
        for k in self.value:
            # Tokens with different *call* names are still considered to be the
            # same.
            if k == 'name':
                continue
            if self.value[k] != other.value[k]:
                return False
        return True


class LexToken(Token):

    pass


class UnexpandedToken(Token):

    pass


class NonTerminalToken(Token):

    pass


class TerminalToken(Token):

    pass


class InternalToken(Token):

    pass
