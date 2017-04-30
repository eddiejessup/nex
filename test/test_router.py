import os

import pytest

from nex.router import CSRouter, make_route_token
from nex.utils import NoSuchControlSequence
from nex.common import Token
from nex.lexer import control_sequence_lex_type

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')


dummy_token = Token(type_='dummy',
                    value={'lex_type': control_sequence_lex_type,
                           'name': 'test',
                           'attribute': 'attribute_value'})


def get_call_token(name):
    return Token(type_='call', value={'name': name,
                                      'lex_type': control_sequence_lex_type})


def test_router_non_exist():
    e = CSRouter(control_sequences={},
                 macros={},
                 let_chars={},
                 parameters={},
                 primitives={},
                 enclosing_scope=None)
    with pytest.raises(NoSuchControlSequence):
        e.resolve_control_sequence_to_token(name='test')
    with pytest.raises(NoSuchControlSequence):
        e.do_let_assignment(target_token=dummy_token, new_name='test_2')


def prepare_control_sequences(type_map, route_id):
    control_sequences = {}
    for type_, t_map in type_map.items():
        route_token = make_route_token(type_, route_id)
        name = 'test_' + type_
        control_sequences[name] = route_token
        attr_value = 'value_' + type_
        tok = dummy_token.copy()
        tok.value['attribute'] = attr_value
        t_map[route_id] = tok
    return control_sequences


def test_router_resolve_name():
    route_id = 1
    macros, parameters, primitives = {}, {}, {}
    type_map = {
        'macro': macros,
        'parameter': parameters,
        'primitive': primitives,
    }
    control_sequences = prepare_control_sequences(type_map, route_id)
    r = CSRouter(control_sequences=control_sequences,
                 macros=macros,
                 let_chars={},
                 parameters=parameters,
                 primitives=primitives,
                 enclosing_scope=None)
    name_to_expected_token_map = {
        'test_macro': macros[route_id],
        'test_parameter': parameters[route_id],
        'test_primitive': primitives[route_id],
    }
    for name in control_sequences:
        d = r.resolve_control_sequence_to_token(name=name)
        # Check 'name' matches the call, not the underlying token name.
        assert d.value['name'] == name
        # But is in other ways identical.
        assert d.equal_contents_to(name_to_expected_token_map[name])


def test_router_let():
    route_id = 1
    macros, parameters, primitives = {}, {}, {}
    type_map = {
        'macro': macros,
        'parameter': parameters,
        'primitive': primitives,
    }
    control_sequences = prepare_control_sequences(type_map, route_id)
    r = CSRouter(control_sequences=control_sequences,
                 macros=macros,
                 let_chars={},
                 parameters=parameters,
                 primitives=primitives,
                 enclosing_scope=None)

    # Alias 'something_let' to 'something' and check they return the same.
    for name in ('test_macro', 'test_parameter', 'test_primitive'):
        new_let_name = name + '_let'
        call_token = get_call_token(name)
        r.do_let_assignment(new_name=new_let_name, target_token=call_token)
        d_old = r.resolve_control_sequence_to_token(name=name)
        d_new = r.resolve_control_sequence_to_token(name=new_let_name)
        assert d_old.equal_contents_to(d_new)

    # Alias some things to overwrite and check they stay correct.

    # Make 'test_macro' refer to our primitive token.
    r.do_let_assignment(new_name='test_macro',
                        target_token=get_call_token('test_primitive'))
    # Check 'test_macro' now returns the primitive token.
    d_1 = r.resolve_control_sequence_to_token(name='test_macro')
    assert d_1.equal_contents_to(primitives[route_id])
    # Check so does the original call, 'test_primitive'.
    d_2 = r.resolve_control_sequence_to_token(name='test_primitive')
    assert d_2.equal_contents_to(primitives[route_id])
    assert d_2.equal_contents_to(d_1)
    # And so does the let primitive version.
    d_4 = r.resolve_control_sequence_to_token(name='test_primitive_let')
    assert d_4.equal_contents_to(primitives[route_id])
    assert d_4.equal_contents_to(d_1)
    assert d_4.equal_contents_to(d_2)
    # But the let version, 'test_macro_let', still returns the macro token.
    d_3 = r.resolve_control_sequence_to_token(name='test_macro_let')
    assert d_3.equal_contents_to(macros[route_id])
    assert not d_3.equal_contents_to(primitives[route_id])
