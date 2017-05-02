from collections import Counter

from ..constants.primitive_control_sequences import (terminal_instructions,
                                                     if_instructions)


def instructions_to_types(instructions):
    return tuple(i.value for i in instructions)


# TODO: Move some tokens to only be in command parser
terminal_types = instructions_to_types(terminal_instructions)


duplicates = [typ for typ, cnt in Counter(terminal_types).items() if cnt > 1]
if duplicates:
    raise ValueError(f'Terminal types contains duplicates: {duplicates}')

cond_terminal_instructions = if_instructions
cond_terminal_types = instructions_to_types(cond_terminal_instructions)
