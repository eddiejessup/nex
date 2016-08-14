from collections import namedtuple
import string
from string import ascii_letters, ascii_lowercase, ascii_uppercase
from enum import Enum
import logging


ascii_characters = ''.join(chr(i) for i in range(128))


class EndOfFile(Exception):
    pass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

cat_codes = [
    'escape',  # 0
    'begin_group',  # 1
    'end_group',  # 2
    'math_shift',  # 3
    'align_tab',  # 4
    'end_of_line',  # 5
    'parameter',  # 6
    'superscript',  # 7
    'subscript',  # 8
    'ignored',  # 9
    'space',  # 10
    'letter',  # 11
    'other',  # 12
    'active',  # 13
    'comment',  # 14
    'invalid',  # 15
]

CatCode = Enum('CatCode', {symbol: i for i, symbol in enumerate(cat_codes)})


weird_char_codes = {
    'null': 0,
    'line_feed': 10,
    'carriage_return': 13,
    'delete': 127,
}
weird_chars = {
    k: chr(v) for k, v in weird_char_codes.items()
}
WeirdChar = Enum('WeirdChar', weird_chars)


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


math_classes = [
    'ordinary',  # 0
    'large_operator',  # 1
    'binary_relation',  # 2
    'relation',  # 3
    'opening',  # 4
    'closing',  # 5
    'punctuation',  # 6
    'variable_family',  # 7
    'special_active',  # 8 (weird special case)
]

MathClass = Enum('MathClass', {symbol: i for i, symbol in enumerate(math_classes)})

MathCode = namedtuple('MathCode', ('math_class', 'family', 'position'))


class ReadingState(Enum):
    line_begin = 'N'
    line_middle = 'M'
    skipping_blanks = 'S'


class Mode(Enum):
    # Building the main vertical list.
    vertical_mode = 'V'
    # Building a vertical list for a vbox.
    internal_vertical_mode = 'IV'
    # Building a horizontal list for a paragraph.
    horizontal_mode = 'H'
    # Building a horizontal list for an hbox.
    restricted_horizontal_mode = 'RH'
    # Building a formula to be placed in a horizontal list.
    math_mode = 'M'
    # Building a formula to be placed on a line by itself,
    # interrupting the current paragraph.
    display_math_mode = 'DM'


class State(object):

    def __init__(self, chars):
        self.i = -1
        self.chars = chars

        self.reading_state = ReadingState.line_begin
        # At the beginning, TeX is in vertical mode, ready to construct pages.
        self.mode = Mode.vertical_mode
        self.initialize_char_cats()
        self.initialize_char_math_codes()
        self.initialize_case_codes()
        self.initialize_space_factor_codes()
        self.initialize_control_sequences()
        self.expanding_tokens = True

    def disable_expansion(self):
        self.expanding_tokens = False

    def enable_expansion(self):
        self.expanding_tokens = True

    def initialize_control_sequences(self):
        self.control_sequences = {}
        # TODO: should these control sequences actually return
        # (char, cat) pairs? Rather than just a plain character?
        self.control_sequences.update({c: [c] for c in self.char_to_cat})

    def initialize_char_cats(self):
        self.char_to_cat = {
            c: CatCode.other for c in ascii_characters
        }
        self.char_to_cat.update({let: CatCode.letter
                                 for let in ascii_letters})

        self.char_to_cat['\\'] = CatCode.escape
        self.char_to_cat[' '] = CatCode.space
        self.char_to_cat['%'] = CatCode.comment
        self.char_to_cat[WeirdChar.null.value] = CatCode.ignored
        # NON-STANDARD
        self.char_to_cat[WeirdChar.line_feed.value] = CatCode.end_of_line
        self.char_to_cat[WeirdChar.carriage_return.value] = CatCode.end_of_line
        self.char_to_cat[WeirdChar.delete.value] = CatCode.invalid

    def initialize_char_math_codes(self):
        self.char_to_math_code = {}
        for i, c in enumerate(ascii_characters):
            if c in ascii_letters:
                family = 1
            else:
                family = 0
            if c in (ascii_letters + string.digits):
                math_class = MathClass.variable_family
            else:
                math_class = MathClass.ordinary
            self.char_to_math_code[i] = MathCode(math_class=math_class,
                                                 family=family,
                                                 position=i)
            # TODO: handle special "8000 value, page 155 of The TeXbook.

    def initialize_case_codes(self):
        self.lower_case_code, self.upper_case_code = [
            {c: chr(0) for c in ascii_characters}
            for _ in range(2)
        ]
        for lower, upper in zip(ascii_lowercase, ascii_uppercase):
            self.lower_case_code[lower] = lower
            self.upper_case_code[upper] = upper
            self.lower_case_code[upper] = lower
            self.upper_case_code[lower] = upper

    def initialize_space_factor_codes(self):
        self.space_factor_code = {c: (999 if c in ascii_uppercase else 1000)
                                  for c in ascii_characters}

    def peek_ahead(self, n=1):
        try:
            char = self.chars[self.i + n]
        except IndexError:
            raise EndOfFile
        cat = self.char_to_cat[char]
        return char, cat

    @property
    def cur_char(self):
        return self.peek_ahead(n=0)

    @property
    def cur_char_with_trio(self):
        return self.chomp_next_char_with_trio(current=True)

    def advance_loc(self, n=1):
        self.i += n

    def chomp_next_char(self, peek=False):
        r = self.peek_ahead()
        if not peek:
            self.advance_loc()
        return r

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
                    cat = self.char_to_cat[char]
                    if not peek:
                        self.advance_loc(n=2)
        return char, cat

    def get_tokens(self):
        while True:
            try:
                token = self.process_next_character()
                if token is not None:
                    yield token
            except EndOfFile:
                return

    def process_next_character(self):
        char, cat = self.chomp_next_char_with_trio()
        logger.debug('Chomped {}_{}'.format(char, cat))
        if cat == CatCode.comment:
            logger.info('Comment')
            while self.chomp_next_char()[1] != CatCode.end_of_line:
                logger.debug('Chomped comment character {}_{}'.format(*self.cur_char))
                pass
            logger.debug('Chomped end_of_line in comment')
            self.reading_state = ReadingState.line_begin
        elif cat == CatCode.escape:
            logger.debug('Chomped escape character {}_{}'.format(char, cat))
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
                self.reading_state = ReadingState.line_middle
            control_sequence_name = ''.join(control_sequence_chars)
            return {'type': 'control_sequence', 'name': control_sequence_name}
            logger.debug('Got control sequence {}'.format(control_sequence_name))
        elif cat in tokenise_cats:
            token = {'type': 'char_cat_pair', 'char': char, 'cat': cat}
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
                token = {'type': 'char_cat_pair', 'char': ' ', 'cat': cat}
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
                token = {'type': 'control_sequence', 'name': 'par'}
                return token
            # if TeX is in state M (mid-line),
            elif self.reading_state == ReadingState.line_middle:
                # the end-of-line character is converted to a token for
                # character 32 (' ') of category 10 (space).
                token = {'type': 'char_cat_pair', 'char': ' ',
                         'cat': CatCode.space}
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


with open('p.tex', 'rb') as f:
    chars = [chr(b) for b in f.read()]

if __name__ == '__main__':
    state = State(chars)
    try:
        state.get_token()
    except EndOfFile:
        pass
    print(state.tokens)
