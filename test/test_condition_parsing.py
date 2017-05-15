import pytest

from nex.parsing import parsing, utils as pu

from common import PTok as T, str_to_lit_str, str_to_toks


@pytest.fixture(scope='module')
def parser():
    return parsing.get_parser(start='condition', chunking=False)


def test_if_num(parser):
    parser.parse(iter(str_to_toks('IF_NUM ONE GREATER_THAN ZERO')))


def test_if_dimen(parser):
    unit_str = str_to_lit_str('pt')
    tstr = f'IF_DIMEN ONE {unit_str} GREATER_THAN ONE {unit_str} SPACE'
    parser.parse(iter(str_to_toks(tstr)))


def test_if_bool(parser):
    parser.parse(iter(str_to_toks('IF_TRUE')))
    parser.parse(iter(str_to_toks('IF_FALSE')))


def test_if_odd(parser):
    parser.parse(iter(str_to_toks('IF_ODD ONE')))


def test_if_modes(parser):
    parser.parse(iter(str_to_toks('IF_V_MODE')))
    parser.parse(iter(str_to_toks('IF_H_MODE')))


def test_if_case(parser):
    parser.parse(iter(str_to_toks('IF_CASE ONE')))
