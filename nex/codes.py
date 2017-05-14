from collections import namedtuple
from enum import Enum
from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits

from .utils import ascii_characters, NotInScopeError


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

GlyphCode = namedtuple('GlyphCode', ('family', 'position'))
ignored_glyph_code = GlyphCode(family=0, position=0)

MathCode = namedtuple('MathCode', ('math_class', 'glyph_code'))
active_math_code = MathCode(math_class=MathClass.special_active,
                            glyph_code=ignored_glyph_code)

DelimiterCode = namedtuple('DelimiterCode',
                           ('small_glyph_code', 'large_glyph_code'))
not_a_delimiter_code = DelimiterCode(small_glyph_code=None,
                                     large_glyph_code=None)
ignored_delimiter_code = DelimiterCode(
    small_glyph_code=ignored_glyph_code,
    large_glyph_code=ignored_glyph_code
)


def get_unset_ascii_char_dict():
    return {c: None for c in ascii_characters}


class Codes:

    def __init__(self,
                 char_to_cat,
                 char_to_math_code,
                 lower_case_code, upper_case_code,
                 space_factor_code,
                 delimiter_code,
                 ):
        self.code_type_to_char_map = {
            'cat': char_to_cat,
            'math': char_to_math_code,
            'upper_case': upper_case_code,
            'lower_case': lower_case_code,
            'space_factor': space_factor_code,
            'delimiter': delimiter_code,
        }

    @staticmethod
    def default_initial_cat_codes():
        char_to_cat = get_unset_ascii_char_dict()
        char_to_cat.update({c: CatCode.other for c in ascii_characters})
        char_to_cat.update({let: CatCode.letter for let in ascii_letters})

        char_to_cat['\\'] = CatCode.escape
        char_to_cat[' '] = CatCode.space
        char_to_cat['%'] = CatCode.comment
        char_to_cat[WeirdChar.null.value] = CatCode.ignored
        # NON-STANDARD
        char_to_cat[WeirdChar.line_feed.value] = CatCode.end_of_line
        char_to_cat[WeirdChar.carriage_return.value] = CatCode.end_of_line
        char_to_cat[WeirdChar.delete.value] = CatCode.invalid
        return char_to_cat

    @staticmethod
    def default_initial_math_codes():
        char_to_math_code = get_unset_ascii_char_dict()
        for i, c in enumerate(ascii_characters):
            if c in ascii_letters:
                family = 1
            else:
                family = 0
            if c in (ascii_letters + digits):
                math_class = MathClass.variable_family
            else:
                math_class = MathClass.ordinary
            glyph_code = GlyphCode(family=family, position=i)
            char_to_math_code[i] = MathCode(math_class, glyph_code)
            # TODO: handle special active_math_code value,
            # page 155 of The TeXbook.
        return char_to_math_code

    @staticmethod
    def default_initial_case_codes():
        lower_case_code = get_unset_ascii_char_dict()
        upper_case_code = get_unset_ascii_char_dict()
        initial_vals = {c: chr(0) for c in ascii_characters}
        lower_case_code.update(initial_vals)
        upper_case_code.update(initial_vals)
        for lower, upper in zip(ascii_lowercase, ascii_uppercase):
            lower_case_code[lower] = lower
            upper_case_code[upper] = upper
            lower_case_code[upper] = lower
            upper_case_code[lower] = upper
        return lower_case_code, upper_case_code

    @staticmethod
    def default_initial_space_factor_codes():
        space_factor_code = get_unset_ascii_char_dict()
        for c in ascii_characters:
            space_factor_code[c] = 999 if c in ascii_uppercase else 1000
        return space_factor_code

    @staticmethod
    def default_initial_delimiter_codes():
        delimiter_code = get_unset_ascii_char_dict()
        delimiter_code.update({c: not_a_delimiter_code for c in ascii_characters})
        delimiter_code['.'] = ignored_delimiter_code
        return delimiter_code

    @classmethod
    def default_initial(cls):
        char_to_cat = cls.default_initial_cat_codes()
        char_to_math_code = cls.default_initial_math_codes()
        lower_case_code, upper_case_code = cls.default_initial_case_codes()
        space_factor_code = cls.default_initial_space_factor_codes()
        delimiter_code = cls.default_initial_delimiter_codes()
        return cls(char_to_cat,
                   char_to_math_code,
                   lower_case_code,
                   upper_case_code,
                   space_factor_code,
                   delimiter_code)

    @classmethod
    def default_local(cls, enclosing_scope):
        char_to_cat = get_unset_ascii_char_dict()
        char_to_math_code = get_unset_ascii_char_dict()
        lower_case_code = get_unset_ascii_char_dict()
        upper_case_code = get_unset_ascii_char_dict()
        space_factor_code = get_unset_ascii_char_dict()
        delimiter_code = get_unset_ascii_char_dict()
        return cls(char_to_cat,
                   char_to_math_code,
                   lower_case_code,
                   upper_case_code,
                   space_factor_code,
                   delimiter_code)

    def get(self, code_type, char):
        value = self._check_and_get_char_map_value(code_type, char)
        if value is None:
            raise NotInScopeError('No value in codes {code_type}, character {char}')
        return value

    def set(self, code_type, char, code):
        # Check key already exists.
        self._check_and_get_char_map_value(code_type, char)
        char_map = self._check_and_get_char_map(code_type)
        char_map[char] = code

    def _check_and_get_char_map(self, code_type):
        if code_type not in self.code_type_to_char_map:
            raise ValueError(f'No codes of type {code_type}')
        return self.code_type_to_char_map[code_type]

    def _check_and_get_char_map_value(self, code_type, char):
        char_map = self._check_and_get_char_map(code_type)
        if char not in char_map:
            raise ValueError(f'Character {char} not in codes {code_type}')
        return char_map[char]

    def set_cat_code(self, char, cat):
        self.set('cat', char, cat)

    def set_math_code(self, char, code):
        self.set('math', char, code)

    def set_upper_case_code(self, char, up_char):
        self.set('upper_case', char, up_char)

    def set_lower_case_code(self, char, low_char):
        self.set('lower_case', char, low_char)

    def set_space_factor_code(self, char, code):
        self.set('space_factor', char, code)

    def set_delimiter_code(self, char, code):
        self.set('delimiter', char, code)

    def get_cat_code(self, char):
        return self.get('cat', char)

    def get_math_code(self, char):
        return self.get('math', char)

    def get_upper_case_code(self, char):
        return self.get('upper_case', char)

    def get_lower_case_code(self, char):
        return self.get('lower_case', char)

    def get_space_factor_code(self, char):
        return self.get('space_factor', char)

    def get_delimiter_code(self, char):
        return self.get('delimiter', char)
