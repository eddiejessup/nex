import pytest

from nex.common import Token
from nex.registers import Registers


def test_registers_empty():
    r = Registers(*[0 for _ in range(5)])

    # Check we can't retrieve or set indexes that should not be there.
    for test_i in (0, None, 5, -1):
        with pytest.raises(ValueError):
            r.get_register_value('COUNT', test_i)
        for test_val in (0, 5):
            with pytest.raises(ValueError):
                r.set_register_value('COUNT', test_i, test_val)
        # Check we can't access registers that should not be there.
        for test_type in ('NOT_A_REGISTER', None):
            with pytest.raises(KeyError):
                r.get_register_value(test_type, test_i)


def test_registers_uninitialized():
    r = Registers(1, 0, 0, 0, 0)

    # Check we can't retrieve values that are not initialized.
    with pytest.raises(ValueError):
        r.get_register_value('COUNT', 0)
    # But that once we set them, we can.
    test_val = 2
    r.set_register_value('COUNT', 0, test_val)
    assert r.get_register_value('COUNT', 0) == test_val


def test_register_types():
    r = Registers(*[1 for _ in range(5)])
    tokens = [Token(type_='whocares', value=4)]
    dct = {'hihi': 3}
    int_val = 5
    for type_ in ('COUNT', 'DIMEN'):
        r.set_register_value(type_, 0, int_val)
        with pytest.raises(TypeError):
            r.set_register_value(type_, 0, dct)
        with pytest.raises(TypeError):
            r.set_register_value(type_, 0, tokens)
    for type_ in ('SKIP', 'MU_SKIP'):
        with pytest.raises(TypeError):
            r.set_register_value(type_, 0, int_val)
        r.set_register_value(type_, 0, dct)
        with pytest.raises(TypeError):
            r.set_register_value(type_, 0, tokens)
    with pytest.raises(TypeError):
        r.set_register_value('TOKS', 0, int_val)
    with pytest.raises(TypeError):
        r.set_register_value('TOKS', 0, dct)
    r.set_register_value('TOKS', 0, tokens)
