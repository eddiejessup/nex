import logging
from collections import deque
from enum import Enum

from rply.errors import ParsingError

from common import Token, TerminalToken, InternalToken
from utils import increasing_window
from lexer import make_char_cat_token, make_control_sequence_token, CatCode
from typer import (lex_token_to_unexpanded_terminal_token,
                   unexpanded_cs_types, unexpanded_cs_type,
                   unexpanded_one_char_cs_type)
from expander import short_hand_def_map, get_nr_params, parse_parameter_text, if_map
from condition_parser import condition_parser

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

read_unexpanded_control_sequence_types = (
    'DEF',
    'LET',
    'BACKTICK',
)
read_unexpanded_control_sequence_types += tuple(set(short_hand_def_map.values()))

if_types = if_map.values()
message_types = ('MESSAGE', 'ERROR_MESSAGE', 'WRITE')


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


def make_char_cat_term_token(char, cat):
    char_lex_token = make_char_cat_token(char, cat)
    char_term_token = lex_token_to_unexpanded_terminal_token(char_lex_token)
    return char_term_token


class Banisher(object):

    def __init__(self, lexer, expander):
        self.lexer = lexer
        self.expander = expander
        # Input buffer.
        self.input_tokens_stack = deque()
        # Output buffer.
        self.output_terminal_tokens_stack = deque()
        self.context_mode_stack = []

        self._secret_terminal_list = []

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
        self._secret_terminal_list.append(next_token)
        # for t in self._secret_terminal_list[-20:]:
        #     print(t)
        return next_token

    def populate_input_stack(self):
        new_lex_token = self._next_lex_token
        terminal_token = lex_token_to_unexpanded_terminal_token(new_lex_token)
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
            self.pop_context()

    def push_context(self, mode):
        self.context_mode_stack.append(mode)

    def pop_context(self):
        if self.context_mode_stack:
            return self.context_mode_stack.pop()
        else:
            return self.context_mode_stack

    @property
    def context_mode(self):
        if self.context_mode_stack:
            return self.context_mode_stack[-1]
        else:
            return ContextMode.normal

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
        # print(first_token)
        # print(self.context_mode_stack)
        # print()
        if self.context_mode == ContextMode.reading_macro_arguments:
            self.argument_text.append(first_token)
            self.check_macro_argument_text()
        # If we get a control sequence token, we need to either start expanding
        # it, or add it as an un-expanded token, depending on the context.
        elif self.expanding_control_sequences and type_ in unexpanded_cs_types:
            name = first_token.value
            self.push_context(ContextMode.reading_macro_arguments)
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
            # Done with getting balanced text.
            self.pop_context()
        elif self.context_mode == ContextMode.absorbing_parameter_text:
            if type_ == 'LEFT_BRACE':
                parameter_text_template = parse_parameter_text(self.parameter_text_tokens)
                parameter_text_token = TerminalToken(type_='PARAMETER_TEXT',
                                                     value=parameter_text_template)
                self.output_terminal_tokens_stack.append(parameter_text_token)
                # Put the LEFT_BRACE back on the input stack.
                self.input_tokens_stack.appendleft(first_token)
                # Done absorbing parameter text.
                self.pop_context()
                # Now get the replacement text.
                self.push_context(ContextMode.awaiting_balanced_text_start)
            else:
                self.parameter_text_tokens.append(first_token)
        elif (self.context_mode == ContextMode.awaiting_unexpanded_cs and
              type_ in unexpanded_cs_types):
            # Put the unexpanded control sequence on the output stack.
            self.output_terminal_tokens_stack.append(first_token)
            # Done with getting an un-expanded control sequence.
            self.pop_context()
        elif type_ in read_unexpanded_control_sequence_types:
            # Get an unexpanded control sequence token and add it to the
            # output stack, along with the first token.
            next_token = self.pop_next_input_token()
            self.output_terminal_tokens_stack.append(first_token)
            self.output_terminal_tokens_stack.append(next_token)
            if type_ == 'DEF':
                self.push_context(ContextMode.absorbing_parameter_text)
                self.parameter_text_tokens = []
            elif type_ == 'LET':
                self.push_context(ContextMode.awaiting_unexpanded_cs)
        elif type_ in message_types:
            self.output_terminal_tokens_stack.append(first_token)
            self.push_context(ContextMode.awaiting_balanced_text_start)
        elif type_ in if_types:
            # We will be messing with the output stack lots, so just
            # save anything current, empty the stack, and restore it at the
            # end.
            saved_output_stack = self.output_terminal_tokens_stack.copy()
            self.output_terminal_tokens_stack = deque([first_token])
            # Get enough tokens to evaluate condition. Populating might add
            # more tokens than are needed to evaluate the condition, so we need
            # to add output tokens, then find the longest input sequence that
            # will parse, and drop that input sequence from the stack, as we
            # only need it for the condition.
            # We know to stop adding tokens when we see a switch from not
            # parsing, to parsing, to not parsing again.
            while True:
                # TODO: isn't this thing actually a queue, not a stack?
                # (Entails lots of renaming.)
                # While populating this, maybe we will see an if_type in the
                # condition. Haven't tested, but it seems like this should
                # recurse correctly.
                self.populate_output_stack()
                have_parsed = False
                input_string = list(self.output_terminal_tokens_stack)
                inputs_partial = increasing_window(input_string)
                for i_max, input_partial in enumerate(inputs_partial):
                    try:
                        is_true = condition_parser.parse(iter(input_partial), state='hihi')
                    except (ParsingError, StopIteration):
                        if have_parsed:
                            break
                    else:
                        have_parsed = True
                # If we try all parse strings, and either never can parse, or
                # do not switch back to an invalid parse, then run again with
                # more tokens.
                else:
                    continue
                # If we have broken from the loop, we have got the no-parse to
                # parse to no-parse behaviour we want, and we can use 'i'
                # to get the longest-parsing string.
                break
            # Get rid of the condition tokens, as we are done with them,
            # and the (main) parser will be confused by them.
            # Minus 1 because we find the first string *not* to parse, meaning
            # we have some extra fluff.
            for i in range(i_max - 1):
                self.output_terminal_tokens_stack.popleft()

            # Now get the body of the condition text.
            # TeXbook:
            # "Expansion is suppressed at the following times:
            # [...]
            # When tokens are being skipped because conditional text is
            # being ignored."
            # From testing, the above does not seem to hold, so I am going
            # to carry on expansion.
            while True:
                nr_conditions = 1
                # This is very wasteful, because we check the same tokens
                # over and over, but it saves us worrying about stuff that
                # is already on the input stack from before.
                i_else = None
                # for i, t in enumerate(self.input_tokens_stack):
                for i, t in enumerate(self.output_terminal_tokens_stack):
                    print(t)
                    # Because we are not expanding, I guess we must do this?
                    # Seems messy.
                    if t.type in if_types:
                        nr_conditions += 1
                    elif t.type == 'END_IF':
                        nr_conditions -= 1
                    # If we are at the pertinent if-nesting level, then
                    # a condition block delimiter should be kept track of.
                    # We only keep one delimiter here; fuck ifcase, we will
                    # handle that later.
                    if nr_conditions == 1 and t.type in ('ELSE', 'OR'):
                        i_else = i
                    if nr_conditions == 0:
                        break
                # If we do not get to the end of the if,
                # add a token and go again.
                else:
                    self.populate_output_stack()
                    continue
                break
            i_end_if = i

            # Now we need to strip the skipped block.
            # In all cases we will drop the END_IF; its work is done.
            # We never read past this, so it will not mess up indexing.
            del self.output_terminal_tokens_stack[i_end_if]
            # Similar to removing the condition tokens, drop the input tokens
            # in the truth-ey or false-ey (else) block.
            if is_true:
                # If we have an ELSE, then we drop from that, inclusive, until
                # the END_IF, exclusive.
                i_to_del = i_else
                if i_else is not None:
                    range_to_del = range(i_else, i_end_if)
                # Otherwise, we do nothing.
                else:
                    range_to_del = range(0)
            else:
                # If we have an ELSE, then we drop until that, inclusive.
                i_to_del = 0
                if i_else is not None:
                    range_to_del = range(i_else + 1)
                # Otherwise, we drop until the END_IF, exclusive.
                else:
                    range_to_del = range(i_end_if)
            # Note that we always del at the same index, because the indices will
            # shift when we do a del.
            for i in range_to_del:
                del self.output_terminal_tokens_stack[i_to_del]

            # Restore the old things on the output stack.
            # TODO: check, this might be backwards.
            self.output_terminal_tokens_stack.extendleft(saved_output_stack)
        elif type_ == 'STRING':
            next_token = self.pop_next_input_token()
            tokens = []
            if next_token.type in unexpanded_cs_types:
                chars = list(next_token.value)
                # Internal instruction to produce an escape character token.
                escape_char_token = InternalToken(type_='ESCAPE_CHAR',
                                                  value=None)
                tokens += [escape_char_token]
            else:
                char = next_token.value['char']
                chars = [char]
            char_term_tokens = [make_char_cat_term_token(c, CatCode.other)
                                for c in chars]
            tokens += char_term_tokens
            self.input_tokens_stack.extendleft(tokens[::-1])
        elif type_ == 'ESCAPE_CHAR':
            escape_char_param_token = self.expander.expand_to_token_list('escapechar',
                                                                         argument_text=[])
            escape_char_code = escape_char_param_token.value
            escape_char = chr(escape_char_code)
            escape_char_token = make_char_cat_term_token(escape_char,
                                                         CatCode.other)
            self.output_terminal_tokens_stack.append(escape_char_token)
        # Just some semantic bullshit, stick it on the output stack
        # for the interpreter to deal with.
        else:
            self.output_terminal_tokens_stack.append(first_token)
