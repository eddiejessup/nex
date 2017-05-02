from string import ascii_letters
from collections import deque

from .tokens import InstructionToken
from .lexer import (make_char_cat_lex_token,
                    control_sequence_lex_type, char_cat_lex_type)
from .constants.primitive_control_sequences import Instructions
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
    token = InstructionToken.from_instruction(
        instruction,
        value=value,
        position_like=char_cat_lex_token
    )
    return token


def make_control_sequence_instruction_token(name, position_like=None):
    if len(name) == 1:
        instruction = Instructions.unexpanded_one_char_control_sequence
    else:
        instruction = Instructions.unexpanded_many_char_control_sequence
    return InstructionToken.from_instruction(
        instruction,
        value={'name': name, 'lex_type': control_sequence_lex_type},
        position_like=position_like
    )


def make_instruction_token_from_char_cat(char, cat, *pos_args, **pos_kwargs):
    """Utility function to make a terminal char-cat token straight from a pair.
    """
    lex_token = make_char_cat_lex_token(char, cat, *pos_args, **pos_kwargs)
    token = make_char_cat_pair_instruction_token(lex_token)
    return token


def lex_token_to_instruction_token(lex_token):
    # If we have a char-cat pair, we must type it to its terminal version,
    if lex_token.type == char_cat_lex_type:
        return make_char_cat_pair_instruction_token(lex_token)
    elif lex_token.type == control_sequence_lex_type:
        name = lex_token.value
        return make_control_sequence_instruction_token(
            name, position_like=lex_token)
    # Aren't any other types of lexed tokens.
    else:
        raise Exception


class TyperPipe:

    def __init__(self, lexer):
        self.lexer = lexer
        self.input_tokens_queue = deque()
        self.output_tokens_queue = deque()

    def pop_next_output_token(self):
        while not self.output_tokens_queue:
            new_output_tokens = self._get_new_output_tokens()
            self.output_tokens_queue.extend(new_output_tokens)
        return self.output_tokens_queue.popleft()

    def _pop_next_input_token(self):
        if not self.input_tokens_queue:
            self.input_tokens_queue.append(self.lexer.get_next_token())
        return self.input_tokens_queue.popleft()

    def _get_new_output_tokens(self):
        first_lex_token = self._pop_next_input_token()
        instruction_token = lex_token_to_instruction_token(first_lex_token)
        return [instruction_token]