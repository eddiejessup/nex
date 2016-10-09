import os

import pytest

from nex.expander import Expander, NoSuchControlSequence
from nex.common import Token
from nex.typer import control_sequence_lex_type

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')


def test_expander():
    e = Expander(control_sequences={},
                 macros={},
                 let_chars={},
                 parameters={},
                 primitives={},
                 enclosing_scope=None)
    with pytest.raises(NoSuchControlSequence):
        # General.
        e.resolve_control_sequence_to_token(name='test')
    with pytest.raises(NoSuchControlSequence):
        # Macro.
        e.expand_macro_to_token_list(name='test', arguments=[])
    with pytest.raises(NoSuchControlSequence):
        # Let.
        dummy_token = Token(type_='dummy',
                            value={'lex_type': control_sequence_lex_type,
                                   'name': 'test'})
        e.do_let_assignment(target_token=dummy_token, new_name='test_2')
    with pytest.raises(NoSuchControlSequence):
        # Parameter.
        e.get_parameter_value(name='test')
