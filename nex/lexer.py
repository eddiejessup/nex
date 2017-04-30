from enum import Enum
import logging

from .reader import Reader, EndOfFile
from .common import LexToken
from .codes import CatCode

logger = logging.getLogger(__name__)

# CatCodes that should just be made into a char-cat lex token.
# That is to say, they do not immediately affect the lexing of the input.
tokenise_cats = [
    CatCode.begin_group,
    CatCode.end_group,
    CatCode.math_shift,
    CatCode.align_tab,
    CatCode.parameter,
    CatCode.superscript,  # Assuming not part of hex trio.
    CatCode.subscript,
    CatCode.letter,
    CatCode.other,
    CatCode.active,
]


# TODO: Make lex types into an enum. Love an enum, makes me feel so safe.
char_cat_lex_type = 'CHAR_CAT_PAIR'
control_sequence_lex_type = 'CONTROL_SEQUENCE'


class ReadingState(Enum):
    line_begin = 'N'
    line_middle = 'M'
    skipping_blanks = 'S'


def make_char_cat_lex_token(char, cat, *pos_args, **pos_kwargs):
    return LexToken(type_=char_cat_lex_type, value={'char': char, 'cat': cat},
                    *pos_args, **pos_kwargs)


def make_control_sequence_lex_token(name, *pos_args, **pos_kwargs):
    return LexToken(type_=control_sequence_lex_type, value=name,
                    *pos_args, **pos_kwargs)


def is_char_cat(token):
    return (isinstance(token.value, dict) and
            'lex_type' in token.value and
            token.value['lex_type'] == char_cat_lex_type)


def is_control_sequence_call(token):
    return (isinstance(token.value, dict) and
            'lex_type' in token.value and
            token.value['lex_type'] == control_sequence_lex_type)


