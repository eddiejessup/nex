from collections import deque

import pytest

from nex.constants.instructions import Instructions
from nex.constants.specials import Specials
from nex.state import Mode, GlobalState
from nex import box
from nex.box_writer import write_to_dvi_file
from nex.state import ExecuteCommandError
from nex.utils import UserError
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
    font_id = state.load_new_font(file_name='cmr10', at_clause=None)
    state._select_font(is_global=True, font_id=font_id)
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
    lst = state.current_page
    assert len(lst) == 3
    assert isinstance(lst[0], box.FontDefinition)
    assert isinstance(lst[1], box.FontSelection)
    assert isinstance(lst[2], box.HBox)
    hbox = lst[2]
    assert isinstance(hbox.contents[0], box.HBox)
    assert isinstance(hbox.contents[1], box.Character)
    write(state, 'test_single_letter.dvi')


def test_token_executor(state):
    tok = ITok(instruction=DummyInstructions.test, value=None)
    with pytest.raises(ExecuteCommandError):
        state.execute_command_token(tok, banisher=None)
    with pytest.raises(ExecuteCommandError):
        state.execute_command_tokens(iter([tok]), banisher=None)


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
    state.push_mode(Mode.horizontal)
    state.add_v_rule(width=int(1e7), height=int(1e2), depth=0)
    state.add_v_rule(width=int(1e7), height=int(1e2), depth=int(1e7))
    state.do_paragraph()
    assert len(state.modes) == 1
    assert state.mode == Mode.vertical
    lst = state.current_page
    assert isinstance(lst[2], box.HBox)
    h_box = lst[2]
    assert isinstance(h_box.contents[0], box.Rule)
    assert isinstance(h_box.contents[1], box.Rule)
    write(state, 'test_v_rule.dvi')


def nr_tok(n):
    v = BuiltToken(type_='internal_number', value=n)
    return BuiltToken(type_='number', value=v)


def test_if_num(state):
    assert state.evaluate_if_num(2, 2, '=')
    assert state.evaluate_if_num(5, 0, '>')
    assert not state.evaluate_if_num(-6, -10, '<')


def test_if_dimen(state):
    assert state.evaluate_if_dim(2, 2, '=')
    assert state.evaluate_if_dim(5, 0, '>')
    assert not state.evaluate_if_dim(-6, -10, '<')


def test_if_odd(state):
    assert not state.evaluate_if_odd(2)
    assert state.evaluate_if_odd(5)
    assert not state.evaluate_if_odd(-6)
    assert state.evaluate_if_odd(-1)
    assert not state.evaluate_if_odd(0)


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
    assert state.evaluate_if_case(2) == 2
    assert state.evaluate_if_case(5) == 5
    with pytest.raises(ValueError):
        state.evaluate_if_case(-6)


def test_set_box(state):
    box_item = box.HBox(contents=[])
    state.set_box_register(token_source=None, i=2, item=box_item, is_global=False)
    state.append_register_box(i=2, copy=False)
    lst = state.current_page
    assert lst[-1].contents is box_item.contents


def test_set_box_void(state):
    nr_elems_before = len(state.current_page)
    state.append_register_box(i=2, copy=False)
    nr_elems_after = len(state.current_page)
    assert nr_elems_before == nr_elems_after


def test_unbox(state):
    box_item = box.VBox([
        box.HBox([
            box.Glue(20),
        ]),
        box.Glue(100),
    ])

    i_reg = 2
    state.set_box_register(token_source=None, i=i_reg, item=box_item, is_global=False)
    nr_elems_before = len(state.current_page)
    state.append_unboxed_register_v_box(i=i_reg, copy=True)
    nr_elems_after = len(state.current_page)
    assert nr_elems_after == nr_elems_before + 2
    unboxed_contents = state.get_unboxed_register_box(i=i_reg, copy=False,
                                                      horizontal=False)
    inner_glue = unboxed_contents[0].contents[0]
    assert isinstance(inner_glue, box.Glue)
    assert inner_glue.is_set

    outer_glue = unboxed_contents[1]
    assert isinstance(outer_glue, box.Glue)
    assert not outer_glue.is_set

    # Should be empty now, because I called with copy == False just then.
    assert state.get_register_box(i=i_reg, copy=False) is None


def test_unbox_bad_box_type(state):
    box_item = box.HBox(contents=[box.Rule(1, 1, 1), box.Rule(2, 2, 2)])
    state.set_box_register(token_source=None, i=2, item=box_item, is_global=False)
    with pytest.raises(UserError):
        state.append_unboxed_register_v_box(i=2, copy=False)


def test_get_box_dimen(state):
    box_item = box.HBox(contents=[], to=100)
    state.set_box_register(token_source=None, i=2, item=box_item, is_global=False)
    b = state.get_box_dimen(i=2, type_=Instructions.box_dimen_width.value)
    assert b == 100


