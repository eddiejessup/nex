import pytest

from nex.state import GlobalState, Mode
from nex.fonts import GlobalFontState
from nex import box
from nex.box_writer import write_to_dvi_file
from nex.utils import ExecuteCommandError

from common import ITok, DummyInstructions


do_output = True
font_path = '/Users/ejm/projects/nex/fonts'


class DummyFontInfo:

    def __init__(self, file_name, file_path, at_clause):
        self.font_name = file_name
        self.file_name = file_name
        self.file_path = file_path
        self.at_clause = at_clause
        self.width = lambda code: 1
        self.height = lambda code: 1
        self.depth = lambda code: 1
        self.x_height = 1


class DummyGlobalFontState(GlobalFontState):

    FontInfo = DummyFontInfo

    def define_new_font(self, file_name, at_clause):
        font_info = DummyFontInfo(file_name=file_name,
                                  file_path=f'/dummy/font/path/{file_name}',
                                  at_clause=at_clause)
        font_id = max(self.fonts.keys()) + 1
        self.fonts[font_id] = font_info
        # Return new font id.
        return font_id


@pytest.fixture
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
