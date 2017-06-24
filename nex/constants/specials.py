"""
Define the list of internal 'special' variables that TeX requires to run. TeX
uses these to keep track of what's going on, such as the height of the current
page so far. These may vary while TeX runs, as opposed to the more static
'Parameters'. However, they are similar in many ways.
They have two types: integers, and dimensions (physical lengths).
"""
from enum import Enum

from .instructions import Instructions
from ..tokens import instructions_to_types


class Specials(Enum):
    space_factor = 'SPACE_FACTOR'
    # The number of lines in the paragraph most recently completed or partially
    # completed.
    prev_graf = 'PREV_GRAF'
    # The number of times \output was called since the last \shipout.
    dead_cycles = 'DEAD_CYCLES'
    # Means different things:
    # 1. In the ouput routine, the total number of held-over insertions. For
    #    each class of insertions this includes the unused part of a split
    #    insertion and all other insertions which don't appear on the current
    #    page.
    # 2. In the page-making routine, the total of the \floatingpenalty for each
    #    unsplit insertion which is carried over to the next page.
    insert_penalties = 'INSERT_PENALTIES'

    # The depth of the last box added to the current vertical list.
    prev_depth = 'PREV_DEPTH'
    # The actual depth of the last box on the main page.
    page_depth = 'PAGE_DEPTH'
    # The desired height of the current page.
    page_goal = 'PAGE_GOAL'
    # The accumulated height of the current page.
    page_total = 'PAGE_TOTAL'
    # The amount of finite stretchability in the current page.
    page_stretch = 'PAGE_STRETCH'
    # The amount of first-order infinite stretchability in the current page.
    page_fil_stretch = 'PAGE_FIL_STRETCH'
    # The amount of second-order infinite stretchability in the current page.
    page_fill_stretch = 'PAGE_FILL_STRETCH'
    # The amount of third-order infinite stretchability in the current page.
    page_filll_stretch = 'PAGE_FILLL_STRETCH'
    # The amount of finite shrinkability in the current page.
    page_shrink = 'PAGE_SHRINK'


special_to_instr = {
    Specials.space_factor: Instructions.special_integer,
    # The number of lines in the paragraph most recently completed or partially
    # completed.
    Specials.prev_graf: Instructions.special_integer,
    # The number of times \output was called since the last \shipout.
    Specials.dead_cycles: Instructions.special_integer,
    # Means different things:
    # 1. In the ouput routine, the total number of held-over insertions. For
    #    each class of insertions this includes the unused part of a split
    #    insertion and all other insertions which don't appear on the current
    #    page.
    # 2. In the page-making routine, the total of the \floatingpenalty for each
    #    unsplit insertion which is carried over to the next page.
    Specials.insert_penalties: Instructions.special_integer,

    # The depth of the last box added to the current vertical list.
    Specials.prev_depth: Instructions.special_dimen,
    # The actual depth of the last box on the main page.
    Specials.page_depth: Instructions.special_dimen,
    # The desired height of the current page.
    Specials.page_goal: Instructions.special_dimen,
    # The accumulated height of the current page.
    Specials.page_total: Instructions.special_dimen,
    # The amount of finite stretchability in the current page.
    Specials.page_stretch: Instructions.special_dimen,
    # The amount of first-order infinite stretchability in the current page.
    Specials.page_fil_stretch: Instructions.special_dimen,
    # The amount of second-order infinite stretchability in the current page.
    Specials.page_fill_stretch: Instructions.special_dimen,
    # The amount of third-order infinite stretchability in the current page.
    Specials.page_filll_stretch: Instructions.special_dimen,
    # The amount of finite shrinkability in the current page.
    Specials.page_shrink: Instructions.special_dimen,
}
special_to_type = {p: instr.value for p, instr in special_to_instr.items()}

special_instrs = (
    Instructions.special_integer,
    Instructions.special_dimen,
)
special_instr_types = instructions_to_types(special_instrs)


def is_special_type(type_):
    return type_ in special_instr_types
