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

specials = {
    'SPACE_FACTOR': Instructions.special_integer,
    # The number of lines in the paragraph most recently completed or partially
    # completed.
    'PREV_GRAF': Instructions.special_integer,
    # The number of times \output was called since the last \shipout.
    'DEAD_CYCLES': Instructions.special_integer,
    # Means different things:
    # 1. In the ouput routine, the total number of held-over insertions. For
    #    each class of insertions this includes the unused part of a split
    #    insertion and all other insertions which don't appear on the current
    #    page.
    # 2. In the page-making routine, the total of the \floatingpenalty for each
    #    unsplit insertion which is carried over to the next page.
    'INSERT_PENALTIES': Instructions.special_integer,

    # The depth of the last box added to the current vertical list.
    'PREV_DEPTH': Instructions.special_dimen,
    # The actual depth of the last box on the main page.
    'PAGE_DEPTH': Instructions.special_dimen,
    # The desired height of the current page.
    'PAGE_GOAL': Instructions.special_dimen,
    # The accumulated height of the current page.
    'PAGE_TOTAL': Instructions.special_dimen,
    # The amount of finite stretchability in the current page.
    'PAGE_STRETCH': Instructions.special_dimen,
    # The amount of first-order infinite stretchability in the current page.
    'PAGE_FIL_STRETCH': Instructions.special_dimen,
    # The amount of second-order infinite stretchability in the current page.
    'PAGE_FILL_STRETCH': Instructions.special_dimen,
    # The amount of third-order infinite stretchability in the current page.
    'PAGE_FILLL_STRETCH': Instructions.special_dimen,
    # The amount of finite shrinkability in the current page.
    'PAGE_SHRINK': Instructions.special_dimen,
}
Specials = Enum('Specials', {s.lower(): s for s in specials})
special_to_instr = {p: specials[p.value] for p in Specials}
special_to_type = {p: instr.value for p, instr in special_to_instr.items()}

special_instrs = (
    Instructions.special_integer,
    Instructions.special_dimen,
)
special_instr_types = instructions_to_types(special_instrs)


def is_special_type(type_):
    return type_ in special_instr_types
