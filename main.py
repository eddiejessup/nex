import string
from enum import Enum


cat_codes = [
    'escape',
    'begin_group',
    'end_group',
    'math_shift',
    'align_tab',
    'end_of_line',
    'parameter',
    'superscript',
    'subscript',
    'ignored',
    'space',
    'letter',
    'other',
    'active',
    'comment',
    'invalid',
]

CatCode = Enum({symbol: i for i, symbol in enumerate(cat_codes)})


class WeirdChar(Enum):
    null = 0
    carr_return = 13
    delete = 127


char_cats = {
    chr(i): CatCode.other for i in range(128)
}
char_cats.update({let: CatCode.letter for let in string.ascii_letters})

char_cats['\\'] = CatCode.escape
char_cats[' '] = CatCode.space
char_cats['%'] = CatCode.comment
char_cats[WeirdChar.null] = CatCode.ignored
char_cats[WeirdChar.carr_return] = CatCode.end_of_line
char_cats[WeirdChar.delete] = CatCode.invalid
