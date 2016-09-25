import logging
from collections import deque
from enum import Enum

from common import TerminalToken
from lexer import make_char_cat_token, is_control_sequence_call
from parser import parser
from typer import (CatCode,
                   char_cat_lex_type, control_sequence_lex_type,
                   lex_token_to_unexpanded_terminal_token,
                   make_unexpanded_control_sequence_terminal_token,
                   unexpanded_cs_types, unexpanded_token_type,
                   explicit_box_map,
                   short_hand_def_map, def_map, if_map,
                   )
from interpreter import Mode, vertical_modes, Group
from executor import CommandGrabber, execute_commands, execute_condition
from expander import parse_parameter_text
from condition_parser import condition_parser
from general_text_parser import general_text_parser

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')

read_unexpanded_control_sequence_types = (
    'LET',
    'BACKTICK',
    'FONT',
)
read_unexpanded_control_sequence_types += tuple(set(def_map.values()))
read_unexpanded_control_sequence_types += tuple(set(short_hand_def_map.values()))

if_types = if_map.values()
message_types = ('MESSAGE', 'ERROR_MESSAGE', 'WRITE')
hyphenation_types = ('HYPHENATION', 'PATTERNS')

token_variable_start_types = ('TOKEN_PARAMETER', 'TOKS_DEF_TOKEN', 'TOKS')


class ContextMode(Enum):
    normal = 1
    awaiting_balanced_text_start = 2
    awaiting_balanced_text_or_token_variable_start = 7
    awaiting_make_h_box_start = 3
    awaiting_make_v_box_start = 4
    awaiting_make_v_top_start = 5
    absorbing_parameter_text = 6


box_context_mode_map = {
    'H_BOX': ContextMode.awaiting_make_h_box_start,
    'V_BOX': ContextMode.awaiting_make_v_box_start,
    'V_TOP': ContextMode.awaiting_make_v_top_start,
}
awaiting_make_box_context_modes = tuple(box_context_mode_map.values())

expanding_context_modes = (
    ContextMode.normal,
    ContextMode.awaiting_balanced_text_start,
    ContextMode.awaiting_balanced_text_or_token_variable_start,
    ContextMode.awaiting_make_h_box_start,
    ContextMode.awaiting_make_v_box_start,
    ContextMode.awaiting_make_v_top_start,
)
expanding_context_modes += awaiting_make_box_context_modes


def make_char_cat_term_token(char, cat):
    char_lex_token = make_char_cat_token(char, cat)
    char_term_token = lex_token_to_unexpanded_terminal_token(char_lex_token)
    return char_term_token


def get_brace_sign(token):
    if token.type == 'LEFT_BRACE':
        return 1
    elif token.type == 'RIGHT_BRACE':
        return -1
    else:
        return 0


