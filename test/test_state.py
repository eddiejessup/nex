import pytest

from nex.parsing.command_parser import command_parser
from nex.banisher import Banisher
from nex.parsing.utils import safe_chunk_grabber
from nex.state import GlobalState, Mode
from nex.tex_parameters import Parameters
from nex import box
from nex.box_writer import write_to_file

from test_banisher import test_char_to_cat


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


class DummyParameters:

    def __init__(self, param_map):
        self.param_map = param_map

    def get(self, name, *args, **kwargs):
        return self.param_map[name]


font_path = '/Users/ejm/projects/nex/example/fonts'


def get_state(char_to_cat, cs_map, param_map):
    router = DummyRouter(cs_map)
    parameters = DummyParameters(param_map)
    codes = DummyCodes(char_to_cat)
    font = DummyFontState()
    return GlobalState(font_search_paths=[font_path],
                       codes=codes, registers=None,
                       scoped_font_state=font, router=router,
                       parameters=parameters)


def test():
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
    state = get_state(test_char_to_cat, {}, params)
    font_id = state.define_new_font(file_name='cmr10', at_clause=None)
    state.select_font(is_global=True, font_id=font_id)
    state.add_character('a')
    state.do_paragraph()
    assert len(state.modes) == 1
    assert state.mode == Mode.vertical
    lst = state._layout_list
    assert len(lst) == 3
    assert isinstance(lst[0], box.FontDefinition)
    assert isinstance(lst[1], box.FontSelection)
    assert isinstance(lst[2], box.Character)
    out_path = 'state_test.dvi'
    write_to_file(state, out_path)
