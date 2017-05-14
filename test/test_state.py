import pytest

from nex.state import GlobalState, Mode
from nex.accessors import Parameters
from nex.fonts import GlobalFontState
from nex import box
from nex.box_writer import write_to_dvi_file

from test_banisher import test_char_to_cat


do_output = False
font_path = '/Users/ejm/projects/nex/example/fonts'


class DummyCodes:
    def __init__(self, char_to_cat):
        if char_to_cat is None:
            self.char_to_cat = test_char_to_cat.copy()
        else:
            self.char_to_cat = char_to_cat

    def get_cat_code(self, char):
        return self.char_to_cat[char]

    def get_lower_case_code(self, c):
        return c.lower()

    def get_upper_case_code(self, c):
        return c.upper()


class DummyRouter:

    def __init__(self, cs_map):
        self.cs_map = cs_map

    def lookup_control_sequence(self, name, *args, **kwargs):
        canon_token = self.cs_map[name]
        return canon_token.copy(*args, **kwargs)


class DummyFontState:

    def __init__(self):
        self._current_font_id = 0

    def set_current_font(self, is_global, font_id):
        self._current_font_id = font_id

    @property
    def current_font_id(self):
        return self._current_font_id


class DummyNamedValues:

    def __init__(self, param_map):
        self.param_map = param_map

    def get(self, name, *args, **kwargs):
        return self.param_map[name]


class DummyFontInfo:

    def __init__(self, file_name, file_path, at_clause):
        self.font_name = file_name
        self.file_name = file_name
        self.file_path = file_path
        self.at_clause = at_clause


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


font_path = '/Users/ejm/projects/nex/example/fonts'


def get_state(char_to_cat, cs_map, param_map):
    router = DummyRouter(cs_map)
    parameters = DummyNamedValues(param_map)
    specials = DummyNamedValues({})
    codes = DummyCodes(char_to_cat)
    font = DummyFontState()
    if do_output:
        global_font_state = GlobalFontState(search_paths=[font_path])
    else:
        global_font_state = DummyGlobalFontState()
    state = GlobalState(global_font_state=global_font_state,
                        specials=specials,
                        codes=codes, registers=None,
                        scoped_font_state=font, router=router,
                        parameters=parameters)
    font_id = state.define_new_font(file_name='cmr10', at_clause=None)
    state.select_font(is_global=True, font_id=font_id)
    return state


def g(d, str, shr):
    return {'dimen': d, 'stretch': str, 'shrink': shr}


params = {
    Parameters.par_skip: g(10, 0, 0),
    Parameters.par_indent: 100,
    Parameters.par_fill_skip: g(10, 0, 0),
    Parameters.h_size: 10,
    Parameters.base_line_skip: g(10, 0, 0),
    Parameters.mag: 1000
}


def test_single_letter():
    state = get_state(test_char_to_cat, {}, params)
    state.add_character_char('a')
    state.do_paragraph()
    assert len(state.modes) == 1
    assert state.mode == Mode.vertical
    lst = state._layout_list
    assert len(lst) == 3
    assert isinstance(lst[0], box.FontDefinition)
    assert isinstance(lst[1], box.FontSelection)
    assert isinstance(lst[2], box.Character)
    if do_output:
        write_to_dvi_file(state, 'test_single_letter.dvi')


def test_solo_accent():
    state = get_state(test_char_to_cat, {}, params)
    state.add_character_code(23)
    state.do_paragraph()
    if do_output:
        write_to_dvi_file(state, 'test_accent.dvi')


def test_rule():
    state = get_state(test_char_to_cat, {}, params)
    state.add_rule(width=int(1e7), height=int(1e2), depth=0)
    state.add_rule(width=int(1e7), height=int(1e2), depth=int(1e7))
    state.do_paragraph()
    assert len(state.modes) == 1
    assert state.mode == Mode.vertical
    lst = state._layout_list
    assert isinstance(lst[2], box.Rule)
    assert isinstance(lst[3], box.Rule)
    if do_output:
        write_to_dvi_file(state, 'test_v_rule.dvi')
