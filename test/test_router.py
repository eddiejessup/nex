import os

import pytest

from nex.router import CSRouter
from nex.utils import NoSuchControlSequence
from nex.common import Token
from nex.typer import control_sequence_lex_type

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


def test_router_resolution():
    route_id = 1
    route_token_macro = Token(type_='macro', value=route_id)
    route_token_parameter = Token(type_='parameter', value=route_id)
    route_token_primitive = Token(type_='primitive', value=route_id)
    control_sequences = {'test_macro': route_token_macro,
                         'test_param': route_token_parameter,
                         'test_primitive': route_token_primitive,
                         }
    macros = {route_id: dummy_token}
    parameters = {route_id: dummy_token}
    primitives = {route_id: dummy_token}
    e = CSRouter(control_sequences=control_sequences,
                 macros=macros,
                 let_chars={},
                 parameters=parameters,
                 primitives=primitives,
                 enclosing_scope=None)
    for name in ('test_macro', 'test_param', 'test_primitive'):
        d = e.resolve_control_sequence_to_token(name=name)
        assert d.value['name'] == name
        assert d.type == 'dummy'


def test_router_let_control_sequence():
    route_id = 1
    control_sequences = {}
    macros, parameters, primitives = {}, {}, {}
    type_map = {
        'macro': macros,
        'parameter': parameters,
        'primitive': primitives,
    }
    for type_, t_map in type_map.items():
        route_token = Token(type_=type_, value=route_id)
        name = 'test_' + type_
        control_sequences[name] = route_token
        attr_value = 'value_' + type_
        tok = dummy_token.copy()
        tok.value['attribute'] = attr_value
        t_map[route_id] = tok
    e = CSRouter(control_sequences=control_sequences,
                 macros=macros,
                 let_chars={},
                 parameters=parameters,
                 primitives=primitives,
                 enclosing_scope=None)
    # Alias 'something_let' to 'something' and check they return the same.
    for name in ('test_macro', 'test_parameter', 'test_primitive'):
        new_let_name = name + '_let'
        call_token = get_call_token(name)
        e.do_let_assignment(new_name=new_let_name, target_token=call_token)
        d_old = e.resolve_control_sequence_to_token(name=name)
        d_new = e.resolve_control_sequence_to_token(name=new_let_name)
        assert d_old.equal_contents_to(d_new)

    # Alias some things to overwrite and check they stay correct.

    # Make 'test_macro' refer to our primitive token.
    e.do_let_assignment(new_name='test_macro',
                        target_token=get_call_token('test_primitive'))
    # Check 'test_macro' now returns the primitive token.
    d_1 = e.resolve_control_sequence_to_token(name='test_macro')
    # As does the original call, 'test_primitive'.
    d_2 = e.resolve_control_sequence_to_token(name='test_primitive')
    # And the let primitive version.
    d_4 = e.resolve_control_sequence_to_token(name='test_primitive_let')
    assert d_1.equal_contents_to(d_2)
    assert d_1.equal_contents_to(primitives[route_id])
    assert d_1.equal_contents_to(d_4)
    # But the let version, 'test_macro_let', still returns the macro token.
    d_3 = e.resolve_control_sequence_to_token(name='test_macro_let')
    assert d_3.equal_contents_to(macros[route_id])
