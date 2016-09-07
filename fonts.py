from enum import Enum

from utils import get_unique_id
from typer import terminal_primitive_control_sequences_map


class FontInfo(object):

    def __init__(self, file_name, at_clause):
        # Hacky short-term.
        self.file_name = file_name
        self.at_clause = at_clause

        self.at_size = None
        self.design_size = None
        self.name = None
        self.area = None
        self.glue = None
        self.hyphen_char = None
        self.skew_char = None

    def __repr__(self):
        fields = ('file_name', 'at_clause')
        field_args = ((f, self.__dict__[f]) for f in fields)
        args = (','.join('{}={}'.format(k, v) for k, v in field_args))
        return '{}<{}>'.format(self.__class__.__name__, args)

    @property
    def em_size(self):
        return 1

    @property
    def ex_size(self):
        return 1


class FontRange(Enum):
    text = terminal_primitive_control_sequences_map['textfont']
    script = terminal_primitive_control_sequences_map['scriptfont']
    scriptscript = terminal_primitive_control_sequences_map['scriptscriptfont']


get_empty_font_family = lambda: {font_range: None for font_range in FontRange}


def get_initial_font_families():
    font_families = {i: get_empty_font_family() for i in range(16)}
    return font_families


def get_initial_font_state(global_font_state):
    font_families = get_initial_font_families()
    font_state = FontState(font_families)
    font_state.set_current_font(global_font_state.null_font_id)
    return font_state


def get_local_font_state():
    # Much like global, because I think we need to define the data structure so
    # we can read and write to it easily. But we should make it so that if the
    # entry is None, we raise a KeyError.
    font_families = get_initial_font_families()
    font_state = FontState(font_families)
    return font_state


class FontState(object):

    def __init__(self, font_families):
        self._current_font_id = None
        self.font_families = font_families

    def set_font_family(self, family_nr, font_range, font_id):
        self.font_families[family_nr][font_range] = font_id

    # TODO: make font_family getter, but raise KeyError if entry is None.

    def set_current_font(self, font_id):
        self._current_font_id = font_id

    @property
    def current_font_id(self):
        # We raise an error on None, because we will be calling this from a
        # scope. If the font is None, we want to go to the outer scope, which
        # we know to do when a KeyError is raised.
        if self._current_font_id is not None:
            return self._current_font_id
        raise KeyError


class GlobalFontState(object):

    null_font_id = 0

    def __init__(self):
        null_font = FontInfo(file_name=None, at_clause=None)
        self.fonts = {self.null_font_id: null_font}

    def set_skew_char(self, font_id, number):
        self.fonts[font_id].skew_char = number

    def set_hyphen_char(self, font_id, number):
        self.fonts[font_id].hyphen_char = number

    @property
    def null_font(self):
        return self.fonts[self.null_font_id]

    def define_new_font(self, file_name, at_clause):
        # TODO: do this properly.
        font_info = FontInfo(file_name, at_clause)
        font_id = get_unique_id()
        self.fonts[font_id] = font_info
        # Return new font id.
        return font_id
