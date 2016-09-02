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
