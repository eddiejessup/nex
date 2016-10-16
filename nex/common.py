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

    def copy(self, *args, **kwargs):
        v = self.value
        if isinstance(v, dict):
            v_copy = v.copy()
        elif isinstance(v, int):
            v_copy = v
        return self.__class__(type_=self.type, value=v_copy, *args, **kwargs)

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

    def __init__(self,
                 line_nr=None, col_nr=None, char_nr=None, char_len=None,
                 position_like=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if position_like is not None:
            self._copy_position_from_token(position_like)
        else:
            self.set_position(line_nr, col_nr, char_nr, char_len)
        # if self.line_nr is None and self.__class__ != BuiltToken:
        #     import pdb; pdb.set_trace()

    def set_position(self, line_nr, col_nr, char_nr, char_len):
        self.line_nr = line_nr
        self.col_nr = col_nr
        self.char_nr = char_nr
        self.char_len = char_len

    def _copy_position_from_token(self, token):
        self.set_position(token.line_nr, token.col_nr, token.char_nr,
                          token.char_len)

    def get_position_str(self, reader):
        cs = reader.current_chars
        here_i = self.char_nr
        context_len = 20

        before_i = max(here_i - context_len, 0)
        pre_context = ''.join(cs[before_i:here_i])

        here_i_end = here_i
        if self.char_len is None:
            here_len = 1
        else:
            here_len = self.char_len
        here_i_end = here_i + here_len
        here = ''.join(cs[here_i:here_i_end])
        here = here.replace(' ', '␣')
        here = colorama.Fore.RED + here + colorama.Style.RESET_ALL

        end_i = min(here_i_end + context_len, len(cs))
        post_context = ''.join(cs[here_i_end:end_i])

        intro = 'L:{:04d}C:{:03d}: '.format(self.line_nr, self.col_nr)
        s = intro + '…' + pre_context + here + post_context + '…'
        s = s.replace('\n', '⏎ ')
        s = s.replace('\t', '⇥')
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
