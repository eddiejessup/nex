import pytest

from nex.parsing import parsing

from common import str_to_toks as stoks, str_to_lit_str


def test_numbers():
    parser = parsing.get_parser(start='number', chunking=False)

    def p(s):
        return parser.parse(iter(stoks(s)))

    def basic_check(r):
        assert r.type == 'number'
        sgns, sz = r.value['signs'], r.value['size']
        assert sz.type == 'size'
        return sgns, sz

    r = p('ZERO ONE TWO')
    sgns, sz = basic_check(r)
    assert len(sgns.value) == 0
    szv = sz.value
    assert szv.type == 'integer_constant'
    dig_collect = szv.value
    assert dig_collect.base == 10

    number_makers = [
        # Check signs.
        'MINUS_SIGN MINUS_SIGN ONE TWO',
        # Check optional space.
        'ONE TWO SPACE',
        # Check hex and octal constants.
        'SINGLE_QUOTE TWO',
        'DOUBLE_QUOTE TWO',

        'BACKTICK UNEXPANDED_CONTROL_SYMBOL',
        'BACKTICK EQUALS',
        'BACKTICK ACTIVE_CHARACTER',

        'INTEGER_PARAMETER',
        'SPECIAL_INTEGER',
        'CHAR_DEF_TOKEN',
        'MATH_CHAR_DEF_TOKEN',
        'COUNT_DEF_TOKEN',
        'COUNT ONE'
    ]

    for number_maker in number_makers:
        r = p(number_maker)
        basic_check(r)

    s = 'COUNT'
    for number_maker in number_makers:
        cs = ' '.join([s, number_maker])
        r = p(cs)
        basic_check(r)


def test_dimens():
    parser = parsing.get_parser(start='dimen', chunking=False)
    parser.parse(iter(stoks(f'ONE {str_to_lit_str("pt")}')))