class Lexer:

    def __init__(self, reader, get_cat_code_func):
        self.reader = reader
        self.reading_state = ReadingState.line_begin
        self.get_cat_code_func = get_cat_code_func

    @classmethod
    def from_string(cls, s, *args, **kwargs):
        reader = Reader()
        reader.insert_string(s)
        return cls(reader, *args, **kwargs)

    def get_next_token(self):
        while True:
            token = self._process_next_character()
            if token is not None:
                # print(token.get_position_str(self.reader))
                return token

    def advance_to_end(self):
        """Return an iterator over the lexer's tokens until end-of-file. Use
        with care, as the tokens' meanings, when acted on, may change the input
        that should be read."""
        while True:
            try:
                yield self.get_next_token()
            except EndOfFile:
                break

    def _peek_ahead(self, n=1):
        if n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        char = self.reader.peek_ahead(n)
        cat = self.get_cat_code_func(char)
        return char, cat

    @property
    def _cur_char_cat(self):
        return self._peek_ahead(n=0)

    def _chomp_next_char(self, peek=False):
        c = self._peek_ahead()
        if not peek:
            self.reader.advance_loc()
        return c

    def _chomp_next_char_trio(self, peek=False, current=False):
        if current:
            start_char, start_cat = self._cur_char_cat
            peek_offset = 0
        else:
            start_char, start_cat = self._chomp_next_char(peek=peek)
            if peek:
                peek_offset = 1
            else:
                peek_offset = 0
        char, cat = start_char, start_cat
        char_len = 1
        if start_cat == CatCode.superscript:
            # If the next character from the start is end-of-file, then
            # no trio-ing is going on.
            try:
                next_char, next_cat = self._peek_ahead(n=peek_offset + 1)
            except EndOfFile:
                return char, cat, char_len
            # Next char-cat must match start char-cat.
            if (next_char == start_char) and (next_cat == start_cat):
                # If the next-but-one character from the start is end-of-file,
                # then no trio-ing is going on.
                try:
                    triod_char, triod_cat = self._peek_ahead(n=peek_offset + 2)
                except EndOfFile:
                    return char, cat, char_len
                if triod_cat != CatCode.end_of_line:
                    triod_ascii_code = ord(triod_char)
                    if triod_ascii_code >= 64:
                        triod_ascii_code -= 64
                    else:
                        triod_ascii_code += 64
                    char = chr(triod_ascii_code)
                    cat = self.get_cat_code_func(char)
                    char_len = 3
                    if not peek:
                        self.reader.advance_loc(n=2)
        return char, cat, char_len

    def _process_next_character(self):
        pos_info = {
            'file_hash': self.reader.current_hash,
            'line_nr': self.reader.line_nr,
            'col_nr': self.reader.col_nr,
            # char_nr is the start, which is always now plus 1, regardless of
            # trios.
            'char_nr': self.reader.char_nr + 1,
        }
        char, cat, total_char_len = self._chomp_next_char_trio()
        pos_info['char_len'] = total_char_len

        logger.debug('Chomped {}_{}'.format(char, cat))
        if cat == CatCode.comment:
            logger.info('Comment')
            while self._chomp_next_char()[1] != CatCode.end_of_line:
                logger.debug('Chomped comment character {}_{}'
                             .format(*self._cur_char_cat))
                pass
            logger.debug('Chomped end_of_line in comment')
            self.reading_state = ReadingState.line_begin
        elif cat == CatCode.escape:
            logger.debug('Chomped escape character {}_{}'.format(char, cat))
            first_char, first_cat, first_char_len = self._chomp_next_char_trio()
            pos_info['char_len'] += first_char_len
            control_sequence_chars = [first_char]
            # If non-letter, have a control sequence of that single character.
            if first_cat != CatCode.letter:
                if first_cat == CatCode.space:
                    self.reading_state = ReadingState.skipping_blanks
                else:
                    self.reading_state = ReadingState.line_middle
            # If letter, keep reading control sequence until have non-letter.
            else:
                while True:
                    # Peek to see if next (possibly trio-d) character is a letter.
                    # If it is, chomp it and add it to the list of control sequence
                    # characters.
                    try:
                        next_char, next_cat, next_char_len = self._chomp_next_char_trio(peek=True)
                    # If the next 'character' is end-of-file, then finish
                    # control sequence.
                    except EndOfFile:
                        break
                    if next_cat == CatCode.letter:
                        self._chomp_next_char_trio(peek=False)
                        control_sequence_chars.append(next_char)
                        pos_info['char_len'] += next_char_len
                    else:
                        break
                self.reading_state = ReadingState.skipping_blanks
            control_sequence_name = ''.join(control_sequence_chars)
            logger.debug('Got control sequence {}'.format(control_sequence_name))
            return make_control_sequence_lex_token(control_sequence_name,
                                                   **pos_info)
        elif cat in tokenise_cats:
            token = make_char_cat_lex_token(char, cat, **pos_info)
            self.reading_state = ReadingState.line_middle
            return token
        # If TeX sees a character of category 10 (space), the action
        # depends on the current state.
        elif cat == CatCode.space:
            # If TeX is in state N or S
            if self.reading_state in (ReadingState.line_begin,
                                      ReadingState.skipping_blanks):
                # The character is simply passed by, and TeX remains in the
                # same state.
                pass
            # Otherwise TeX is in state M
            else:
                # the character is converted to a token of category 10 whose
                # character code is 32, and TeX enters state S. The character
                # code in a space token is always 32.
                token = make_char_cat_lex_token(' ', cat, **pos_info)
                self.reading_state = ReadingState.skipping_blanks
                return token
        elif cat == CatCode.end_of_line:
            # NOTE: I'm very confused about TeX's concept of lines.
            # I am going to implement a sort of mishmash of these two
            # explanations below.

            # 1. This bit of explanation is mixed in with the code, for
            #    clarity. I do not know what this bit really means.

            # If TeX sees an end-of-line character (category 5), it throws away
            # any other information that might remain on the current line.

            # Then if TeX is in state N (new line),
            if self.reading_state == ReadingState.line_begin:
                # the end-of-line character is converted to the control
                # sequence token 'par' (end of paragraph).
                token = make_control_sequence_lex_token('par', **pos_info)
            # if TeX is in state M (mid-line),
            elif self.reading_state == ReadingState.line_middle:
                # the end-of-line character is converted to a token for
                # character 32 (' ') of category 10 (space).
                token = make_char_cat_lex_token(' ', CatCode.space, **pos_info)
            # and if TeX is in state S (skipping blanks),
            elif self.reading_state == ReadingState.skipping_blanks:
                # the end-of-line character is simply dropped.
                token = None
            # "At the beginning of every line [TeX is] in state N".
            self.reading_state = ReadingState.line_begin
            if token is not None:
                return token
            # 2.
            # TeX deletes any <space> characters (number 32) that occur at the
            # right end of an input line.
            # Then it inserts a <return> character
            # (number 13) at the right end of the line, except that it places
            # nothing additional at the end of a line that you inserted with
            # |I|' during error recovery. Note that <return> is considered to
            # be an actual character that is part of the line; you can obtain
            # special effects by changing its catcode.
            # cr_char = WeirdChar.carriage_return
            # cr_cat = self.char_to_cat[cr_char]
            # token = {'type': 'char_cat_pair', 'char': cr_char, 'cat': cr_cat}
            # return token
        else:
            import pdb; pdb.set_trace()
