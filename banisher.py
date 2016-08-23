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
unexpanded_cs_types = (unexpanded_cs_type, unexpanded_one_char_cs_type)

undelim_param_type = 'UNDELIMITED_PARAM'
delim_param_type = 'DELIMITED_PARAM'
param_types = (undelim_param_type, delim_param_type)

special_control_sequence_types += unexpanded_cs_types

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
    reading_macro_arguments = 5


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
        # If we have a char-cat pair, we must type it to its terminal version,
        if fresh_lex_token.type == 'CHAR_CAT_PAIR':
            terminal_token = char_cat_pair_to_terminal_token(fresh_lex_token)
        elif fresh_lex_token.type == 'CONTROL_SEQUENCE':
            name = fresh_lex_token.value
            type_ = (unexpanded_one_char_cs_type if len(name) == 1
                     else unexpanded_cs_type)
            # Convert to a primitive unexpanded control sequence.
            terminal_token = TerminalToken(type_=type_, value=fresh_lex_token)
        else:
            import pdb; pdb.set_trace()
        self.input_tokens_stack.append(terminal_token)

    def pop_next_input_token(self):
        if not self.input_tokens_stack:
            self.populate_input_stack()
        return self.input_tokens_stack.popleft()

    def get_balanced_text_token(self):
        tokens = []
        brace_level = 1
        while True:
            token = self.pop_next_input_token()
            tokens.append(token)
            if token.type == 'LEFT_BRACE':
                brace_level += 1
            elif token.type == 'RIGHT_BRACE':
                brace_level -= 1
            if brace_level == 0:
                break
        # Put the ending right brace token back on the input stack.
        self.input_tokens_stack.appendleft(tokens[-1])
        balanced_text = TerminalToken(type_='BALANCED_TEXT', value=tokens[:-1])
        return balanced_text

    def check_macro_argument_text(self):
        if len(self.argument_text) == get_nr_params(self.param_text):
            # Now run again, hopefully now seeing a primitive token.
            # (Might not, if the expansion needs more expansion, but the
            # ultimate escape route is to see a primitive token.)
            expanded_first_token = self.expander.expand_to_token_list(self.macro_name, self.argument_text)
            self.input_tokens_stack.extendleft(expanded_first_token[::-1])
            self.context_mode = ContextMode.normal

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
        if self.context_mode == ContextMode.reading_macro_arguments:
            self.argument_text.append(first_token)
            self.check_macro_argument_text()
        # If we get a control sequence token, we need to either start expanding
        # it, or add it as an un-expanded token, depending on the context.
        elif self.expanding_control_sequences and type_ in unexpanded_cs_types:
            name = first_token.value.value
            self.context_mode = ContextMode.reading_macro_arguments
            self.macro_name = name
            self.param_text = self.expander.expand_to_parameter_text(name)
            self.argument_text = []
            self.check_macro_argument_text()
        elif (self.context_mode == ContextMode.awaiting_balanced_text_start and
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
                parameter_text_template = parse_parameter_text(self.parameter_text_tokens)
                parameter_text_token = TerminalToken(type_='PARAMETER_TEXT',
                                                     value=parameter_text_template)
                self.output_terminal_tokens_stack.append(parameter_text_token)
                # Put the LEFT_BRACE back on the input stack.
                self.input_tokens_stack.appendleft(first_token)
                self.context_mode = ContextMode.awaiting_balanced_text_start
            else:
                self.parameter_text_tokens.append(first_token)
        elif (self.context_mode == ContextMode.awaiting_unexpanded_cs and
              type_ in unexpanded_cs_types):
            # Put the unexpanded control sequence on the output stack.
            self.output_terminal_tokens_stack.append(first_token)
            # Now go back to ordinary mode.
            self.context_mode = ContextMode.normal
        elif type_ in read_control_sequence_name_types:
            # Get an unexpanded control sequence token and add it to the
            # output stack, along with the first token.
            next_token = self.pop_next_input_token()
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


def parse_parameter_text(tokens):
    p_nr = 1
    i = 0
    tokens_processed = []
    while i < len(tokens) - 1:
        t = tokens[i]
        if t.type == 'PARAMETER':
            i += 1
            t_next = tokens[i]
            if int(t_next.value.value['char']) != p_nr:
                raise ValueError
            # How does TeX determine where an argument stops, you ask. Answer:
            # There are two cases.
            # An undelimited parameter is followed immediately in the parameter
            # text by a parameter token, or it occurs at the very end of the
            # parameter text; [...]
            if i == len(tokens) - 1:
                type_ = undelim_param_type
            else:
                t_after = tokens[i + 1]
                if t_after.type == 'PARAMETER':
                    type_ = undelim_param_type
                # A delimited parameter is followed in the parameter text by
                # one or more non-parameter tokens [...]
                else:
                    type_ = delim_param_type
            t = Token(type_=type_, value=p_nr)
            p_nr += 1
        tokens_processed.append(t)
        i += 1
    return tokens_processed


def parse_replacement_text(tokens):
    i = 0
    tokens_processed = []
    while i < len(tokens) - 1:
        t = tokens[i]
        if t.type == 'PARAMETER':
            i += 1
            t_next = tokens[i]
            # [...] each # must be followed by a digit that appeared after # in
            # the parameter text, or else the # should be followed by another
            # #.
            if t_next.type == 'PARAMETER':
                raise NotImplementedError
            else:
                p_nr = int(t_next.value.value['char'])
                t = Token(type_='PARAM_NUMBER', value=p_nr)
        tokens_processed.append(t)
        i += 1
    return tokens_processed


def get_nr_params(param_text):
    return sum(t.type in param_types for t in param_text)
