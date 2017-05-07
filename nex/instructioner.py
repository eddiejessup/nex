from string import ascii_letters
from collections import deque

from .tokens import InstructionToken
from .lexer import (Lexer, make_char_cat_lex_token,
                    control_sequence_lex_type, char_cat_lex_type)
from .instructions import Instructions
from .tex_parameters import param_to_instr
from .codes import CatCode


literals_map = {
    ('<', CatCode.other): Instructions.less_than,
    ('>', CatCode.other): Instructions.greater_than,

    ('=', CatCode.other): Instructions.equals,
    ('+', CatCode.other): Instructions.plus_sign,
    ('-', CatCode.other): Instructions.minus_sign,

    ('0', CatCode.other): Instructions.zero,
    ('1', CatCode.other): Instructions.one,
    ('2', CatCode.other): Instructions.two,
    ('3', CatCode.other): Instructions.three,
    ('4', CatCode.other): Instructions.four,
    ('5', CatCode.other): Instructions.five,
    ('6', CatCode.other): Instructions.six,
    ('7', CatCode.other): Instructions.seven,
    ('8', CatCode.other): Instructions.eight,
    ('9', CatCode.other): Instructions.nine,

    ('\'', CatCode.other): Instructions.single_quote,
    ('"', CatCode.other): Instructions.double_quote,
    ('`', CatCode.other): Instructions.backtick,

    ('.', CatCode.other): Instructions.point,
    (',', CatCode.other): Instructions.comma,

    ('A', CatCode.other): Instructions.a,
    ('B', CatCode.other): Instructions.b,
    ('C', CatCode.other): Instructions.c,
    ('D', CatCode.other): Instructions.d,
    ('E', CatCode.other): Instructions.e,
    ('F', CatCode.other): Instructions.f,
    ('A', CatCode.letter): Instructions.a,
    ('B', CatCode.letter): Instructions.b,
    ('C', CatCode.letter): Instructions.c,
    ('D', CatCode.letter): Instructions.d,
    ('E', CatCode.letter): Instructions.e,
    ('F', CatCode.letter): Instructions.f,
}

non_active_letters_map = {c: Instructions['non_active_uncased_{}'.format(c.lower())]
                          for c in ascii_letters}

category_map = {
    CatCode.space: Instructions.space,
    CatCode.begin_group: Instructions.left_brace,
    CatCode.end_group: Instructions.right_brace,
    CatCode.active: Instructions.active_character,
    CatCode.parameter: Instructions.parameter,
    CatCode.math_shift: Instructions.math_shift,
    CatCode.align_tab: Instructions.align_tab,
    CatCode.superscript: Instructions.superscript,
    CatCode.subscript: Instructions.subscript,
}


def get_char_cat_pair_instruction(char, cat):
    if cat in (CatCode.letter, CatCode.other) and (char, cat) in literals_map:
        return literals_map[(char, cat)]
    elif cat != CatCode.active and char in non_active_letters_map:
        return non_active_letters_map[char]
    elif cat in (CatCode.letter, CatCode.other):
        return Instructions.misc_char_cat_pair
    elif cat in category_map:
        return category_map[cat]
    else:
        import pdb; pdb.set_trace()


def make_char_cat_pair_instruction_token(char_cat_lex_token):
    v = char_cat_lex_token.value
    char, cat = v['char'], v['cat']
    instruction = get_char_cat_pair_instruction(char, cat)
    value = char_cat_lex_token.value
    value['lex_type'] = char_cat_lex_token.type
    token = InstructionToken(
        instruction,
        value=value,
        position_like=char_cat_lex_token
    )
    return token


def make_parameter_control_sequence_instruction(name, parameter):
    instr = param_to_instr[parameter]
    instr_tok = make_primitive_control_sequence_instruction(name, instr)
    # This is what is used to look up the parameter value. The  'name' just
    # records the name of the control sequence used to refer to this parameter.
    instr_tok.value['parameter'] = parameter
    return instr_tok


def make_primitive_control_sequence_instruction(name, instruction):
    return InstructionToken(
        instruction,
        value={'name': name, 'lex_type': control_sequence_lex_type},
        line_nr='abstract'
    )


def make_unexpanded_control_sequence_instruction(name, position_like=None):
    if len(name) == 1:
        instruction = Instructions.unexpanded_one_char_control_sequence
    else:
        instruction = Instructions.unexpanded_many_char_control_sequence
    return InstructionToken(
        instruction,
        value={'name': name, 'lex_type': control_sequence_lex_type},
        position_like=position_like
    )


def char_cat_instr_tok(char, cat, *pos_args, **pos_kwargs):
    """Utility function to make a terminal char-cat token straight from a pair.
    """
    lex_token = make_char_cat_lex_token(char, cat, *pos_args, **pos_kwargs)
    return make_char_cat_pair_instruction_token(lex_token)


def lex_token_to_instruction_token(lex_token):
    # If we have a char-cat pair, we must type it to its terminal version,
    if lex_token.type == char_cat_lex_type:
        return make_char_cat_pair_instruction_token(lex_token)
    elif lex_token.type == control_sequence_lex_type:
        return make_unexpanded_control_sequence_instruction(
            lex_token.value, position_like=lex_token)
    # Aren't any other types of lexed tokens.
    else:
        raise Exception


class Instructioner:

    def __init__(self, lexer):
        self.lexer = lexer
        # Input buffer.
        # TODO: Use GetBuffer.
        self.input_tokens_queue = deque()

    @classmethod
    def from_string(cls, *args, **kwargs):
        lexer = Lexer.from_string(*args, **kwargs)
        return cls(lexer)

    def __iter__(self):
        return self

    def __next__(self):
        if self.input_tokens_queue:
            t = self.input_tokens_queue.popleft()
        else:
            new_lex_token = next(self.lexer)
            t = lex_token_to_instruction_token(new_lex_token)
        if t.char_nr is not None:
            print(t.get_position_str(self.lexer.reader))
        return t

    def advance_to_end(self):
        yield from self.lexer.advance_to_end()

    def replace_tokens_on_input(self, tokens):
        self.input_tokens_queue.extendleft(reversed(tokens))
