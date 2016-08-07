import string
from enum import Enum
import logging


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
    'carr_return': 13,
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


class ReadingMode(Enum):
    line_begin = 'N'
    line_middle = 'M'
    skipping_blanks = 'S'


class State(object):

    def __init__(self, chars):
        self.reading_mode = ReadingMode.line_begin
        self.i = -1
        self.initialize_char_cats()
        self.tokens = []

        self.chars = chars

    def initialize_char_cats(self):
        self.char_to_cat = {
            chr(i): CatCode.other for i in range(128)
        }
        self.char_to_cat.update({let: CatCode.letter
                                 for let in string.ascii_letters})

        self.char_to_cat['\\'] = CatCode.escape
        self.char_to_cat[' '] = CatCode.space
        self.char_to_cat['%'] = CatCode.comment
        self.char_to_cat[WeirdChar.null.value] = CatCode.ignored
        # NON-STANDARD
        self.char_to_cat[WeirdChar.line_feed.value] = CatCode.end_of_line
        self.char_to_cat[WeirdChar.carr_return.value] = CatCode.end_of_line
        self.char_to_cat[WeirdChar.delete.value] = CatCode.invalid

    def peek_ahead(self, n=1):
        try:
            char = self.chars[self.i + n]
        except IndexError:
            raise EndOfFile
        cat = self.char_to_cat[char]
        return char, cat

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
        if start_cat == CatCode.superscript:
            next_char, next_cat = self.peek_ahead(n=peek_offset + 1)
            if (next_char == start_char) and (next_cat == start_cat):
                triod_char, triod_cat = self.peek_ahead(n=peek_offset + 2)
                if triod_cat != CatCode.end_of_line:
                    triod_ascii_code = ord(triod_char)
                    if triod_ascii_code >= 64:
                        triod_ascii_code -= 64
                    else:
                        triod_ascii_code += 64
                    start_char = chr(triod_ascii_code)
                    start_cat = self.char_to_cat[start_char]
                    if not peek:
                        self.advance_loc(n=2)
        else:
            char, cat = start_char, start_cat
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
            self.reading_mode = ReadingMode.line_begin
        elif cat == CatCode.escape:
            logger.debug('Chomped escape character {}_{}'.format(char, cat))
            char, cat = self.chomp_next_char_with_trio()
            control_sequence_chars = [char]
            # If non-letter, have a control sequence of that single character.
            if cat != CatCode.letter:
                if cat == CatCode.space:
                    self.reading_mode = ReadingMode.skipping_blanks
                else:
                    self.reading_mode = ReadingMode.line_middle
            # If letter, keep reading control sequence until have non-letter.
            else:
                while True:
                    # Peek to see if next (possibly trio-d) character is a letter.
                    # If it is, chomp it and add it to the list of control sequence
                    # characters.
                    next_char, next_cat = self.chomp_next_char_with_trio(peek=True)
                    if next_cat == CatCode.letter:
                        self.chomp_next_char_with_trio(peek=False)
                        control_sequence_chars.append(next_char)
                    else:
                        break
                self.reading_mode = ReadingMode.line_middle
            control_sequence_name = ''.join(control_sequence_chars)
            return {'type': 'control_sequence', 'name': control_sequence_name}
            logger.debug('Got control sequence {}'.format(control_sequence_name))
        elif cat in tokenise_cats:
            token = {'type': 'char_cat_pair', 'char': char, 'cat': cat}
            self.reading_mode = ReadingMode.line_middle
            return token
        # If TeX sees a character of category 10 (space), the action
        # depends on the current state.
        elif cat == CatCode.space:
            # If TeX is in state N or S
            if self.reading_mode in (ReadingMode.line_begin,
                                     ReadingMode.skipping_blanks):
                # The character is simply passed by, and TeX remains in the
                # same state.
                pass
            # Otherwise TeX is in state M
            else:
                # the character is converted to a token of category 10 whose
                # character code is 32, and TeX enters state S. The character
                # code in a space token is always 32.
                token = {'type': 'char_cat_pair', 'char': ' ', 'cat': cat}
                self.reading_mode = ReadingMode.skipping_blanks
                return token
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
