import logging
from collections import deque

from .tokens import InstructionToken
from .lexer import (is_control_sequence_call,
                    char_cat_lex_type, control_sequence_lex_type)
from .codes import CatCode
from .constants.primitive_control_sequences import (Instructions,
                                                    explicit_box_instructions,
                                                    short_hand_def_instructions,
                                                    def_instructions,
                                                    if_instructions,
                                                    message_instructions,
                                                    unexpanded_cs_instructions,
                                                    hyphenation_instructions)
from .lex_typer import (make_control_sequence_instruction_token,
                        make_instruction_token_from_char_cat)
from .state import Mode, Group, ContextMode, context_mode
from .executor import execute_commands
from .if_executor import execute_condition
from .expander import parse_parameter_text
from .parsing.utils import ChunkGrabber
from .parsing.command_parser import command_parser
from .parsing.condition_parser import condition_parser
from .parsing.general_text_parser import general_text_parser


logger = logging.getLogger(__name__)

read_unexpanded_control_sequence_instructions = (
    Instructions.font,
) + short_hand_def_instructions

token_variable_start_instructions = (
    # TODO: This will break, parameters are not instructions.
    Instructions.token_parameter,
    Instructions.toks_def_token,
    Instructions.toks,
)

box_context_mode_map = {
    Instructions.h_box: ContextMode.awaiting_make_h_box_start,
    Instructions.v_box: ContextMode.awaiting_make_v_box_start,
    Instructions.v_top: ContextMode.awaiting_make_v_top_start,
}

mode_material_instruction_map = {
    Mode.internal_vertical: Instructions.vertical_mode_material_and_right_brace,
    Mode.restricted_horizontal: Instructions.horizontal_mode_material_and_right_brace,
}

expanding_context_modes = (
    ContextMode.normal,
    ContextMode.awaiting_balanced_text_start,
    ContextMode.awaiting_balanced_text_or_token_variable_start,
    ContextMode.awaiting_make_h_box_start,
    ContextMode.awaiting_make_v_box_start,
    ContextMode.awaiting_make_v_top_start,
)


def get_brace_sign(token):
    if token.instruction == Instructions.left_brace:
        return 1
    elif token.instruction == Instructions.right_brace:
        return -1
    else:
        return 0


