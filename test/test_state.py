import pytest

from nex.state import Mode, GlobalState
from nex import box
from nex.instructions import Instructions
from nex.box_writer import write_to_dvi_file
from nex.utils import ExecuteCommandError, NotInScopeError
from nex.tokens import BuiltToken
from nex.fonts import GlobalFontState

from common import ITok, DummyInstructions, DummyGlobalFontState


do_output = False
font_path = '/Users/ejm/projects/nex/fonts'


@pytest.fixture()
def state():
    if do_output:
        global_font_state = GlobalFontState(search_paths=[font_path])
    else:
        global_font_state = DummyGlobalFontState()
    state = GlobalState.from_defaults(global_font_state=global_font_state)
    font_id = state.define_new_font(file_name='cmr10', at_clause=None)
    state.select_font(is_global=True, font_id=font_id)
    return state


def write(state, file_name):
    if do_output:
        write_to_dvi_file(state, file_name, write_pdf=True)


def test_single_letter(state):
    state.do_indent()
    state.add_character_char('a')
    state.do_paragraph()
    assert len(state.modes) == 1
    assert state.mode == Mode.vertical
    lst = state._layout_list
    assert len(lst) == 5
    assert isinstance(lst[0], box.FontDefinition)
    assert isinstance(lst[1], box.FontSelection)
    assert isinstance(lst[2], box.UnSetGlue)
    assert isinstance(lst[3], box.HBox)
    assert isinstance(lst[4], box.UnSetGlue)
    hbox = lst[3]
    assert isinstance(hbox.contents[1], box.Character)
    write(state, 'test_single_letter.dvi')


def test_token_executor(state):
    tok = ITok(instruction=DummyInstructions.test, value=None)
    with pytest.raises(ValueError):
        state.execute_command_token(tok, banisher=None, reader=None)
    with pytest.raises(ExecuteCommandError):
        state.execute_command_tokens(iter([tok]), banisher=None, reader=None)
    with pytest.raises(ExecuteCommandError):
        state.execute_next_command_token(iter([tok]), banisher=None, reader=None)


def test_solo_accent(state):
    state.do_indent()
    state.do_accent(accent_code=23, target_code=None)
    state.do_paragraph()
    write(state, 'test_solo_accent.dvi')


def test_paired_accent(state):
    state.do_indent()
    state.do_accent(accent_code=127, target_code=ord('O'))
    state.do_accent(accent_code=127, target_code=ord('o'))
    state.add_character_char('O')
    state.add_character_char('o')
    state.do_paragraph()
    write(state, 'test_accent.dvi')


def test_v_rule(state):
    state.add_rule(width=int(1e7), height=int(1e2), depth=0)
    state.add_rule(width=int(1e7), height=int(1e2), depth=int(1e7))
    state.do_paragraph()
    assert len(state.modes) == 1
    assert state.mode == Mode.vertical
    lst = state._layout_list
    assert isinstance(lst[2], box.Rule)
    assert isinstance(lst[3], box.Rule)
    write(state, 'test_v_rule.dvi')


def nr_tok(n):
    v = BuiltToken(type_='internal_number', value=n)
    return BuiltToken(type_='number', value=v)


def test_if_num(state):
    assert state.evaluate_if_num(nr_tok(2), nr_tok(2), '=')
    assert state.evaluate_if_num(nr_tok(5), nr_tok(0), '>')
    assert not state.evaluate_if_num(nr_tok(-6), nr_tok(-10), '<')


def test_if_dimen(state):
    assert state.evaluate_if_dim(nr_tok(2), nr_tok(2), '=')
    assert state.evaluate_if_dim(nr_tok(5), nr_tok(0), '>')
    assert not state.evaluate_if_dim(nr_tok(-6), nr_tok(-10), '<')


def test_if_odd(state):
    assert not state.evaluate_if_odd(nr_tok(2))
    assert state.evaluate_if_odd(nr_tok(5))
    assert not state.evaluate_if_odd(nr_tok(-6))
    assert state.evaluate_if_odd(nr_tok(-1))
    assert not state.evaluate_if_odd(nr_tok(0))


def test_if_mode(state):
    assert state.evaluate_if_v_mode()
    assert not state.evaluate_if_h_mode()
    assert not state.evaluate_if_m_mode()
    assert not state.evaluate_if_inner_mode()
    state.do_indent()
    assert not state.evaluate_if_v_mode()
    assert state.evaluate_if_h_mode()
    assert not state.evaluate_if_m_mode()
    assert not state.evaluate_if_inner_mode()


def test_if_case(state):
    assert state.evaluate_if_case(nr_tok(2)) == 2
    assert state.evaluate_if_case(nr_tok(5)) == 5
    with pytest.raises(ValueError):
        state.evaluate_if_case(nr_tok(-6))


def test_set_box(state):
    box_item = box.HBox(contents=[])
    state.set_box_register(i=2, item=box_item, is_global=False)
    state.append_box_register(i=2, copy=False)
    lst = state._layout_list
    assert lst[-1].contents is box_item.contents


def test_set_box_fail(state):
    with pytest.raises(NotInScopeError):
        state.append_box_register(i=2, copy=False)


def test_get_box_dimen(state):
    box_item = box.HBox(contents=[], to=100)
    state.set_box_register(i=2, item=box_item, is_global=False)
    b = state.get_box_dimen(i=2, type_=Instructions.box_dimen_width.value)
    assert b == 100


def test_command_token_set_box(state):
    i_reg = 5
    box_tok = BuiltToken(type_='h_box', value={'contents': [], 'specification': None})
    set_box_tok = BuiltToken(type_=Instructions.set_box.value,
                             value={'box': box_tok, 'nr': nr_tok(i_reg), 'global': True})
    state.execute_command_token(set_box_tok, banisher=None, reader=None)
