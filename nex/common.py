import colorama


colorama.init()

ascii_characters = ''.join(chr(i) for i in range(128))


class BaseToken(object):

    def __init__(self, type_, value):
        self.type = type_
        self.value = value

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


class PositionToken(BaseToken):

    def __init__(self, line_nr=None, col_nr=None, char_nr=None,
                 position_like=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if position_like is not None:
            self._copy_position_from_token(position_like)
        else:
            self.set_position(line_nr, col_nr, char_nr)
        if self.line_nr is None and self.__class__ != BuiltToken:
            import pdb; pdb.set_trace()

    def set_position(self, line_nr, col_nr, char_nr):
        self.line_nr = line_nr
        self.col_nr = col_nr
        self.char_nr = char_nr

    def _copy_position_from_token(self, token):
        self.set_position(token.line_nr, token.col_nr, token.char_nr)

    def get_position_str(self, reader):
        cs = reader.chars
        ci = self.char_nr

        bi = max(ci - 10, 0)
        pre_context = ''.join(cs[bi:ci])

        here = cs[ci]
        if here == ' ':
            here = '[_]'
        here = colorama.Fore.RED + here + colorama.Style.RESET_ALL

        ei = min(ci + 10, len(cs))
        post_context = ''.join(cs[ci + 1:ei])

        bits = [pre_context, post_context]
        for i, bit in enumerate(bits):
            bit = bit.replace('\n', colorama.Fore.GREEN + '\\n' + colorama.Style.RESET_ALL)
            bit = bit.replace('\t', colorama.Fore.GREEN + '\\t' + colorama.Style.RESET_ALL)
            bits[i] = bit
        intro = 'L {} C {}:'.format(self.line_nr, self.col_nr)
        s = intro + bits[0] + here + bits[1]
        return s


class TerminalToken(PositionToken):

    # Token interface.

    def gettokentype(self):
        return self.type

    def getsourcepos(self):
        return (self.line_nr, self.col_nr)

    def getstr(self):
        return self.__repr__()

    @property
    def lineno(self):
        return self.line_nr

    @property
    def lexpos(self):
        return None


class Token(PositionToken):

    pass


class BuiltToken(Token):

    pass


class LexToken(Token):

    pass


class UnexpandedToken(Token):

    pass


class NonTerminalToken(Token):

    pass


class InternalToken(BaseToken):

    pass
