import colorama

from .feedback import strep, csep

colorama.init()


def get_position_str(chars, char_nr, char_len, line_nr, col_nr):
    here_i = char_nr
    context_len = 60

    before_i = max(here_i - context_len, 0)
    pre_context = ''.join(chars[before_i:here_i])
    if '\n' in pre_context:
        pre_context = pre_context[pre_context.rfind('\n'):]
    else:
        if before_i > 0:
            pre_context = '…' + pre_context

    if char_len is None:
        here_len = 1
    else:
        here_len = char_len
    here_i_end = here_i + here_len
    here = ''.join(chars[here_i:here_i_end])
    here = colorama.Fore.RED + here + colorama.Style.RESET_ALL

    end_i = min(here_i_end + context_len, len(chars))

    post_context = ''.join(chars[here_i_end:end_i])
    if '\n' in post_context:
        post_context = post_context[:post_context.find('\n') + 1]
    else:
        if end_i != len(chars):
            post_context = post_context + '…'

    s = pre_context + here + post_context
    s = strep(s)
    intro = f'{line_nr}:{col_nr}\t'
    return intro + s


class BaseToken:

    def __init__(self, type_, value=None):
        self._type = type_
        self.value = value

    @property
    def type(self):
        return self._type

    @property
    def value_repr(self):
        if self.value is None:
            return ''
        elif isinstance(self.value, dict):
            v = self.value.copy()
            if 'lex_type' in v:
                v.pop('lex_type')
            return v
        else:
            return repr(self.value)

    @property
    def value_str(self):
        if self.value is None:
            return ''
        elif isinstance(self.value, dict):
            v = self.value.copy()
            if 'lex_type' in v:
                v.pop('lex_type')
            return str(v)
        else:
            return str(self.value)

    def __repr__(self):
        return '{}({}: {})'.format(self.__class__.__name__,
                                   self.type, self.value_repr)

    def __str__(self):
        return self.__repr__()


class PositionToken(BaseToken):

    def __init__(self,
                 line_nr='abstract', col_nr=None, char_nr=None, char_len=None,
                 file_hash=None,
                 position_like=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if position_like is not None:
            self._copy_position_from_token(position_like)
        else:
            self.set_position(line_nr, col_nr, char_nr, char_len, file_hash)

    def pos_summary(self, verbose=False):
        if self.line_nr == 'abstract':
            return ''

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
            s = 'Line {}, Col {}, Index {}, Length {}'.format(s_line, s_col,
                                                              s_pos, s_len)
        else:
            s = f'L{s_line}'
        return s

    def set_position(self, line_nr, col_nr, char_nr, char_len, file_hash):
        self.line_nr = line_nr
        self.col_nr = col_nr
        self.char_nr = char_nr
        self.char_len = char_len
        self.file_hash = file_hash

    @property
    def char_nr_end(self):
        return self.char_nr + self.char_len - 1

    def _copy_position_from_token(self, token):
        self.set_position(token.line_nr, token.col_nr, token.char_nr,
                          token.char_len, token.file_hash)

    def get_position_str(self, reader):
        buff = reader.get_buffer(self.file_hash)
        cs = buff.chars
        name = buff.name
        s = get_position_str(cs, self.char_nr, self.char_len, self.line_nr,
                             self.col_nr)
        if name:
            s = f'{name}:{s}'
        return s


class LexToken(PositionToken):

    pass


class InstructionToken(PositionToken):

    def __init__(self, instruction, *args, **kwargs):
        super().__init__(type_=None, *args, **kwargs)
        self.instruction = instruction

    def copy(self, *args, **kwargs):
        v = self.value
        if v is None:
            v_copy = v
        elif isinstance(v, dict):
            v_copy = v.copy()
        elif isinstance(v, int):
            v_copy = v
        else:
            raise Exception
        return self.__class__(instruction=self.instruction,
                              value=v_copy, *args, **kwargs)

    def __eq__(self, other):
        return (
            self.instruction == other.instruction and
            self.value == other.value
        )

    @property
    def type(self):
        return self.instruction.value

    def __repr__(self):
        a = [f'I={self.instruction.name}']
        pos_summary = self.pos_summary()
        if pos_summary:
            pos = '@{}'.format(pos_summary)
        else:
            pos = ''
        a.append(pos)
        a.append(f'v={self.value_repr}')
        return f'IT({csep(a)})'

    def __str__(self):
        a = []
        a.append(f'{self.value_str}')
        return f'{self.instruction.name}({csep(a, str_func=str)})'


class BuiltToken(PositionToken):

    def _copy_position_from_token(self, tokens):
        self.constituent_tokens = tokens
        # If a single token is passed, make it into a list.
        try:
            iter(tokens)
        except TypeError:
            tokens = [tokens]
        if not tokens:
            self.set_position(None, None, None, None, None)
        # Ignore tokens that aren't really concrete tokens, like the output
        # of empty productions (None), or internal tokens.
        tokens = [t for t in tokens if isinstance(t, PositionToken)]
        tagged_ts = [t for t in tokens if t.char_nr is not None]
        if not tagged_ts:
            self.set_position(None, None, None, None, None)
        else:
            # All but char_len are the same as the first tagged token.
            super()._copy_position_from_token(tagged_ts[0])
            self.char_len = sum(t.char_len for t in tagged_ts)

    def __repr__(self):
        if self.type == 'fil_dimension':
            ells = 'l' * self.value['number_of_fils']
            return f"{self.value['factor']} fi{ells}"
        else:
            return super().__repr__()

    def __str__(self):
        if self.type == 'fil_dimension':
            ells = 'l' * self.value['number_of_fils']
            return f"{self.value['factor']} fi{ells}"
        else:
            a = []
            a.append(f'{self.value_str}')
            return f'{self.type}({csep(a, str_func=str)})'


class CommandToken(BuiltToken):

    def __init__(self, command, *args, **kwargs):
        super().__init__(type_=None, *args, **kwargs)
        self.command = command

    def __repr__(self):
        a = [f'C={self.command.name}']
        pos_summary = self.pos_summary()
        if pos_summary:
            pos = '@{}'.format(pos_summary)
        else:
            pos = ''
        a.append(pos)
        a.append(f'v={self.value_repr}')
        return f'CT({csep(a)})'

    def __str__(self):
        a = []
        a.append(f'{self.value_str}')
        return f'{self.command.name}({csep(a, str_func=str)})'


def instructions_to_types(instructions):
    return tuple(i.value for i in instructions)
