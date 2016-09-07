from enum import Enum
# import logging

from reader import EndOfFile
from common import Token
# TODO: Make lex types into an enum. Love an enum, makes me feel so safe.
from typer import CatCode, char_cat_lex_type, control_sequence_lex_type

# logger = logging.getLogger(__name__)
# logger.setLevel('DEBUG')


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


class ReadingState(Enum):
    line_begin = 'N'
    line_middle = 'M'
    skipping_blanks = 'S'


def make_char_cat_token(char, cat):
    return Token(type_=char_cat_lex_type, value={'char': char, 'cat': cat})


def make_control_sequence_token(name):
    return Token(type_=control_sequence_lex_type, value=name)


class Lexer(object):

    def __init__(self, reader, global_state):
        self.reader = reader
        self.reading_state = ReadingState.line_begin
        self.global_state = global_state

    def peek_ahead(self, n=1):
        # TODO: stop peeking ahead very far, because scope might change and
        # results would be incorrect.
        char = self.reader.peek_ahead(n)
        cat = self.global_state.get_cat_code(char)
        return char, cat

    @property
    def cur_char(self):
        return self.peek_ahead(n=0)

    @property
    def cur_char_with_trio(self):
        return self.chomp_next_char_with_trio(current=True)

    def chomp_next_char(self, peek=False):
        c = self.peek_ahead()
        if not peek:
            self.reader.advance_loc()
        return c

    def chomp_next_char_with_trio(self, peek=False, current=False):
        if current:
            start_char, start_cat = self.cur_char
            peek_offset = 0
        else:
            start_char, start_cat = self.chomp_next_char(peek=peek)
            if peek:
                peek_offset = 1
            else:
                peek_offset = 0
        char, cat = start_char, start_cat
        if start_cat == CatCode.superscript:
            # If the next character from the start is end-of-file, then
            # no trio-ing is going on.
            try:
                next_char, next_cat = self.peek_ahead(n=peek_offset + 1)
            except EndOfFile:
                return char, cat
            if (next_char == start_char) and (next_cat == start_cat):
                # If the next-but-one character from the start is end-of-file,
                # then no trio-ing is going on.
                try:
                    triod_char, triod_cat = self.peek_ahead(n=peek_offset + 2)
                except EndOfFile:
                    return char, cat
                if triod_cat != CatCode.end_of_line:
                    triod_ascii_code = ord(triod_char)
                    if triod_ascii_code >= 64:
                        triod_ascii_code -= 64
                    else:
                        triod_ascii_code += 64
                    char = chr(triod_ascii_code)
                    cat = self.global_state.get_cat_code(char)
                    if not peek:
                        self.reader.advance_loc(n=2)
        return char, cat

    @property
    def next_token(self):
        while True:
            token = self.process_next_character()
            if token is not None:
                return token

    def process_next_character(self):
        char, cat = self.chomp_next_char_with_trio()
        # logger.debug('Chomped {}_{}'.format(char, cat))
        if cat == CatCode.comment:
            # logger.info('Comment')
            while self.chomp_next_char()[1] != CatCode.end_of_line:
                # logger.debug('Chomped comment character {}_{}'.format(*self.cur_char))
                pass
            # logger.debug('Chomped end_of_line in comment')
            self.reading_state = ReadingState.line_begin
        elif cat == CatCode.escape:
            # logger.debug('Chomped escape character {}_{}'.format(char, cat))
            char, cat = self.chomp_next_char_with_trio()
            control_sequence_chars = [char]
            # If non-letter, have a control sequence of that single character.
            if cat != CatCode.letter:
                if cat == CatCode.space:
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
                        next_char, next_cat = self.chomp_next_char_with_trio(peek=True)
                    # If the next 'character' is end-of-file, then finish
                    # control sequence.
                    except EndOfFile:
                        break
                    if next_cat == CatCode.letter:
                        self.chomp_next_char_with_trio(peek=False)
                        control_sequence_chars.append(next_char)
                    else:
                        break
                self.reading_state = ReadingState.skipping_blanks
            control_sequence_name = ''.join(control_sequence_chars)
            return make_control_sequence_token(control_sequence_name)
            # logger.debug('Got control sequence {}'.format(control_sequence_name))
        elif cat in tokenise_cats:
            token = make_char_cat_token(char, cat)
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
                token = make_char_cat_token(' ', cat)
                self.reading_state = ReadingState.skipping_blanks
                return token
        elif cat == CatCode.end_of_line:
            # NOTE: I'm very confused about TeX's concept of lines.
            # I am going to implement a sort of mishmash of these two
            # explanations below.

            # 1. [This bit of explanation is mixed in with the code, for
            #    clarity]
            # [I do not know what this bit really means]
            # If TeX sees an end-of-line character (category 5), it throws away
            # any other information that might remain on the current line.

            # Then if TeX is in state N (new line),
            if self.reading_state == ReadingState.line_begin:
                # the end-of-line character is converted to the control
                # sequence token 'par' (end of paragraph).
                token = make_control_sequence_token('par')
                return token
            # if TeX is in state M (mid-line),
            elif self.reading_state == ReadingState.line_middle:
                # the end-of-line character is converted to a token for
                # character 32 (' ') of category 10 (space).
                token = make_char_cat_token(' ', CatCode.space)
                return token
            # and if TeX is in state S (skipping blanks),
            elif self.reading_state == ReadingState.skipping_blanks:
                # the end-of-line character is simply dropped.
                pass

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
