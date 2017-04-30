from collections import deque

from .common import UnexpandedToken, TerminalToken
from .lexer import (make_char_cat_lex_token,
                    control_sequence_lex_type, char_cat_lex_type)
from .codes import CatCode
from .constants.literals import (non_active_literals_map,
                                 other_literal_type,
                                 category_map,
                                 literals_map)
from .constants.strange_types import (unexpanded_one_char_cs_type,
                                      unexpanded_many_char_cs_type)


def get_char_cat_pair_terminal_type(char_cat_pair_token):
    v = char_cat_pair_token.value
    char, cat = v['char'], v['cat']
    if cat in (CatCode.letter, CatCode.other) and (char, cat) in literals_map:
        terminal_token_type = literals_map[(char, cat)]
    elif cat != CatCode.active and char in non_active_literals_map:
        terminal_token_type = non_active_literals_map[char]
    elif cat in (CatCode.letter, CatCode.other):
        terminal_token_type = other_literal_type
    elif cat in category_map:
        terminal_token_type = category_map[cat]
    else:
        import pdb; pdb.set_trace()
    return terminal_token_type


def make_char_cat_pair_terminal_token(char_cat_pair_token):
    terminal_token_type = get_char_cat_pair_terminal_type(char_cat_pair_token)
    value = char_cat_pair_token.value
    value['lex_type'] = char_cat_pair_token.type
    token = TerminalToken(type_=terminal_token_type, value=value,
                          position_like=char_cat_pair_token)
    return token


def make_control_sequence_unexpanded_token(name, position_like=None):
    if len(name) == 1:
        type_ = unexpanded_one_char_cs_type
    else:
        type_ = unexpanded_many_char_cs_type
    return TerminalToken(type_=type_,
                         value={'name': name,
                                'lex_type': control_sequence_lex_type},
                         position_like=position_like)


def make_char_cat_terminal_token(char, cat, *pos_args, **pos_kwargs):
    """Utility function to make a terminal char-cat token straight from a pair.
    """
    lex_token = make_char_cat_lex_token(char, cat, *pos_args, **pos_kwargs)
    terminal_token = make_char_cat_pair_terminal_token(lex_token)
    return terminal_token


def lex_token_to_unexpanded_token(lex_token):
    # If we have a char-cat pair, we must type it to its terminal version,
    if lex_token.type == char_cat_lex_type:
        return make_char_cat_pair_terminal_token(lex_token)
    elif lex_token.type == control_sequence_lex_type:
        name = lex_token.value
        return make_control_sequence_unexpanded_token(
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
        first_input_token = self._pop_next_input_token()
        unexpanded_token = lex_token_to_unexpanded_token(first_input_token)
        return deque([unexpanded_token])
