import pytest

from nex.accessors import Registers
from nex.instructions import Instructions
from nex.box import HBox
from nex.utils import NotInScopeError


def test_registers_empty():
    rmap = {
        Instructions.count.value: {},
    }
    r = Registers(rmap)

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
    rmap = {
        Instructions.count.value: {0: None},
    }
    r = Registers(rmap)

    # Check we can't retrieve values that are not initialized.
    with pytest.raises(NotInScopeError):
        r.get(Instructions.count.value, 0)
    # But that once we set them, we can.
    test_val = 2
    r.set(Instructions.count.value, 0, test_val)
    assert r.get(Instructions.count.value, 0) == test_val


def test_register_types():
    rmap = {
        Instructions.count.value: {0: None},
        Instructions.dimen.value: {0: None},
        Instructions.skip.value: {0: None},
        Instructions.mu_skip.value: {0: None},
        Instructions.toks.value: {0: None},
        Instructions.set_box.value: {0: None},
    }
    r = Registers(rmap)
    tokens = ['fake_token']
    dct = {'hihi': 3}
    int_val = 5
    box = HBox(contents=[])
    for type_ in (Instructions.count.value, Instructions.dimen.value):
        # Good type.
        r.set(type_, 0, int_val)
        # Bad type.
        with pytest.raises(TypeError):
            r.set(type_, 0, dct)
        with pytest.raises(TypeError):
            r.set(type_, 0, tokens)
    for type_ in (Instructions.skip.value, Instructions.mu_skip.value):
        # Good type.
        r.set(type_, 0, dct)
        # Bad type.
        with pytest.raises(TypeError):
            r.set(type_, 0, int_val)
        with pytest.raises(TypeError):
            r.set(type_, 0, tokens)
    # Good type.
    r.set(Instructions.toks.value, 0, tokens)
    # Bad type.
    with pytest.raises(TypeError):
        r.set(Instructions.toks.value, 0, int_val)
    with pytest.raises(TypeError):
        r.set(Instructions.toks.value, 0, dct)
    # Good type.
    r.set(Instructions.set_box.value, 0, box)
    # Bad type.
    with pytest.raises(TypeError):
        r.set(Instructions.set_box.value, 0, int_val)
    with pytest.raises(TypeError):
        r.set(Instructions.set_box.value, 0, dct)
