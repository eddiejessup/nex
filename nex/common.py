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
                 file_hash=None,
                 position_like=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if position_like is not None:
            self._copy_position_from_token(position_like)
        else:
            self.set_position(line_nr, col_nr, char_nr, char_len, file_hash)

    def pos_summary(self, verbose=False):
        s = ''
        if self.line_nr is not None:
            s_line = '{:d}'.format(self.line_nr)
        else:
            s_line = '?'

        if self.col_nr is not None:
            s_col = '{:d}'.format(self.col_nr)
        else:
            s_col = '?'

        if self.char_nr is not None:
            s_pos = '{:d}'.format(self.char_nr)
        else:
            s_pos = '?'

        if self.char_len is not None:
            s_len = '{:d}'.format(self.char_len)
        else:
            s_len = '?'

        if verbose:
            f = 'Line {}, Col {}, Index {}, Length {}'
        else:
            f = '{}:{},{}+{}'
        s = f.format(s_line, s_col, s_pos, s_len)
        return s

    def __repr__(self):
        return "<{}({}): {!r} {!r}>".format(self.__class__.__name__,
                                            self.pos_summary(),
                                            self.type, self.value)

    def set_position(self, line_nr, col_nr, char_nr, char_len, file_hash):
        self.line_nr = line_nr
        self.col_nr = col_nr
        self.char_nr = char_nr
        self.char_len = char_len
        self.file_hash = file_hash

    def _copy_position_from_token(self, token):
        self.set_position(token.line_nr, token.col_nr, token.char_nr,
                          token.char_len, token.file_hash)

    def get_position_str(self, reader):
        cs = reader.get_buffer(self.file_hash).chars
        here_i = self.char_nr
        context_len = 20

        before_i = max(here_i - context_len, 0)
        pre_context = ''.join(cs[before_i:here_i])

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
