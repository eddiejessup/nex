from enum import Enum
import logging

from .reader import Reader, EndOfFile
from .tokens import LexToken
from .codes import CatCode
from .utils import strep

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
    """
    Takes output from a reader, and produces tokens representing either character-
    category pairs, such as ("A", "letter") or ("{", "left brace"), or control
    sequence calls, such as "\input" or "\mymacro". The only state the lexer
    depends on is the mapping of characters to category codes (and the state of the
    reader of course).
    """

    def __init__(self, reader, get_cat_code_func):
        self.reader = reader
        self.reading_state = ReadingState.line_begin
        self.get_cat_code = get_cat_code_func

    @classmethod
    def from_string(cls, s, *args, **kwargs):
        reader = Reader()
        reader.insert_string(s)
        return cls(reader, *args, **kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        while True:
            token = self._process_next_character()
            if token is not None:
                return token

    def advance_to_end(self):
        """Return an iterator over the lexer's tokens until end-of-file. Use
        with care, as the tokens' meanings, when acted on, may change the input
        that should be read."""
        while True:
            try:
                yield next(self)
            except EndOfFile:
                return

    def _peek_ahead(self, n=1):
        if n > 3:
            raise ValueError('Peeking ahead so far is forbidden, as lies might'
                             'be returned')
        char = self.reader.peek_ahead(n)
        cat = self.get_cat_code(char)
        return char, cat

    @property
    def _cur_char_cat(self):
        return self._peek_ahead(n=0)

    def _chomp_next_char(self, peek=False):
        c = self._peek_ahead()
        if not peek:
            self.reader.advance_loc()
        return c

    def _chomp_next_char_trio(self, peek=False):
        if peek:
            peek_offset = 1
        else:
            peek_offset = 0
        start_char, start_cat = self._chomp_next_char(peek=peek)
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
                    cat = self.get_cat_code(char)
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

        if cat == CatCode.comment:
            logger.debug('Lexing comment')
            while self._chomp_next_char()[1] != CatCode.end_of_line:
                pass
            self.reading_state = ReadingState.line_begin
        elif cat == CatCode.escape:
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
            logger.debug(f'Lexed control sequence "{control_sequence_name}"')
            return make_control_sequence_lex_token(control_sequence_name,
                                                   **pos_info)
        elif cat in tokenise_cats:
            logger.debug(f'Tokenizing "{strep(char)}" of category {cat.name}')
            token = make_char_cat_lex_token(char, cat, **pos_info)
            self.reading_state = ReadingState.line_middle
            return token
        # If TeX sees a character of category [space], the action
        # depends on the current state.
        elif cat == CatCode.space:
            # If TeX is in state [new line] or [skipping blanks]
            if self.reading_state in (ReadingState.line_begin,
                                      ReadingState.skipping_blanks):
                # The character is simply passed by, and TeX remains in the
                # same state.
                logger.debug('Ignoring space-category character')
                pass
            # Otherwise TeX is in state [line middle]
            else:
                # the character is converted to a token of category 10 whose
                # character code is 32, and TeX enters state [skipping blanks].
                # The character code in a space token is always 32.
                logger.debug('Tokenizing space-category character')
                token = make_char_cat_lex_token(' ', cat, **pos_info)
                self.reading_state = ReadingState.skipping_blanks
                return token
        elif cat == CatCode.end_of_line:
            # [...] if TeX is in state [new line],
            if self.reading_state == ReadingState.line_begin:
                # the end-of-line character is converted to the control
                # sequence token 'par' (end of paragraph).
                logger.debug('Lexing end-of-line character to \par')
                token = make_control_sequence_lex_token('par', **pos_info)
            # if TeX is in state [mid-line],
            elif self.reading_state == ReadingState.line_middle:
                # the end-of-line character is converted to a token for
                # character 32 (' ') of category [space].
                logger.debug('Lexing end-of-line character to space')
                token = make_char_cat_lex_token(' ', CatCode.space, **pos_info)
            # and if TeX is in state [skipping blanks],
            elif self.reading_state == ReadingState.skipping_blanks:
                # the end-of-line character is simply dropped.
                logger.debug('Ignoring end-of-line character')
                token = None
            # "At the beginning of every line [TeX is] in state [new line]".
            self.reading_state = ReadingState.line_begin
            if token is not None:
                return token
        else:
            import pdb; pdb.set_trace()
