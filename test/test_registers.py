import pytest

from nex.registers import Registers
from nex.instructions import Instructions
from nex.utils import NotInScopeError


def test_registers_empty():
    r = Registers(*[0 for _ in range(5)])

    # Check we can't retrieve or set indexes that should not be there.
    for test_i in (0, None, 5, -1):
        with pytest.raises(ValueError):
            r.get(Instructions.count.value, test_i)
        for test_val in (0, 5):
            with pytest.raises(ValueError):
                r.set(Instructions.count.value,
                                     test_i, test_val)
        # Check we can't access registers that should not be there.
        for test_type in ('NOT_A_REGISTER', None):
            with pytest.raises(ValueError):
                r.get(test_type, test_i)


def test_registers_uninitialized():
    r = Registers(1, 0, 0, 0, 0)

    # Check we can't retrieve values that are not initialized.
    with pytest.raises(NotInScopeError):
        r.get(Instructions.count.value, 0)
    # But that once we set them, we can.
    test_val = 2
    r.set(Instructions.count.value, 0, test_val)
    assert r.get(Instructions.count.value, 0) == test_val


def test_register_types():
    r = Registers(*[1 for _ in range(5)])
    tokens = ['fake_token']
    dct = {'hihi': 3}
    int_val = 5
    for type_ in (Instructions.count.value, Instructions.dimen.value):
        r.set(type_, 0, int_val)
        with pytest.raises(TypeError):
            r.set(type_, 0, dct)
        with pytest.raises(TypeError):
            r.set(type_, 0, tokens)
    for type_ in (Instructions.skip.value, Instructions.mu_skip.value):
        with pytest.raises(TypeError):
            r.set(type_, 0, int_val)
        r.set(type_, 0, dct)
        with pytest.raises(TypeError):
            r.set(type_, 0, tokens)
    with pytest.raises(TypeError):
        r.set(Instructions.toks.value, 0, int_val)
    with pytest.raises(TypeError):
        r.set(Instructions.toks.value, 0, dct)
    r.set(Instructions.toks.value, 0, tokens)
