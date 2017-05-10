from .lexer import char_cat_lex_type
from .instructions import (Instructions,
                           unexpanded_cs_instructions)
from .tokens import InstructionToken
from .router import short_hand_def_type_to_token_instr


n = 9
k = 2 * n
lim = (k - 1) // 2


def truncate_list(ts):
    if len(ts) > k:
        return ts[:lim] + ['…'] + ts[-lim:]
    else:
        return ts


def stringify_instrs(ts):
    ts = truncate_list(ts)
    in_chars = False
    b = ''
    for t in ts:
        if isinstance(t, InstructionToken) and isinstance(t.value, dict) and 'lex_type' in t.value and t.value['lex_type'] == char_cat_lex_type:
            if in_chars:
                b += t.value['char']
            else:
                b = t.value['char']
                in_chars = True
        else:
            if in_chars:
                yield b
                in_chars = False

            if isinstance(t, InstructionToken) and t.instruction in unexpanded_cs_instructions:
                yield f"\\{t.value['name']}"
            elif isinstance(t, InstructionToken) and t.instruction == Instructions.param_number:
                yield f'#{t.value}'
            elif isinstance(t, InstructionToken) and t.instruction in short_hand_def_type_to_token_instr.values():
                yield f'{t.value}'
            elif isinstance(t, InstructionToken):
                yield f'I.{t.instruction.name}'
            else:
                yield t
    if in_chars:
        yield b


def stringify_instr_list(ts):
    return ' '.join(stringify_instrs(ts))
