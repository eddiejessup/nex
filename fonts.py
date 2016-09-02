from enum import Enum
from typer import terminal_primitive_control_sequences_map


class FontInfo(object):

    def __init__(self, file_name, at_clause):
        self.at_size = None
        self.design_size = None
        self.name = None
        self.area = None
        self.glue = None
        self.hyphen_char = None
        self.skew_char = None


class FontRange(Enum):
    text = terminal_primitive_control_sequences_map['textfont']
    script = terminal_primitive_control_sequences_map['scriptfont']
    scriptscript = terminal_primitive_control_sequences_map['scriptscriptfont']


get_empty_font_family = lambda: {font_range: None for font_range in FontRange}


class FontState(object):

    def __init__(self):
        self.font = None
        self.font_control_sequences = {}
        self.font_families = {i: get_empty_font_family() for i in range(16)}

    def set_skew_char(self, name, number):
        self.font_control_sequences[name].skew_char = number

    def set_hyphen_char(self, name, number):
        self.font_control_sequences[name].hyphen_char = number

    def name_is_font_control_sequence(self, name):
        return name in self.font_control_sequences

    def do_font_definition(self, name, file_name, at_clause):
        # TODO: do this properly.
        font_info = FontInfo(file_name, at_clause)
        self.font_control_sequences[name] = font_info

    def set_font_family(self, family_nr, font_range, name):
        self.font_families[family_nr][font_range] = name

    def set_current_font(self, name):
        if name not in self.font_control_sequences:
            raise ValueError
        self.font = name