class Banisher(object):

    def __init__(self, lexer, state, reader):
        self.lexer = lexer
        self.global_state = state
        # The banisher needs the reader because it can execute commands,
        # and one possible command is '\input', which needs to modify the
        # reader.
        self.reader = reader
        # Input buffer.
        self.input_tokens_queue = deque()
        self.context_mode_stack = []

        self._secret_terminal_list = []

    @property
    def _next_lex_token(self):
        return self.lexer.next_token

    @property
    def expanding_control_sequences(self):
        return self.context_mode in expanding_context_modes

    def pop_or_fill_and_pop(self, queue):
        while not queue:
            self.process_input_to_queue(queue)
        next_token = queue.popleft()
        return next_token

    def pop_or_fill_and_pop_input(self, input_queue):
        if not input_queue:
            self.pop_input_to_queue(input_queue)
        next_token = input_queue.popleft()
        return next_token

    def populate_input_queue(self):
        new_lex_token = self._next_lex_token
        terminal_token = lex_token_to_unexpanded_terminal_token(new_lex_token)
        self.input_tokens_queue.append(terminal_token)

    def pop_next_input_token(self):
        if not self.input_tokens_queue:
            self.populate_input_queue()
        return self.input_tokens_queue.popleft()

    def get_balanced_text_token(self):
        tokens = []
        brace_level = 1
        while True:
            token = self.pop_next_input_token()
            tokens.append(token)
            brace_level += get_brace_sign(token)
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

    def get_escape_char_token(self):
        escape_char_code = self.global_state.get_parameter_value('escapechar')
        if escape_char_code >= 0:
            escape_char = chr(escape_char_code)
            escape_char_token = make_char_cat_term_token(escape_char,
                                                         CatCode.other)
            return escape_char_token
        else:
            return None

    def process_next_input_token(self):
        # A terminal token is simply a token that is accepted by the parser.
        # Might be a lex token, a primitive token or a terminal token.
        first_token = self.pop_next_input_token()
        try:
            output_tokens = self._process_input_token(first_token)
        except Exception:
            # If something goes wrong in the expansion, we *assume* that the
            # function has had no side effects, and just put the input token
            # back on the input queue, then raise the exception. This might
            # happen if we've tried to parse tokens too far in one command, and
            # bled into another command that only makes sense once the previous
            # one has executed. For example, defining a new macro, then the
            # next command calling that macro.
            self.input_tokens_queue.appendleft(first_token)
            raise
        return output_tokens

    def _process_input_token(self, first_token):
        output_tokens = deque()

        # To reduce my own confusion:
        # a primitive token is one that is not a lex token. But it might not be
        # a terminal token either, if it needs combining with other tokens
        # to make a terminal token. For instance, a primitive token might be a
        # \def that needs combining with the rest of its bits to make a
        # DEFINITION terminal token.
        # But I might blur the line between these two sometimes.

        # If the token is a control sequence call, then we must check if it is
        # a user control sequence. If it is, then we expand it. If it isn't, we
        # will 'type' it into a primitive sequence. NOT like macro expansion,
        # because it happens in the same call. This is important, because sometimes
        # we are only expanding once, not recursively, so it is important what
        # one expansion call does.
        if (self.expanding_control_sequences and
                first_token.type in unexpanded_cs_types):
            first_token = self.global_state.resolve_control_sequence_to_token(first_token.value['name'])
        type_ = first_token.type
        if type_ == 'MACRO':
            macro_definition = first_token.value['definition']
            name = macro_definition.value['name']
            macro_text = macro_definition.value['text']
            params = macro_text.value['parameter_text']

            def tokens_equal(t, u):
                if t.value['lex_type'] != u.value['lex_type']:
                    return False
                if t.value['lex_type'] == char_cat_lex_type:
                    attr_keys = ('char', 'cat')
                elif t.value['lex_type'] == control_sequence_lex_type:
                    attr_keys = ('name',)
                else:
                    import pdb; pdb.set_trace()
                try:
                    return all(t.value[k] == u.value[k] for k in attr_keys)
                except:
                    import pdb; pdb.set_trace()

            arguments = []
            i_param = 0
            for i_param in range(len(params)):
                arg_toks = []
                p_t = params[i_param]
                if p_t.type not in ('UNDELIMITED_PARAM', 'DELIMITED_PARAM'):
                    # We should only see non-parameters in the parameter list,
                    # if they are text preceding the parameters proper. See
                    # the comments in `parse_parameter_text` for further
                    # details.
                    # We just swallow up these tokens.
                    assert not arguments
                    next_token = self.pop_next_input_token()
                    if not tokens_equal(p_t, next_token):
                        raise Exception
                    continue
                delim_toks = p_t.value['delim_tokens']
                if p_t.type == 'UNDELIMITED_PARAM':
                    assert not delim_toks
                    next_token = self.pop_next_input_token()
                    if next_token.type == 'LEFT_BRACE':
                        b_tok = self.get_balanced_text_token()
                        arg_toks.extend(b_tok.value)
                    else:
                        arg_toks.append(next_token)
                elif p_t.type == 'DELIMITED_PARAM':
                    # To be finished, we must be balanced brace-wise.
                    brace_level = 0
                    while True:
                        next_token = self.pop_next_input_token()
                        brace_level += get_brace_sign(next_token)
                        arg_toks.append(next_token)
                        # If we are balanced, and we could possibly
                        # have got the delimiter tokens.
                        if brace_level == 0 and len(arg_toks) >= len(delim_toks):
                            # Check if the recent argument tokens match the
                            # delimiter tokens, and if so, we are done.
                            to_compare = zip(reversed(arg_toks),
                                             reversed(delim_toks))
                            if all(tokens_equal(*ts) for ts in to_compare):
                                break
                    # Remove the delimiter tokens as they are not part of
                    # the argument
                    arg_toks = arg_toks[:-len(delim_toks)]
                    # We remove exactly one set of braces, if present.
                    if arg_toks[0].type == 'LEFT_BRACE' and arg_toks[-1].type == 'RIGHT_BRACE':
                        arg_toks = arg_toks[1:-1]
                arguments.append(arg_toks)

            expanded_first_token = self.global_state.expand_macro_to_token_list(name, arguments)

            # Now run again, hopefully now seeing a primitive token.
            # (Might not, if the expansion needs more expansion, but the
            # ultimate escape route is to see a primitive token.)
            self.input_tokens_queue.extendleft(reversed(expanded_first_token))
        # TODO: Maybe put these as sub-checks, inside seeing 'LEFT_BRACE'.
        # TODO: In fact, I don't think all of these brace handling cases belong
        # in banisher; LEFT_BRACE should be a command, and it can be handled
        # in the executor.
        elif (self.context_mode in (ContextMode.awaiting_balanced_text_start,
                                    ContextMode.awaiting_balanced_text_or_token_variable_start)
                and type_ == 'LEFT_BRACE'):
            # Put the LEFT_BRACE on the output queue.
            output_tokens.append(first_token)
            # Now merge all lex tokens until right brace lex token seen,
            # into a 'BALANCED_TEXT_AND_RIGHT_BRACE' terminal token, which we put on the
            # input queue to read later.
            balanced_text_token = self.get_balanced_text_token()
            # Put it on the input queue to be read again.
            output_tokens.append(balanced_text_token)
            # Done with getting balanced text.
            self.pop_context()
        elif (self.context_mode == ContextMode.awaiting_balanced_text_or_token_variable_start and
              type_ in token_variable_start_types):
            # Put the token on the output queue.
            output_tokens.append(first_token)
            # We can handle this sort of token-list argument in the parser; we
            # only had this context in case a balanced text needed to be got.
            self.pop_context()
        elif (self.context_mode in box_context_mode_map.values() and
                type_ == 'LEFT_BRACE'):
            # Put the LEFT_BRACE on the output queue.
            output_tokens.append(first_token)

            # Left brace initiates a new level of grouping.
            # See Group class for explanation of this bit.
            # TODO: merge pushing group and scope with helper method(s).
            if self.context_mode == ContextMode.awaiting_make_v_box_start:
                box_group = Group.v_box
            elif self.context_mode == ContextMode.awaiting_make_v_top_start:
                box_group = Group.v_top
            elif self.context_mode == ContextMode.awaiting_make_h_box_start:
                if self.global_state.mode == Mode.vertical:
                    box_group = Group.adjusted_h_box
                else:
                    box_group = Group.h_box
            self.global_state.push_group(box_group)
            # (By later context, can tell this means a new scope.)
            self.global_state.push_new_scope()

            # Enter relevant mode.
            if self.context_mode in (ContextMode.awaiting_make_v_box_start,
                                     ContextMode.awaiting_make_v_top_start):
                mode = Mode.internal_vertical
            elif self.context_mode == ContextMode.awaiting_make_h_box_start:
                mode = Mode.restricted_horizontal
            self.global_state.push_mode(mode)

            # Done with the context.
            self.pop_context()

            box_parser = parser
            command_grabber = CommandGrabber(self, parser=box_parser)

            # Matching right brace should trigger EndOfSubExecutor and return.
            box = execute_commands(command_grabber, self.global_state,
                                   banisher=self, reader=self.reader)

            # [After ending the group, then TeX] packages the hbox (using the
            # size that was saved on the stack), and completes the setbox
            # command, returning to the mode it was in at the time of the
            # setbox.
            material_map = {
                Mode.internal_vertical: 'VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE',
                Mode.restricted_horizontal: 'HORIZONTAL_MODE_MATERIAL_AND_RIGHT_BRACE',
            }
            material_type = material_map[mode]
            material = TerminalToken(type_=material_type, value=box)
            output_tokens.append(material)
            self.global_state.pop_mode()
        elif type_ in read_unexpanded_control_sequence_types:
            # Get an unexpanded control sequence token and add it to the
            # output queue, along with the first token.
            next_token = self.pop_next_input_token()
            output_tokens.append(first_token)
            output_tokens.append(next_token)
            if type_ in def_map.values():
                parameter_text_tokens = []
                while True:
                    tok = self.pop_next_input_token()
                    if tok.type == 'LEFT_BRACE':
                        break
                    parameter_text_tokens.append(tok)
                parameters = parse_parameter_text(parameter_text_tokens)
                parameters_token = TerminalToken(type_='PARAMETER_TEXT',
                                                 value=parameters)
                # Now get the replacement text.
                # TODO: this is where expanded-def will be differentiated from
                # normal-def.
                balanced_text_token = self.get_balanced_text_token()
                # Put the parameter text, LEFT_BRACE and replacement
                # text on the output queue.
                output_tokens.extend([parameters_token, tok,
                                      balanced_text_token])
            elif type_ == 'LET':
                # We are going to parse the arguments of LET ourselves,
                # because we want to allow the target token be basically
                # anything, and this would be a pain to tell the parser.
                let_arguments = []
                let_arguments.append(self.pop_next_input_token())
                # If we have found an equals, ignore that and read again.
                if let_arguments[-1].type == 'EQUALS':
                    let_arguments.append(self.pop_next_input_token())
                if let_arguments[-1].type == 'SPACE':
                    let_arguments.append(self.pop_next_input_token())
                # Make the target argument into a special 'any' token.
                let_arguments[-1] = TerminalToken(type_=unexpanded_token_type,
                                                  value=let_arguments[-1])
                output_tokens.extend(let_arguments)
        elif type_ in token_variable_start_types:
            # Watch for a balanced text starting.
            output_tokens.append(first_token)
            self.push_context(ContextMode.awaiting_balanced_text_or_token_variable_start)
        elif type_ == 'EXPAND_AFTER':
            unexpanded_token = self.pop_next_input_token()
            next_tokens = self.process_next_input_token()
            self.input_tokens_queue.extendleft(reversed(next_tokens))
            self.input_tokens_queue.appendleft(unexpanded_token)
        elif type_ in message_types:
            # TODO: this is all wrong, these things expect general_text.
            # do like (upper/lower)case does.
            output_tokens.append(first_token)
            self.push_context(ContextMode.awaiting_balanced_text_start)
        elif type_ in hyphenation_types:
            # TODO: See above.
            output_tokens.append(first_token)
            self.push_context(ContextMode.awaiting_balanced_text_start)
        elif type_ in if_types:
            command_grabber = CommandGrabber(self, parser=condition_parser)
            command_grabber.buffer_queue.append(first_token)
            condition_token = command_grabber.get_command()
            outcome = execute_condition(condition_token, self.global_state)
            # Pick up any left-over tokens from the condition command parsing.
            if_queue = command_grabber.buffer_queue

            # TODO: Move inside executor? Not sure.
            if type_ == 'IF_CASE':
                i_block_to_pick = outcome
            else:
                i_block_to_pick = 0 if outcome else 1

            # Now get the body of the condition text.
            # TeXbook:
            # "Expansion is suppressed at the following times:
            # [...]
            # When tokens are being skipped because conditional text is
            # being ignored."
            # From testing, the above does not seem to hold, so I am going
            # to carry on expansion.
            nr_conditions = 1
            i_block = 0
            not_skipped_tokens = []
            condition_block_delimiter_names = ('else', 'or')

            if_names = if_map.keys()

            def get_condition_sign(token):
                if not is_control_sequence_call(token):
                    return 0
                name = token.value['name']
                if name in if_names:
                    return 1
                elif name == 'fi':
                    return -1
                else:
                    return 0

            def is_condition_delimiter(token):
                return (is_control_sequence_call(token) and
                        t.value['name'] in condition_block_delimiter_names)

            while True:
                t = self.pop_or_fill_and_pop_input(if_queue)

                # Keep track of nested conditions.
                nr_conditions += get_condition_sign(t)

                # If we get the terminal  \fi, break
                if nr_conditions == 0:
                    break
                # If we are at the pertinent if-nesting level, then
                # a condition block delimiter should be kept track of.
                elif nr_conditions == 1 and is_condition_delimiter(t):
                    i_block += 1
                # if we're in the block the condition says we should pick,
                # include token.
                elif i_block == i_block_to_pick:
                    not_skipped_tokens.append(t)
                # Otherwise we are skipping tokens.
                else:
                    pass
            self.input_tokens_queue.extendleft(reversed(not_skipped_tokens))
        elif type_ == 'STRING':
            next_token = self.pop_next_input_token()
            string_tokens = []
            if next_token.type in unexpanded_cs_types:
                chars = list(next_token.value['name'])
                escape_char_token = self.get_escape_char_token()
                if escape_char_token is not None:
                    string_tokens += [escape_char_token]
            else:
                char = next_token.value['char']
                chars = [char]
            char_term_tokens = [make_char_cat_term_token(c, CatCode.other)
                                for c in chars]
            string_tokens += char_term_tokens
            self.input_tokens_queue.extendleft(reversed(string_tokens))
        elif type_ == 'CS_NAME':
            cs_name_tokens = []
            cs_name_queue = deque()

            while True:
                t = self.pop_or_fill_and_pop(cs_name_queue)
                if t.type == 'END_CS_NAME':
                    break
                cs_name_tokens.append(t)
            chars = [tok.value['char'] for tok in cs_name_tokens]
            cs_name = ''.join(chars)
            cs_token = make_unexpanded_control_sequence_terminal_token(cs_name)
            # If we expanded such that we got tokens past 'endcsname',
            # put them back on the input queue.
            self.input_tokens_queue.extendleft(reversed(cs_name_queue))
            # But first comes our shiny new control sequence token.
            self.input_tokens_queue.appendleft(cs_token)
        elif type_ == 'ESCAPE_CHAR':
            escape_char_token = self.get_escape_char_token()
            if escape_char_token is not None:
                output_tokens.append(escape_char_token)
        elif type_ in ('UPPER_CASE', 'LOWER_CASE'):
            # TODO: This is wrong. Need to expand tokens between this command
            # and the left brace. Probably need to push two contexts; one to
            # get a balanced text token; and one to indicate what to do with
            # it when it's got.
            case_tokens = []
            while True:
                t = self.pop_next_input_token()
                case_tokens.append(t)
                if t.type == 'LEFT_BRACE':
                    balanced_text_token = self.get_balanced_text_token()
                    case_tokens.append(balanced_text_token)
                    break
            # Check arguments obey the rules of a 'general text'.
            # TODO: Can this be done better with a command grabber or
            # something?
            general_text_token = general_text_parser.parse(iter(case_tokens))

            case_funcs_map = {
                'LOWER_CASE': self.global_state.get_lower_case_code,
                'UPPER_CASE': self.global_state.get_upper_case_code,
            }
            case_func = case_funcs_map[type_]

            def get_cased_tok(un_cased_tok):
                if un_cased_tok.value['lex_type'] == char_cat_lex_type:
                    un_cased_char = un_cased_tok.value['char']
                    cased_char = case_func(un_cased_char)
                    if cased_char == chr(0):
                        cased_char = un_cased_char
                    # Note that the category code is not changed.
                    cased_lex_tok = make_char_cat_token(char=cased_char,
                                                        cat=un_cased_tok.value['cat'])
                    cased_tok = lex_token_to_unexpanded_terminal_token(cased_lex_tok)
                    return cased_tok
                else:
                    return un_cased_tok

            un_cased_toks = general_text_token.value
            cased_toks = list(map(get_cased_tok, un_cased_toks))
            # Put cased tokens back on the queue to read again.
            self.input_tokens_queue.extendleft(reversed(cased_toks))
        elif type_ in explicit_box_map.values():
            # First we read until box specification is finished.
            # Then we will do actual group and scope changes and so on.
            self.push_context(box_context_mode_map[type_])
            # Put the box token on the queue.
            output_tokens.append(first_token)
        # Just some semantic bullshit, stick it on the output queue
        # for the interpreter to deal with.
        else:
            output_tokens.append(first_token)
        return output_tokens

    def process_input_to_queue(self, queue):
        next_output_tokens = self.process_next_input_token()
        queue.extend(next_output_tokens)

    def pop_input_to_queue(self, queue):
        next_input_token = self.pop_next_input_token()
        queue.append(next_input_token)
