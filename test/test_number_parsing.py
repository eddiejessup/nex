from nex.tokens import PLYTokenMixin
from nex.parsing import parsing


import pytest


class T(PLYTokenMixin):
    def __init__(self, type_, v=None):
        self.type = type_
        self.value = v

    def __repr__(self):
        v = self.value if self.value is not None else ''
        return f'T<{self.type}>({v})'


def test_numbers():
    parser = parsing.get_parser(start='number')

    def p(s):
        return parser.parse(iter(s))

    def basic_check(r):
        assert r.type == 'number'
        sgns, sz = r.value['signs'], r.value['size']
        assert sz.type == 'size'
        return sgns, sz

    r = parser.parse(iter([T('ZERO'), T('ONE'), T('TWO')]))
    sgns, sz = basic_check(r)
    assert len(sgns.value) == 0
    szv = sz.value
    assert szv.type == 'integer_constant'
    dig_collect = szv.value
    assert dig_collect.base == 10

    number_makers = [
        # Check signs.
        [T('MINUS_SIGN'), T('MINUS_SIGN'), T('ONE'), T('TWO')],
        # Check optional space.
        [T('ONE'), T('TWO'), T('SPACE')],
        # Check hex and octal constants.
        [T('SINGLE_QUOTE'), T('TWO')],
        [T('DOUBLE_QUOTE'), T('TWO')],

        [T('BACKTICK'), T('UNEXPANDED_CONTROL_SYMBOL')],
        [T('BACKTICK'), T('EQUALS')],
        [T('BACKTICK'), T('ACTIVE_CHARACTER')],

        [T('INTEGER_PARAMETER')],
        [T('SPECIAL_INTEGER')],
        [T('CHAR_DEF_TOKEN')],
        [T('MATH_CHAR_DEF_TOKEN')],
        [T('COUNT_DEF_TOKEN')],
        [T('COUNT'), T('ONE')]
    ]

    for number_maker in number_makers:
        r = parser.parse(iter(number_maker))
        basic_check(r)

    s = [T('COUNT')]
    for number_maker in number_makers:
        cs = s + number_maker
        r = parser.parse(iter(cs))
        basic_check(r)