class Banisher:

    def __init__(self, token_source, state, reader):
        self.token_source = token_source
        self.global_state = state
        # The banisher needs the reader because it can execute commands,
        # and one possible command is '\input', which needs to modify the
        # reader.
        self.reader = reader
        # Input buffer.
        self.input_tokens_queue = deque()

    @property
    def expanding_control_sequences(self):
        return self.context_mode in expanding_context_modes

    def pop_or_fill_and_pop(self, queue):
        while not queue:
            next_output_tokens = self._process_next_input_token()
            queue.extend(next_output_tokens)
        next_token = queue.popleft()
        return next_token

    def replace_on_input_queue(self, tokens):
        self.input_tokens_queue.extendleft(reversed(tokens))

    def _get_next_input_token(self):
        if not self.input_tokens_queue:
            new_input_token = self.token_source.pop_next_output_token()
            self.input_tokens_queue.append(new_input_token)
        return self.input_tokens_queue.popleft()

    def get_balanced_text_token(self):
        tokens = []
        brace_level = 1
        while True:
            token = self._get_next_input_token()
            tokens.append(token)
            brace_level += get_brace_sign(token)
            if brace_level == 0:
                break
        balanced_text = InstructionToken.from_instruction(
            Instructions.balanced_text_and_right_brace,
            value=tokens[:-1],
            position_like=tokens[0]
        )
        return balanced_text

    def _push_context(self, *args, **kwargs):
        return self.global_state._push_context(*args, **kwargs)

    def _pop_context(self, *args, **kwargs):
        return self.global_state._pop_context(*args, **kwargs)

    @property
    def context_mode(self):
        return self.global_state.context_mode

    def get_escape_char_terminal_token(self, position_like=None):
        escape_char_code = self.global_state.get_parameter_value('escapechar')
        if escape_char_code >= 0:
            escape_char = chr(escape_char_code)
            escape_char_token = make_instruction_token_from_char_cat(
                escape_char, CatCode.other, position_like=position_like)
            return escape_char_token
        else:
            return None

    def _process_next_input_token(self):
        first_token = self._get_next_input_token()
        try:
            output_tokens = self._process_input_token(first_token)
        except Exception:
            # If something goes wrong in the expansion, we *assume* that the
            # function has had no side effects, and just put the input token
            # back on the input queue, then raise the exception. This might
            # happen if we've tried to parse tokens too far in one chunk, and
            # bled into another chunk that only makes sense once the previous
            # one has executed. For example, defining a new macro, then
            # calling that macro.
            self.input_tokens_queue.appendleft(first_token)
            raise
        return output_tokens

    def handle_macro(self, first_token):
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

        # Get macro arguments.
        # Set context to inhibit expansion.
        with context_mode(self.global_state,
                          ContextMode.absorbing_macro_arguments):
            arguments = []
            i_param = 0
            for i_param in range(len(params)):
                arg_toks = []
                p_t = params[i_param]
                if p_t.instruction not in (Instructions.undelimited_param,
                                           Instructions.delimited_param):
                    # We should only see non-parameters in the parameter list,
                    # if they are text preceding the parameters proper. See
                    # the comments in `parse_parameter_text` for further
                    # details.
                    # We just swallow up these tokens.
                    assert not arguments
                    next_token = self._get_next_input_token()
                    if not tokens_equal(p_t, next_token):
                        import pdb; pdb.set_trace()
                        raise Exception
                    continue
                delim_toks = p_t.value['delim_tokens']
                if p_t.instruction == Instructions.undelimited_param:
                    assert not delim_toks
                    next_token = self._get_next_input_token()
                    if next_token.instruction == Instructions.left_brace:
                        b_tok = self.get_balanced_text_token()
                        arg_toks.extend(b_tok.value)
                    else:
                        arg_toks.append(next_token)
                elif p_t.instruction == Instructions.delimited_param:
                    # To be finished, we must be balanced brace-wise.
                    brace_level = 0
                    while True:
                        next_token = self._get_next_input_token()
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
                    if arg_toks[0].instruction == Instructions.left_brace and arg_toks[-1].instruction == Instructions.right_brace:
                        arg_toks = arg_toks[1:-1]
                arguments.append(arg_toks)

        expanded_first_token = self.global_state.expand_macro_to_token_list(name, arguments)

        # Now run again, hopefully now seeing a primitive token.
        # (Might not, if the expansion needs more expansion, but the
        # ultimate escape route is to see a primitive token.)
        self.replace_on_input_queue(expanded_first_token)
        return []

    def handle_if(self, first_token):
        condition_grabber = ChunkGrabber(self, parser=condition_parser)
        condition_grabber.buffer_token_queue.append(first_token)
        condition_token = condition_grabber.get_chunk()
        outcome = execute_condition(condition_token, self.global_state)
        # Pick up any left-over tokens from the condition parsing.
        if_queue = condition_grabber.buffer_token_queue

        # TODO: Move inside executor? Not sure.
        if first_token.instruction == Instructions.if_case:
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

        # I don't think I can rely on instructions, because expansion is
        # suppressed.
        delimit_condition_block_names = ('else', 'or')
        end_condition_names = ('fi',)
        start_condition_names = ('ifnum', 'iftrue', 'iffalse', 'ifcase',)

        def get_condition_sign(token):
            if not is_control_sequence_call(token):
                return 0
            name = token.value['name']
            if name in start_condition_names:
                return 1
            elif name in end_condition_names:
                return -1
            else:
                return 0

        def is_condition_delimiter(token):
            return (is_control_sequence_call(token) and
                    t.value['name'] in delimit_condition_block_names)

        with context_mode(self.global_state,
                          ContextMode.absorbing_conditional_text):
            while True:
                if not if_queue:
                    if_queue.append(self._get_next_input_token())
                t = if_queue.popleft()

                # Keep track of nested conditions.
                nr_conditions += get_condition_sign(t)

                # If we get the terminal \fi, break
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
        self.replace_on_input_queue(not_skipped_tokens)

    def handle_making_box(self, first_token):
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
        # TODO: Use context manager for mode.
        self.global_state.push_mode(mode)

        # Done with the context.
        self._pop_context()

        box_parser = command_parser
        chunk_grabber = ChunkGrabber(self, parser=box_parser)

        # Matching right brace should trigger EndOfSubExecutor and return.
        execute_commands(chunk_grabber, self.global_state,
                         banisher=self, reader=self.reader)

        # [After ending the group, then TeX] packages the hbox (using the
        # size that was saved on the stack), and completes the setbox
        # command, returning to the mode it was in at the time of the
        # setbox.
        layout_list = self.global_state.pop_mode()
        material_token = InstructionToken.from_instruction(
            mode_material_instruction_map[mode],
            value=layout_list,
            position_like=first_token
        )
        # Put the LEFT_BRACE on the output queue, and the box material.
        return [first_token, material_token]

    def handle_def(self, first_token):
        cs_name_token = self.get_cs_name_token()

        # Get parameter text.
        parameter_text_tokens = []
        with context_mode(self.global_state,
                          ContextMode.absorbing_macro_parameter_text):
            while True:
                tok = self._get_next_input_token()
                if tok.instruction == Instructions.left_brace:
                    left_brace_token = tok
                    break
                parameter_text_tokens.append(tok)
        parameters = parse_parameter_text(parameter_text_tokens)
        parameters_token = InstructionToken.from_instruction(
            Instructions.parameter_text,
            value=parameters,
            position_like=first_token
        )

        # Now get the replacement text.
        # TODO: this is where expanded-def will be differentiated from
        # normal-def.
        with context_mode(self.global_state,
                          ContextMode.absorbing_macro_replacement_text):
            replacement_text_token = self.get_balanced_text_token()

        # Add the def token, macro name, parameter text, LEFT_BRACE and
        # replacement text to the output queue.
        return [first_token, cs_name_token, parameters_token, left_brace_token,
                replacement_text_token]

    def handle_let(self, first_token):
        cs_name_token = self.get_cs_name_token()

        # We are going to parse the arguments of LET ourselves,
        # because we want to allow the target token be basically
        # anything, and this would be a pain to tell the parser.
        let_arguments = []
        with context_mode(self.global_state,
                          ContextMode.absorbing_misc_unexpanded_arguments):
            let_arguments.append(self._get_next_input_token())
            # If we have found an equals, ignore that and read again.
            if let_arguments[-1].instruction == Instructions.equals:
                let_arguments.append(self._get_next_input_token())
            if let_arguments[-1].instruction == Instructions.space:
                let_arguments.append(self._get_next_input_token())
        # Make the target argument into a special 'any' token.
        let_arguments[-1] = InstructionToken.from_instruction(
            Instructions.let_target,
            value=let_arguments[-1],
            position_like=first_token
        )
        return [first_token, cs_name_token] + let_arguments

    def handle_backtick(self, first_token):
        # Add an unexpanded control sequence as a terminal token to the output.
        with context_mode(self.global_state, ContextMode.absorbing_backtick_argument):
            arg_token = self._get_next_input_token()
        return [first_token, arg_token]

    def get_cs_name_token(self):
        # Get an unexpanded control sequence as a terminal token.
        with context_mode(self.global_state,
                          ContextMode.absorbing_new_control_sequence_name):
            return self._get_next_input_token()

    def _process_input_token(self, first_token):
        if first_token.char_nr is not None:
            print(first_token.get_position_str(self.reader))
        output_tokens = deque()

        # If the token is an unexpanded control sequence call, and expansion is
        # not suppressed, then we must normalize it:
        # - A user control sequence will become a (non-terminal) macro token.
        # - A \let character will become the (terminal) character token.
        # - A primitive control sequence will become a terminal token.
        if (self.expanding_control_sequences and
                first_token.instruction in unexpanded_cs_instructions):
            name = first_token.value['name']
            first_token = self.global_state.resolve_control_sequence_to_token(
                name, position_like=first_token)

        instr = first_token.instruction
        if instr == Instructions.macro:
            self.handle_macro(first_token)
        elif (self.context_mode in (ContextMode.awaiting_balanced_text_start,
                                    ContextMode.awaiting_balanced_text_or_token_variable_start)
                and instr == Instructions.left_brace):
            # Put the LEFT_BRACE on the output queue, and then get a balanced-
            # text token and add that.
            output_tokens.extend([first_token, self.get_balanced_text_token()])
            # Done getting balanced text, so pop context.
            self._pop_context()
        elif (self.context_mode == ContextMode.awaiting_balanced_text_or_token_variable_start and
              instr in token_variable_start_instructions):
            # We can handle this sort of token-list argument in the parser; we
            # only had this context in case a balanced text needed to be got,
            # so we can just put the token on the output queue and pop the
            # context.
            output_tokens.append(first_token)
            self._pop_context()
        elif (self.context_mode in box_context_mode_map.values() and
                instr == Instructions.left_brace):
            output_tokens.extend(self.handle_making_box(first_token))
        elif instr in read_unexpanded_control_sequence_instructions:
            output_tokens.extend([first_token, self.get_cs_name_token()])
        elif instr in def_instructions:
            output_tokens.extend(self.handle_def(first_token))
        elif instr == Instructions.let:
            output_tokens.extend(self.handle_let(first_token))
        elif instr == Instructions.backtick:
            output_tokens.extend(self.handle_backtick(first_token))
        elif instr in token_variable_start_instructions:
            output_tokens.append(first_token)
            # Watch for a balanced text starting.
            self._push_context(ContextMode.awaiting_balanced_text_or_token_variable_start)
        elif instr == Instructions.expand_after:
            with context_mode(self.global_state,
                              ContextMode.absorbing_misc_unexpanded_arguments):
                unexpanded_token = self._get_next_input_token()
            next_tokens = self._process_next_input_token()
            self.replace_on_input_queue(next_tokens)
            self.input_tokens_queue.appendleft(unexpanded_token)
        elif instr in message_instructions:
            # TODO: this is all wrong, these things expect general_text.
            # do like (upper/lower)case does.
            output_tokens.append(first_token)
            self._push_context(ContextMode.awaiting_balanced_text_start)
        elif instr in hyphenation_instructions:
            # TODO: See above.
            output_tokens.append(first_token)
            self._push_context(ContextMode.awaiting_balanced_text_start)
        elif instr in if_instructions:
            self.handle_if(first_token)
        elif instr == Instructions.string:
            with context_mode(self.global_state,
                              ContextMode.absorbing_misc_unexpanded_arguments):
                target_token = self._get_next_input_token()
            string_tokens = []
            # If the target token is a control sequence, then get the chars of
            # its name.
            if target_token.instruction in unexpanded_cs_instructions:
                chars = list(target_token.value['name'])
                escape_char_token = self.get_escape_char_terminal_token(
                    position_like=target_token)
                if escape_char_token is not None:
                    string_tokens += [escape_char_token]
            else:
                char = target_token.value['char']
                chars = [char]
            char_terminal_tokens = [
                make_instruction_token_from_char_cat(
                    c, CatCode.other, position_like=target_token
                )
                for c in chars
            ]
            string_tokens += char_terminal_tokens
            self.replace_on_input_queue(string_tokens)
        elif instr == Instructions.cs_name:
            cs_name_tokens = []
            cs_name_queue = deque()

            while True:
                t = self.pop_or_fill_and_pop(cs_name_queue)
                if t.instruction == Instructions.end_cs_name:
                    break
                cs_name_tokens.append(t)
            chars = [tok.value['char'] for tok in cs_name_tokens]
            cs_name = ''.join(chars)
            cs_token = make_control_sequence_instruction_token(
                cs_name, position_like=first_token)
            # If we expanded such that we got tokens past 'endcsname',
            # put them back on the input queue.
            self.replace_on_input_queue(cs_name_queue)
            # But first comes our shiny new control sequence token.
            self.input_tokens_queue.appendleft(cs_token)
        elif instr in (Instructions.upper_case, Instructions.lower_case):
            case_tokens = []
            while True:
                t = self._get_next_input_token()
                case_tokens.append(t)
                if t.instruction == Instructions.left_brace:
                    with context_mode(self.global_state,
                                      ContextMode.absorbing_misc_unexpanded_arguments):
                        balanced_text_token = self.get_balanced_text_token()
                    case_tokens.append(balanced_text_token)
                    break
            # Check arguments obey the rules of a 'general text'.
            # TODO: Can this be done better with a chunk grabber or
            # something?
            general_text_token = general_text_parser.parse(iter(case_tokens))

            case_funcs_map = {
                Instructions.lower_case: self.global_state.get_lower_case_code,
                Instructions.upper_case: self.global_state.get_upper_case_code,
            }
            case_func = case_funcs_map[instr]

            def get_cased_tok(un_cased_tok):
                if un_cased_tok.value['lex_type'] == char_cat_lex_type:
                    un_cased_char = un_cased_tok.value['char']
                    cased_char = case_func(un_cased_char)
                    if cased_char == chr(0):
                        cased_char = un_cased_char
                    # Note that the category code is not changed.
                    cat = un_cased_tok.value['cat']
                    return make_instruction_token_from_char_cat(
                        cased_char, cat, position_like=un_cased_tok)
                else:
                    return un_cased_tok

            un_cased_toks = general_text_token.value
            cased_toks = list(map(get_cased_tok, un_cased_toks))
            # Put cased tokens back on the queue to read again.
            self.replace_on_input_queue(cased_toks)
        elif instr in explicit_box_instructions:
            # First we read until box specification is finished.
            # Then we will do actual group and scope changes and so on.
            self._push_context(box_context_mode_map[instr])
            # Put the box token on the queue.
            output_tokens.append(first_token)
        # Just some semantic bullshit, stick it on the output queue
        # for the parser to deal with.
        else:
            output_tokens.append(first_token)
        return output_tokens
