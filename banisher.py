import logging
from collections import deque
from enum import Enum

from common import Token, TerminalToken
from lexer import CatCode
from typer import char_cat_pair_to_terminal_token
from expander import short_hand_def_map

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

special_control_sequence_types = (
    'BALANCED_TEXT',
    'PARAMETER_TEXT',
)
unexpanded_cs_type = 'UNEXPANDED_CONTROL_SEQUENCE'
unexpanded_one_char_cs_type = 'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE'
special_control_sequence_types += (
    unexpanded_cs_type,
    unexpanded_one_char_cs_type,
)

read_control_sequence_name_types = (
    'DEF',
    'LET',
    'BACKTICK',
)
read_control_sequence_name_types += tuple(set(short_hand_def_map.values()))


class ContextMode(Enum):
    normal = 1
    awaiting_balanced_text_start = 2
    awaiting_unexpanded_cs = 3
    absorbing_parameter_text = 4


expanding_modes = (
    ContextMode.normal,
    ContextMode.awaiting_balanced_text_start
)


class Banisher(object):

    def __init__(self, lexer, expander):
        self.lexer = lexer
        self.expander = expander
        # Input buffer.
        self.input_tokens_stack = deque()
        # Output buffer.
        self.output_terminal_tokens_stack = deque()
        self.context_mode = ContextMode.normal

    @property
    def _next_lex_token(self):
        return self.lexer.next_token

    @property
    def expanding_control_sequences(self):
        return self.context_mode in expanding_modes

    @property
    def next_token(self):
        while not self.output_terminal_tokens_stack:
            self.populate_output_stack()
        logger.debug(self.output_terminal_tokens_stack)
        next_token = self.output_terminal_tokens_stack.popleft()
        return next_token

    def populate_input_stack(self):
        fresh_lex_token = self._next_lex_token
        self.input_tokens_stack.append(fresh_lex_token)

    def pop_next_input_token(self):
        if not self.input_tokens_stack:
            self.populate_input_stack()
        return self.input_tokens_stack.popleft()

    def get_unexpanded_cs_terminal_token(self):
        token = self.pop_next_input_token()
        if token.type == 'CONTROL_SEQUENCE':
            next_token_name = token.value
            type_ = (unexpanded_one_char_cs_type if len(next_token_name) == 1
                     else unexpanded_cs_type)
            terminal_token = TerminalToken(type_=type_, value=token)
            return terminal_token
        elif token.type == 'CHAR_CAT_PAIR':
            terminal_token = char_cat_pair_to_terminal_token(token)
        else:
            import pdb; pdb.set_trace()
        return terminal_token

    def get_balanced_text_token(self):
        lex_tokens = []
        brace_level = 1
        while True:
            lex_token = self.pop_next_input_token()
            lex_tokens.append(lex_token)
            if lex_token.type == 'CHAR_CAT_PAIR':
                cat = lex_token.value['cat']
                if cat == CatCode.begin_group:
                    brace_level += 1
                elif cat == CatCode.end_group:
                    brace_level -= 1
                if brace_level == 0:
                    break
        # Put the ending right brace token back on the input stack.
        self.input_tokens_stack.appendleft(lex_tokens[-1])
        balanced_text = TerminalToken(type_='BALANCED_TEXT',
                                      value=lex_tokens[:-1])
        return balanced_text

    def populate_output_stack(self):
        # To reduce my own confusion:
        # a primitive token is one that is not a lex token. But it might not be
        # a terminal token either, if it needs combining with other tokens
        # to make a terminal token. For instance, a primitive token might be a
        # \def that needs combining with the rest of its bits to make a
        # DEFINITION terminal token.
        # But I might blur the line between these two sometimes.

        # A terminal token is simply a token that is accepted by the parser.

        # Might be a lex token, a primitive token or a terminal token.
        first_token = self.pop_next_input_token()
        type_ = first_token.type

        # If we get a lex token, we need to make it a terminal token, and run again.
        if not isinstance(first_token, TerminalToken):
            # If we have a char-cat pair, we must type it to its terminal version,
            if type_ == 'CHAR_CAT_PAIR':
                terminal_token = char_cat_pair_to_terminal_token(first_token)
                self.input_tokens_stack.appendleft(terminal_token)
            elif type_ == 'CONTROL_SEQUENCE':
                name = first_token.value
                if self.expanding_control_sequences:
                    # Replace it with its contents and go again. This might be
                    # expanding a user control sequence, or just mapping a lex
                    # token to its primitive token equivalent.
                    expanded_first_token = self.expander.expand_to_token_list(name)
                    self.input_tokens_stack.extendleft(expanded_first_token[::-1])
                else:
                    # Convert to a primitive unexpanded control sequence.
                    terminal_token = TerminalToken(type_=unexpanded_cs_type,
                                                   value=first_token)
                    self.input_tokens_stack.appendleft(terminal_token)
            else:
                import pdb; pdb.set_trace()
            # Now run again, hopefully now seeing a primitive token.
            # (Might not, if the expansion needs more expansion, but the
            # ultimate escape route is to see a primitive token.)
        # We might be able to make some terminal token output, hooray.
        else:
            # Complicated syntactic token that might affect lexing.
            if (self.context_mode == ContextMode.awaiting_balanced_text_start and
                    type_ == 'LEFT_BRACE'):
                # Put the LEFT_BRACE on the output stack.
                self.output_terminal_tokens_stack.append(first_token)
                # Now merge all lex tokens until right brace lex token seen,
                # into a 'BALANCED_TEXT' terminal token, which we put on the
                # input stack to read later. We also put the right brace
                # back on the stack to read later.
                balanced_text_token = self.get_balanced_text_token()
                # Put it on the input stack to be read again.
                self.input_tokens_stack.appendleft(balanced_text_token)
                self.context_mode = ContextMode.normal
            elif self.context_mode == ContextMode.absorbing_parameter_text:
                if type_ == 'LEFT_BRACE':
                    parameter_text_token = TerminalToken(type_='PARAMETER_TEXT',
                                                         value=self.parameter_text_tokens)
                    self.output_terminal_tokens_stack.append(parameter_text_token)
                    # Put the LEFT_BRACE back on the input stack.
                    self.input_tokens_stack.appendleft(first_token)
                    self.context_mode = ContextMode.awaiting_balanced_text_start
                else:
                    self.parameter_text_tokens.append(first_token)
            elif (self.context_mode == ContextMode.awaiting_unexpanded_cs and
                  type_ == unexpanded_cs_type):
                # Put the unexpanded control sequence on the output stack.
                self.output_terminal_tokens_stack.append(first_token)
                # Now go back to ordinary mode.
                self.context_mode = ContextMode.normal
            elif type_ in read_control_sequence_name_types:
                # Get an unexpanded control sequence token and add it to the
                # output stack, along with the first token.
                next_token = self.get_unexpanded_cs_terminal_token()
                self.output_terminal_tokens_stack.append(first_token)
                self.output_terminal_tokens_stack.append(next_token)
                if type_ == 'DEF':
                    self.context_mode = ContextMode.absorbing_parameter_text
                    self.parameter_text_tokens = []
                elif type_ == 'LET':
                    self.context_mode = ContextMode.awaiting_unexpanded_cs
            elif type_ == 'MESSAGE':
                self.output_terminal_tokens_stack.append(first_token)
                self.context_mode = ContextMode.awaiting_balanced_text_start
            # Just some semantic bullshit, stick it on the output stack
            # for the interpreter to deal with.
            else:
                self.output_terminal_tokens_stack.append(first_token)
