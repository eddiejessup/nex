import pytest

from nex.parsing import parsing, utils as pu

from common import PTok as T, str_to_lit_str, str_to_toks


@pytest.fixture
def parser():
    return parsing.get_parser(start='condition', chunking=False)


def test_if_num(parser):
    r = parser.parse(iter(str_to_toks('IF_NUM ONE GREATER_THAN ZERO')))
    assert r.type == 'if_num'


def test_if_dimen(parser):
    unit_str = str_to_lit_str('pt')
    tstr = f'IF_DIMEN ONE {unit_str} GREATER_THAN ONE {unit_str} SPACE'
    r = parser.parse(iter(str_to_toks(tstr)))