def test_command_token_set_box(state):
    i_reg = 5
    box_tok = BuiltToken(type_=Instructions.h_box.value,
                         value={'contents': [], 'specification': None})
    set_box_tok = BuiltToken(type_=Instructions.set_box.value,
                             value={'box': box_tok, 'nr': nr_tok(i_reg), 'global': True})
    state.execute_command_token(set_box_tok, banisher=None)


def test_command_token_get_box(state):
    i_reg = 5
    # Get a box in to retrieve.
    box_item = box.HBox(contents=[])
    state.set_box_register(token_source=None, i=i_reg, item=box_item, is_global=False)

    get_box_tok = BuiltToken(type_=Instructions.box.value,
                             value=nr_tok(i_reg))
    state.execute_command_token(get_box_tok, banisher=None)
    lst = state.current_page
    assert lst[-1].contents is box_item.contents
    state.get_register_box(i=i_reg, copy=False) is None


def test_command_token_add_h_rule(state):
    add_h_rule_tok = BuiltToken(type_=Instructions.h_rule.value,
                                value={'width': None,
                                       'height': None,
                                       'depth': None})
    state.execute_command_token(add_h_rule_tok, banisher=None)
    lst = state.current_page
    assert len(lst) == 3
    assert isinstance(lst[2], box.Rule)
    rule = lst[2]
    assert rule.width == 0
    assert rule.depth == 0
    assert rule.height > 0


def test_command_token_code_assignment(state):
    set_sf_tok = BuiltToken(type_='code_assignment',
                            value={'code_type': Instructions.space_factor_code.value,
                                   'char': nr_tok(ord('a')),
                                   'code': nr_tok(900),
                                   'global': True})
    state.execute_command_token(set_sf_tok, banisher=None)
    assert state.codes.get_space_factor_code('a') == 900


def test_command_token_unbox(state):
    i_reg = 3
    box_item = box.VBox(contents=[box.Rule(1, 1, 1), box.Rule(2, 2, 2)])
    state.set_box_register(token_source=None, i=i_reg, item=box_item, is_global=False)
    nr_elems_before = len(state.current_page)

    get_box_tok = BuiltToken(type_='un_box',
                             value={'nr': nr_tok(i_reg),
                                    'cmd_type': Instructions.un_v_copy})
    state.execute_command_token(get_box_tok, banisher=None)
    nr_elems_after = len(state.current_page)
    assert nr_elems_after == nr_elems_before + 2
    # Should still work, since copy == True.
    state.get_register_box(i=i_reg, copy=False)


def test_space_factor(state):
    state.do_indent()
    a_sf = 900
    state.codes.set(code_type=Instructions.space_factor_code.value,
                    char='a',
                    code=a_sf,
                    is_global=False)
    state.codes.set(code_type=Instructions.space_factor_code.value,
                    char='b',
                    code=1100,
                    is_global=False)
    # Check space factor starts at 1000.
    assert state.specials.get(Specials.space_factor) == 1000
    # Check space factor changes to letter's space factor after adding it.
    state.add_character_char('a')
    assert state.specials.get(Specials.space_factor) == a_sf
    # Check space factor does't jump from less than 1000 to more than 1000.
    state.add_character_char('b')
    assert state.specials.get(Specials.space_factor) == 1000
    # Make space factor be non-1000, then check adding a non-character box sets
    # it back to 1000.
    state.add_character_char('a')
    state.add_v_rule(10, 10, 10)
    assert state.specials.get(Specials.space_factor) == 1000


class DummyTokenQueue:

    def replace_tokens_on_input(self, tokens):
        pass


def test_after_group(state):
    # Input "{\aftergroup\space \aftergroup a}".

    state.start_local_group()
    t_sp = ITok(Instructions.space)
    state.push_to_after_group_queue(t_sp)
    assert list(state.after_group_queue) == [t_sp]

    t_a = ITok(Instructions.a)
    state.push_to_after_group_queue(t_a)
    assert list(state.after_group_queue) == [t_sp, t_a]

    tok_source = DummyTokenQueue()

    state.end_group(tok_source)
    assert not state.after_group_queue


def test_after_group_scoped(state):
    # Input "{\aftergroup\space {\aftergroup a}}".

    state.start_local_group()
    t_sp = ITok(Instructions.space)
    state.push_to_after_group_queue(t_sp)
    assert list(state.after_group_queue) == [t_sp]

    # Assume we have 'b' waiting on the queue to be executed.
    tok_source = DummyTokenQueue()

    state.start_local_group()
    t_a = ITok(Instructions.a)
    state.push_to_after_group_queue(t_a)
    assert list(state.after_group_queue) == [t_a]
    state.end_group(tok_source)
    assert list(state.after_group_queue) == [t_sp]

    state.end_group(tok_source)
    assert not state.after_group_queue
