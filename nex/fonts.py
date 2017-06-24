import os
from enum import Enum
from functools import lru_cache

from .pydvi.TeXUnit import pt2sp
from .pydvi.Font.TfmParser import TfmParser

from .constants.instructions import Instructions
from .utils import ensure_extension, find_file
from .accessors import NotInScopeError
from .feedback import drep


@lru_cache(maxsize=512)
def scale(design_size, d):
    return round(pt2sp(d * design_size))


class FontInfo:

    def __init__(self, file_name, file_path, at_clause):
        if file_name is None:
            self._font_info = None
        else:
            self._font_info = TfmParser.parse(font_name=file_name,
                                              filename=file_path)
        self.at_clause = at_clause

        self.at_size = None
        self.name = None
        self.area = None
        self.glue = None
        self.hyphen_char = None
        self.skew_char = None

    @property
    def font_info(self):
        if self._font_info is not None:
            return self._font_info
        else:
            raise AttributeError('Null font has no font information')

    @property
    def file_name(self):
        return self.font_info.filename

    @property
    def font_name(self):
        return self.font_info.font_name

    def char_info(self, code):
        return self.font_info[code]

    @property
    def design_size(self):
        return self.font_info.design_font_size

    def scale(self, d):
        return scale(self.design_size, d)

    @property
    def slant(self):
        # 'Slant per point'. See TeXbook page 375.
        # Disable until I understand what it means and its units.
        raise NotImplementedError
        return self.font_info.slant

    @property
    def extra_space(self):
        return self.scale(self.font_info.extra_space)

    @property
    def quad(self):
        return self.scale(self.font_info.quad)

    @property
    def space_shrink(self):
        return self.scale(self.font_info.space_shrink)

    @property
    def space_stretch(self):
        return self.scale(self.font_info.space_stretch)

    @property
    def spacing(self):
        return self.scale(self.font_info.spacing)

    @property
    def x_height(self):
        return self.scale(self.font_info.x_height)

    @lru_cache(maxsize=512)
    def width(self, code):
        return self.scale(self.char_info(code).width)

    @lru_cache(maxsize=512)
    def height(self, code):
        return self.scale(self.char_info(code).height)

    @lru_cache(maxsize=512)
    def depth(self, code):
        return self.scale(self.char_info(code).depth)

    def __repr__(self):
        a = [
            f'file_name="{self.file_name}"',
            f'font_name="{self.font_name}"',
        ]
        return drep(self, a)

    @property
    def em_size(self):
        return self.font_info.em_size

    @property
    def ex_size(self):
        return self.font_info.ex_size


class FontRange(Enum):
    text = Instructions.text_font.value
    script = Instructions.script_font.value
    scriptscript = Instructions.script_script_font.value


class FontState:

    def __init__(self, font_families):
        self._current_font_id = None
        self.font_families = font_families

    @staticmethod
    def default_initial_font_families():
        def get_empty_font_family():
            return {font_range: None for font_range in FontRange}
        font_families = {i: get_empty_font_family() for i in range(16)}
        return font_families

    @classmethod
    def default_initial(cls):
        font_families = cls.default_initial_font_families()
        font_state = cls(font_families)
        font_state.set_current_font(GlobalFontState.null_font_id)
        return font_state

    @classmethod
    def default_local(cls, enclosing_scope):
        font_families = cls.default_initial_font_families()
        return cls(font_families)

    def __repr__(self):
        a = [
            f'font_id={self._current_font_id}',
        ]
        return drep(self, a)

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
        raise NotInScopeError


class GlobalFontState:

    null_font_id = 0
    FontInfo = FontInfo

    def __init__(self, search_paths=None):
        null_font = self.FontInfo(file_name=None, file_path=None,
                                  at_clause=None)
        self.fonts = {self.null_font_id: null_font}
        # TODO: Avoid multiple entries.
        self.search_paths = [os.getcwd()]
        if search_paths is not None:
            self.search_paths.extend(search_paths)

    def set_skew_char(self, font_id, number):
        self.fonts[font_id].skew_char = number

    def set_hyphen_char(self, font_id, number):
        self.fonts[font_id].hyphen_char = number

    @property
    def null_font(self):
        return self.fonts[self.null_font_id]

    def get_font(self, font_id):
        return self.fonts[font_id]

    def define_new_font(self, file_name, at_clause):
        file_path = find_file(ensure_extension(file_name, 'tfm'),
                              search_paths=self.search_paths)
        # TODO: do this properly.
        font_info = FontInfo(file_name, file_path, at_clause)
        font_id = max(self.fonts.keys()) + 1
        self.fonts[font_id] = font_info
        # Return new font id.
        return font_id
