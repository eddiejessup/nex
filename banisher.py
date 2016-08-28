import logging
from collections import deque
from enum import Enum

from rply.errors import ParsingError

from common import TerminalToken, InternalToken
from lexer import (make_char_cat_token, CatCode,
                   char_cat_lex_type)
from typer import (lex_token_to_unexpanded_terminal_token,
                   make_unexpanded_control_sequence_terminal_token,
                   unexpanded_cs_types)
from expander import short_hand_def_map, def_map, parse_parameter_text, if_map
from condition_parser import condition_parser
from general_text_parser import general_text_parser

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

read_unexpanded_control_sequence_types = (
    'LET',
    'BACKTICK',
)
read_unexpanded_control_sequence_types += tuple(set(def_map.values()))
read_unexpanded_control_sequence_types += tuple(set(short_hand_def_map.values()))

if_types = if_map.values()
message_types = ('MESSAGE', 'ERROR_MESSAGE', 'WRITE')


class ContextMode(Enum):
    normal = 1
    awaiting_balanced_text_start = 2
    awaiting_unexpanded_cs = 3
    absorbing_parameter_text = 4


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
        next_token = self.pop_or_fill_and_pop(self.output_terminal_tokens_stack)
        logger.debug(self.output_terminal_tokens_stack)
        self._secret_terminal_list.append(next_token)
        # for t in self._secret_terminal_list[-20:]:
        #     print(t)
        return next_token

    def pop_or_fill_and_pop(self, stack):
        while not stack:
            self.process_input_to_stack(stack)
        next_token = stack.popleft()
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
        balanced_text = TerminalToken(type_='BALANCED_TEXT_AND_RIGHT_BRACE', value=tokens[:-1])
        return balanced_text

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

    def process_next_input_token(self):
        output_tokens = deque()

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

        # If we get a control sequence token, we need to either start expanding
        # it, or add it as an un-expanded token, depending on the context.
        if self.expanding_control_sequences and type_ in unexpanded_cs_types:
            name = first_token.value['name']
            param_text = self.expander.expand_to_parameter_text(name)
            argument_text = []
            for _ in range(len(param_text)):
                next_token = self.pop_next_input_token()
                argument_text.append(next_token)
            # Now run again, hopefully now seeing a primitive token.
            # (Might not, if the expansion needs more expansion, but the
            # ultimate escape route is to see a primitive token.)
            expanded_first_token = self.expander.expand_to_token_list(name, argument_text)
            self.input_tokens_stack.extendleft(reversed(expanded_first_token))
        elif (self.context_mode == ContextMode.awaiting_balanced_text_start and
                type_ == 'LEFT_BRACE'):
            # Put the LEFT_BRACE on the output stack.
            output_tokens.append(first_token)
            # Now merge all lex tokens until right brace lex token seen,
            # into a 'BALANCED_TEXT_AND_RIGHT_BRACE' terminal token, which we put on the
            # input stack to read later.
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
                output_tokens.append(parameter_text_token)
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
            output_tokens.append(first_token)
            # Done with getting an un-expanded control sequence.
            self.pop_context()
        elif type_ == 'LEFT_BRACE':
            # We know we aren't seeing a left brace to do with defining a
            # macro, and for now, knowing no better, we will assume we are
            # starting a new level of grouping. This case should include things
            # that have been \let equal to a begin_group-ey character token.
            # TODO: implement \let = <character token>
            # But this isn't the same as \begingroup.
            pass
        elif type_ == 'RIGHT_BRACE':
            # I think roughly same comments as for LEFT_BRACE above apply.
            pass
        elif type_ in read_unexpanded_control_sequence_types:
            # Get an unexpanded control sequence token and add it to the
            # output stack, along with the first token.
            next_token = self.pop_next_input_token()
            output_tokens.append(first_token)
            output_tokens.append(next_token)
            if type_ in def_map.values():
                self.push_context(ContextMode.absorbing_parameter_text)
                self.parameter_text_tokens = []
            elif type_ == 'LET':
                self.push_context(ContextMode.awaiting_unexpanded_cs)
        elif type_ == 'EXPAND_AFTER':
            unexpanded_token = self.pop_next_input_token()
            next_tokens = self.process_next_input_token()
            self.input_tokens_stack.extendleft(reversed(next_tokens))
            self.input_tokens_stack.appendleft(unexpanded_token)
        elif type_ in message_types:
            # TODO: this is all wrong, these things expect general_text.
            # do like (upper/lower)case does.
            output_tokens.append(first_token)
            self.push_context(ContextMode.awaiting_balanced_text_start)
        elif type_ in if_types:
            # TODO: aren't all these things actually queues, not stacks?
            # (Entails lots of renaming.)
            # Processing input tokens might return many tokens, so
            # we store them in a buffer.
            # Want to extend the stack-to-be-parsed one token at a time,
            # so we can break as soon as we have all we need.
            condition_buffer_stack = deque([first_token])
            condition_parse_stack = deque()

            # Get enough tokens to evaluate condition. We find the longest
            # input sequence that will parse, and drop that input sequence from
            # the stack, as we only need it for the condition.
            # We know to stop adding tokens when we see a switch from not
            # parsing, to parsing, to not parsing again.
            have_parsed = False
            while True:
                # While populating this, maybe we will see an if_type in the
                # condition. Haven't tested, but it seems like this should
                # recurse correctly.
                t = self.pop_or_fill_and_pop(condition_buffer_stack)
                condition_parse_stack.append(t)
                try:
                    is_true = condition_parser.parse(iter(condition_parse_stack), state='hihi')
                except (ParsingError, StopIteration):
                    if have_parsed:
                        break
                else:
                    have_parsed = True

            # We got exactly one token of fluff, to make the condition parse
            # stack not-parse. Put that back on the existing buffer, and that
            # gives us the start of the condition body stack.
            # We can forget about the rest of the condition stack, as we are
            # done with it.
            condition_buffer_stack.appendleft(condition_parse_stack.pop())
            if_stack = condition_buffer_stack

            # Now get the body of the condition text.
            # TeXbook:
            # "Expansion is suppressed at the following times:
            # [...]
            # When tokens are being skipped because conditional text is
            # being ignored."
            # From testing, the above does not seem to hold, so I am going
            # to carry on expansion.
            nr_conditions = 1
            in_else = None
            not_skipped_tokens = []
            condition_block_delimiter_types = ('ELSE', 'OR')
            condition_types = ('END_IF',) + tuple(if_types) + tuple(condition_block_delimiter_types)
            while True:
                t = self.pop_or_fill_and_pop(if_stack)
                # Keep track of nested conditions.
                # Since we expand, I'm not actually sure this is needed,
                # as an if_type will be handled inside the process call,
                # but I don't think it does any harm.
                if t.type in if_types:
                    nr_conditions += 1
                # This one *is* needed, for the matching END_IF.
                elif t.type == 'END_IF':
                    nr_conditions -= 1

                # If we are at the pertinent if-nesting level, then
                # a condition block delimiter should be kept track of.
                # We only keep one delimiter here; fuck ifcase, we will
                # handle that later.
                if nr_conditions == 1 and t.type in condition_block_delimiter_types:
                    in_else = True

                # Don't include internal tokens.
                if t.type not in condition_types:
                    # Include token if we're in first block and condition is
                    # true, or we're in the else block and condition is false.
                    if (is_true and not in_else) or (not is_true and in_else):
                        not_skipped_tokens.append(t)

                if nr_conditions == 0:
                    break
            output_tokens.extendleft(reversed(not_skipped_tokens))

        elif type_ == 'STRING':
            next_token = self.pop_next_input_token()
            string_tokens = []
            if next_token.type in unexpanded_cs_types:
                chars = list(next_token.value)
                # Internal instruction to produce an escape character token.
                escape_char_token = InternalToken(type_='ESCAPE_CHAR',
                                                  value=None)
                string_tokens += [escape_char_token]
            else:
                char = next_token.value['char']
                chars = [char]
            char_term_tokens = [make_char_cat_term_token(c, CatCode.other)
                                for c in chars]
            string_tokens += char_term_tokens
            self.input_tokens_stack.extendleft(reversed(string_tokens))
        elif type_ == 'CS_NAME':
            cs_name_tokens = []
            cs_name_stack = deque()

            while True:
                t = self.pop_or_fill_and_pop(cs_name_stack)
                if t.type == 'END_CS_NAME':
                    break
                cs_name_tokens.append(t)
            chars = [tok.value['char'] for tok in cs_name_tokens]
            cs_name = ''.join(chars)
            cs_token = make_unexpanded_control_sequence_terminal_token(cs_name)
            # If we expanded such that we got tokens past 'endcsname',
            # put them back on the input stack.
            self.input_tokens_stack.extendleft(reversed(cs_name_stack))
            # But first comes our shiny new control sequence token.
            self.input_tokens_stack.appendleft(cs_token)
        elif type_ == 'ESCAPE_CHAR':
            escape_char_param_token = self.expander.expand_to_token_list('escapechar',
                                                                         argument_text=[])
            escape_char_code = escape_char_param_token.value
            escape_char = chr(escape_char_code)
            escape_char_token = make_char_cat_term_token(escape_char,
                                                         CatCode.other)
            output_tokens.append(escape_char_token)
        elif type_ in ('UPPER_CASE', 'LOWER_CASE'):
            case_tokens = []
            while True:
                t = self.pop_next_input_token()
                case_tokens.append(t)
                if t.type == 'LEFT_BRACE':
                    balanced_text_token = self.get_balanced_text_token()
                    case_tokens.append(balanced_text_token)
                    break
            # Check arguments obey the rules of a 'general text'.
            balanced_text_token = general_text_parser.parse(iter(case_tokens),
                                                            state='hihi')

            case_maps_map = {
                'LOWER_CASE': self.lexer.lower_case_code,
                'UPPER_CASE': self.lexer.upper_case_code,
            }
            case_map = case_maps_map[type_]

            def modify_tok(tok):
                if tok.value['lex_type'] == char_cat_lex_type:
                    old_char = tok.value['char']
                    new_char = case_map[old_char]
                    if new_char == chr(0):
                        new_char = old_char
                    new_lex_tok = make_char_cat_token(char=new_char,
                                                      cat=tok.value['cat'])
                    new_tok = lex_token_to_unexpanded_terminal_token(new_lex_tok)
                    return new_tok
                else:
                    return tok

            new_toks = list(map(modify_tok, balanced_text_token.value))
            # Put cased tokens back on the stack to read again.
            self.input_tokens_stack.extendleft(reversed(new_toks))

        # Just some semantic bullshit, stick it on the output stack
        # for the interpreter to deal with.
        else:
            output_tokens.append(first_token)
        return output_tokens

    def populate_output_stack(self):
        self.process_input_to_stack(self.output_terminal_tokens_stack)

    def process_input_to_stack(self, stack):
        next_output_tokens = self.process_next_input_token()
        stack.extend(next_output_tokens)
