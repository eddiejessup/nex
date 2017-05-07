from enum import Enum

from .fonts import GlobalFontState
from .scopes import (ScopedCodes, ScopedRegisters, ScopedRouter,
                     ScopedParameters, ScopedFontState)


class Mode(Enum):
    # Building the main vertical list.
    vertical = 'V'
    # Building a vertical list for a vbox.
    internal_vertical = 'IV'
    # Building a horizontal list for a paragraph.
    horizontal = 'H'
    # Building a horizontal list for an hbox.
    restricted_horizontal = 'RH'
    # Building a formula to be placed in a horizontal list.
    math = 'M'
    # Building a formula to be placed on a line by itself,
    # interrupting the current paragraph.
    display_math = 'DM'


vertical_modes = (Mode.vertical, Mode.internal_vertical)
horizontal_modes = (Mode.horizontal, Mode.restricted_horizontal)


class Group(Enum):

    # Note, this is *not* the same as 'global scope'. We could enter
    # sub-groups that do not start a new scope, such as a math group.
    outside = 0
    # For 'local structure'.
    local = 1
    # \hbox{...}.
    h_box = 2
    # \hbox{...} in vertical mode.
    adjusted_h_box = 3
    # \vbox{...}.
    v_box = 4
    # \vtop{...}.
    v_top = 5
    # \halign{...} and \valign{...}.
    align = 6
    # \noalign{...}.
    no_align = 7
    # Output routine.
    output = 8
    # For things such as '^{...}'
    math = 9
    # \discretionary{...}{...}{...}.
    discretionary = 10
    # \insert{...} and \vadjust{...}
    insert = 11
    # \vcenter{...}
    v_center = 12
    # \mathchoice{...}{...}{...}{...}
    math_choice = 13
    # \begingroup...\endgroup
    local_verbose = 14
    # $...$
    math_shift = 15
    # \left...\right
    math_left_right = 16


class GlobalState(object):

    def __init__(self, font_search_paths,
                 codes, registers, scoped_font_state, router, parameters):
        self.global_font_state = GlobalFontState(font_search_paths)

        self.codes = codes
        self.registers = registers
        self.scoped_font_state = scoped_font_state
        self.router = router
        self.parameters = parameters

        # At the beginning, TeX is in vertical mode, ready to construct pages.
        self.modes = [(Mode.vertical, [])]
        self.groups = [Group.outside]

    @classmethod
    def from_defaults(cls, font_search_paths):
        codes = ScopedCodes.from_defaults()
        registers = ScopedRegisters.from_defaults()
        scoped_font_state = ScopedFontState.from_defaults()
        router = ScopedRouter.from_defaults()
        parameters = ScopedParameters.from_defaults()
        return cls(font_search_paths,
                   codes, registers, scoped_font_state, router, parameters)

    # Mode.

    @property
    def mode(self):
        return self.modes[-1][0]

    @property
    def _layout_list(self):
        return self.modes[-1][1]

    def push_mode(self, mode):
        self.modes.append((mode, []))

    def pop_mode(self):
        mode, layout_list = self.modes.pop()
        return layout_list

    def append_to_list(self, item):
        self._layout_list.append(item)

    # Group.

    @property
    def group(self):
        return self.groups[-1]

    def push_group(self, group):
        self.groups.append(group)

    def pop_group(self):
        return self.groups.pop()

    # Affects both global and scoped state: fonts are stored in the global
    # state, but the current font and control sequences to access them are
    # scoped.

    def define_new_font(self, is_global, name, file_name, at_clause):
        new_font_id = self.global_font_state.define_new_font(file_name, at_clause)
        self.router.define_new_font_control_sequence(is_global, name, new_font_id)
        return new_font_id

    @property
    def current_font(self):
        current_font_id = self.scoped_font_state.current_font_id
        return self.global_font_state.fonts[current_font_id]

    # Scope

    @property
    def _scoped_accessors(self):
        return [self.codes, self.registers, self.scoped_font_state,
                self.router, self.parameters]

    def push_new_scope(self):
        for acc in self._scoped_accessors:
            acc.push_new_scope()

    def pop_scope(self):
        for acc in self._scoped_accessors:
            acc.pop_scope()
