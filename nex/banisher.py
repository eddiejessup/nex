from contextlib import contextmanager
import logging
from enum import Enum

from .tokens import InstructionToken
from .reader import EndOfFile
from .lexer import (is_control_sequence_call, is_char_cat,
                    char_cat_lex_type, control_sequence_lex_type)
from .codes import CatCode
from .instructions import (Instructions,
                           explicit_box_instructions,
                           short_hand_def_instructions,
                           def_instructions,
                           if_instructions,
                           message_instructions,
                           unexpanded_cs_instructions,
                           hyphenation_instructions)
from .tex_parameters import Parameters
from .instructioner import (Instructioner,
                            make_unexpanded_control_sequence_instruction,
                            char_cat_instr_tok)
from .state import Mode, Group
from .expander import substitute_params_with_args
from .if_executor import execute_condition
from .parsing.utils import GetBuffer, safe_chunk_grabber
from .parsing.command_parser import command_parser
from .parsing.condition_parser import condition_parser
from .parsing.general_text_parser import general_text_parser


logger = logging.getLogger(__name__)

token_variable_start_instructions = (
    Instructions.token_parameter,
    Instructions.toks_def_token,
    Instructions.toks,
)


class BanisherError(Exception):
    pass


class ContextMode(Enum):
    normal = 1
    awaiting_balanced_text_start = 2
    awaiting_balanced_text_or_token_variable_start = 7
    awaiting_make_h_box_start = 3
    awaiting_make_v_box_start = 4
    awaiting_make_v_top_start = 5
    # Inhibited expansion contexts. I have listed the corresponding entry in
    # the list of cases where expansion is suppressed, in the TeXbook, page
    # 215.
    # Entry 2.
    absorbing_conditional_text = 12
    # Entry 3.
    absorbing_macro_arguments = 13
    # Entry 4.
    absorbing_new_control_sequence_name = 14
    # Entry 5, and the latter part of entry 7.
    absorbing_misc_unexpanded_arguments = 15
    # Entry 6.
    absorbing_macro_parameter_text = 16
    # First part of entry 7.
    absorbing_macro_replacement_text = 17
    # Entry 10.
    absorbing_backtick_argument = 20


@contextmanager
def context_mode(banisher, context_mode):
    banisher._push_context(context_mode)
    yield
    banisher._pop_context()


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


def get_balanced_text_token(tokens):
    b_tokens = []
    brace_level = 1
    while True:
        token = next(tokens)
        b_tokens.append(token)
        brace_level += get_brace_sign(token)
        if brace_level == 0:
            break
    balanced_text = InstructionToken(
        Instructions.balanced_text_and_right_brace,
        value=b_tokens[:-1],
        position_like=b_tokens[0]
    )
    return balanced_text


def get_macro_arguments(params, tokens):
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
        if p_t.instruction not in (Instructions.undelimited_param,
                                   Instructions.delimited_param):
            # We should only see non-parameters in the parameter list,
            # if they are text preceding the parameters proper. See
            # the comments in `parse_parameter_text` for further
            # details.
            # We just swallow up these tokens.
            assert not arguments
            next_token = next(tokens)
            if not tokens_equal(p_t, next_token):
                import pdb; pdb.set_trace()
                raise Exception
            continue
        delim_toks = p_t.value['delim_tokens']
        if p_t.instruction == Instructions.undelimited_param:
            assert not delim_toks
            next_token = next(tokens)
            if next_token.instruction == Instructions.left_brace:
                b_tok = get_balanced_text_token(tokens)
                arg_toks.extend(b_tok.value)
            else:
                arg_toks.append(next_token)
        elif p_t.instruction == Instructions.delimited_param:
            # To be finished, we must be balanced brace-wise.
            brace_level = 0
            while True:
                next_token = next(tokens)
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
    return arguments


def get_conditional_text(instructions, i_block_to_pick):
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
                token.value['name'] in delimit_condition_block_names)

    nr_conditions = 1
    i_block = 0
    not_skipped_instructions = []
    for t in instructions:
        # Keep track of nested conditions.
        nr_conditions += get_condition_sign(t)

        # If we get the terminal \fi, return the gathered tokens.
        if nr_conditions == 0:
            return not_skipped_instructions
        # If we are at the pertinent if-nesting level, then
        # a condition block delimiter should be kept track of.
        elif nr_conditions == 1 and is_condition_delimiter(t):
            i_block += 1
        # if we're in the block the condition says we should pick,
        # include token.
        elif i_block == i_block_to_pick:
            not_skipped_instructions.append(t)
        # Otherwise we are skipping tokens.
        else:
            pass


def get_parameter_instrs(instructions):
    param_instrs = []
    while True:
        instr = next(instructions)
        if instr.instruction == Instructions.left_brace:
            left_brace_instr = instr
            return param_instrs, left_brace_instr
        param_instrs.append(instr)


def get_let_arguments(instructions):
    let_arguments = []
    let_arguments.append(next(instructions))
    # If we find an equals, ignore that and read again.
    if let_arguments[-1].instruction == Instructions.equals:
        let_arguments.append(next(instructions))
    # If we find a space, ignore that and read again.
    if let_arguments[-1].instruction == Instructions.space:
        let_arguments.append(next(instructions))
    # Now we know the last instruction should be the let target.
    preamble_tokens, let_target = let_arguments[:-1], let_arguments[-1]
    return preamble_tokens, let_target


def get_string_instr_repr(target_token, escape_char_code):
    # If a control sequence token appears, its \string expansion
    # consists of the control sequence name (including \escapechar as
    # an escape character, if the control sequence isn't simply an
    # active character).
    if target_token.instruction in unexpanded_cs_instructions:
        chars = []
        if escape_char_code >= 0:
            chars.append(chr(escape_char_code))
        chars += list(target_token.value['name'])
    else:
        chars = [target_token.value['char']]

    toks = []
    for c in chars:
        # Each character in this token list automatically gets category code
        # [other], including the backslash that \string inserts to represent an
        # escape character. However, category [space] will be assigned to the
        # character ']' if it somehow sneaks into the name of a control
        # sequence.
        if c == ' ':
            cat = CatCode.space
        else:
            cat = CatCode.other
        t = char_cat_instr_tok(c, cat, position_like=target_token)
        toks.append(t)
    return toks


class Banisher:

    def __init__(self, instructions, state, reader):
        self.instructions = instructions
        self.global_state = state
        # The banisher needs the reader because it can execute commands,
        # and one possible command is '\input', which needs to modify the
        # reader.
        self.reader = reader
        # Context is not a TeX concept; it's used when doing this messy bit of
        # parsing.
        self.context_mode_stack = []

    @classmethod
    def from_string(cls, s, state):
        instrs = Instructioner.from_string(s, state.codes.get_cat_code)
        return cls(instrs, state, instrs.lexer.reader)

    def _push_context(self, context_mode):
        self.context_mode_stack.append(context_mode)

    def _pop_context(self):
        if self.context_mode_stack:
            return self.context_mode_stack.pop()

    @property
    def context_mode(self):
        if self.context_mode_stack:
            return self.context_mode_stack[-1]
        else:
            return ContextMode.normal

    @property
    def _expanding_control_sequences(self):
        return self.context_mode in expanding_context_modes

    def advance_to_end(self):
        while True:
            try:
                ts = self.get_next_output_list()
            except EndOfFile:
                return
            for t in ts:
                yield t

    def get_next_output_list(self):
        while True:
            outputs = self._iterate()
            if outputs is not None:
                return outputs

    def _iterate(self):
        # TODO: Check what happens when we try to parse tokens too far in one
        # chunk, and bleed into another chunk that only makes sense once the
        # previous one has executed. For example, defining a new macro, then
        # calling that macro. This function might have side effects on the
        # state, and the instructions.
        next_inputs, next_outputs = self._expand_next_input_token()
        if next_inputs and next_outputs:
            raise Exception
        if next_inputs:
            self.instructions.replace_tokens_on_input(next_inputs)
        elif next_outputs:
            return next_outputs
        else:
            # The output of a command could *be* an empty list. For
            # example, a condition might return nothing in some branches.
            pass

    def _handle_macro(self, first_token):
        params = first_token.value['parameter_text']
        replace_text = first_token.value['replacement_text']
        arguments = get_macro_arguments(params, tokens=self.instructions)
        tokens = substitute_params_with_args(replace_text, arguments)
        # Note that these tokens might themselves need more expansion.
        return tokens, []

    def _handle_if(self, first_token):
        # TODO: Can we, and should we, do this grab-then-execute logic with
        # some kind of Executor-like class?
        with safe_chunk_grabber(self, condition_parser,
                                initial=[first_token]) as condition_grabber:
            condition_token = next(condition_grabber)
        outcome = execute_condition(condition_token, self.global_state)

        # TODO: Move inside executor? Not sure.
        if first_token.instruction == Instructions.if_case:
            i_block_to_pick = outcome
        else:
            i_block_to_pick = 0 if outcome else 1

        # Now get the body of the condition text.
        not_skipped_tokens = get_conditional_text(self.instructions,
                                                  i_block_to_pick)
        return not_skipped_tokens, []

    def _handle_making_box(self, first_token):
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
        with safe_chunk_grabber(self, parser=box_parser) as chunk_grabber:
            # Matching right brace should trigger EndOfSubExecutor and return.
            self.global_state.execute_commands(chunk_grabber,
                                               banisher=self,
                                               reader=self.reader)

        # [After ending the group, then TeX] packages the hbox (using the
        # size that was saved on the stack), and completes the setbox
        # command, returning to the mode it was in at the time of the
        # setbox.
        layout_list = self.global_state.pop_mode()
        material_token = InstructionToken(
            mode_material_instruction_map[mode],
            value=layout_list,
            position_like=first_token
        )
        # Put the LEFT_BRACE on the output queue, and the box material.
        return [], [first_token, material_token]

    def _handle_def(self, first_token):
        # Get name of macro.
        cs_name_token = next(self.instructions)

        # Get parameter text.
        parameter_instrs, left_brace_token = get_parameter_instrs(self.instructions)
        parameter_text_token = InstructionToken(
            Instructions.parameter_text,
            value=parameter_instrs,
            position_like=first_token,
        )

        # Get the replacement text.
        # TODO: this is where expanded-def will be differentiated from
        # normal-def.
        replacement_text_token = get_balanced_text_token(self.instructions)

        # Add the def token, macro name, parameter text, left brace and
        # replacement text to the output queue.
        output = [first_token, cs_name_token, parameter_text_token,
                  left_brace_token, replacement_text_token]
        return [], output

    def _handle_let(self, first_token):
        cs_name_token = next(self.instructions)

        # Parse the arguments of LET manually, because the target token can be
        # basically anything, and this would be a pain to tell the parser.
        let_preamble, let_target_tok = get_let_arguments(self.instructions)
        let_target_instr = InstructionToken(
            Instructions.let_target,
            value=let_target_tok,
            position_like=first_token
        )
        output = ([first_token, cs_name_token] +
                  let_preamble + [let_target_instr])
        return [], output

    def _handle_change_case(self, first_token):
        # Get the succeeding general text token for processing.
        with safe_chunk_grabber(self,
                                general_text_parser) as general_text_grabber:
            with context_mode(self, ContextMode.awaiting_balanced_text_start):
                general_text_token = next(general_text_grabber)

        case_funcs_map = {
            Instructions.lower_case: self.global_state.codes.get_lower_case_code,
            Instructions.upper_case: self.global_state.codes.get_upper_case_code,
        }
        case_func = case_funcs_map[first_token.instruction]

        def get_cased_tok(un_cased_tok):
            if un_cased_tok.value['lex_type'] == char_cat_lex_type:
                un_cased_char = un_cased_tok.value['char']
                # Conversion to uppercase means that a character is replaced by
                # its \uccode value, unless the \uccode value is zero (when no
                # change is made). Conversion to lowercase is similar, using
                # the \lccode.
                cased_char = case_func(un_cased_char)
                if cased_char == chr(0):
                    cased_char = un_cased_char
                # The category codes aren't changed.
                cat = un_cased_tok.value['cat']
                return char_cat_instr_tok(cased_char, cat,
                                          position_like=un_cased_tok)
            else:
                return un_cased_tok

        cased_tokens = list(map(get_cased_tok, general_text_token.value))
        return cased_tokens, []

    def _handle_string(self, first_token):
        # TeX first reads the [next] token without expansion.
        target_token = next(self.instructions)
        escape_char_code = self.global_state.parameters.get(Parameters.escape_char)
        return [], get_string_instr_repr(target_token, escape_char_code)

    def _handle_cs_name(self, first_token):
        chars = []

        out_queue = GetBuffer(getter=self.get_next_output_list)
        for t in out_queue:
            if t.instruction == Instructions.end_cs_name:
                break
            if is_char_cat(t):
                chars.append(t.value['char'])
            else:
                raise BanisherError(f'Found non-character inside '
                                    f'\csname ... \endcsname block: {t}')

        cs_name = ''.join(chars)
        cs_token = make_unexpanded_control_sequence_instruction(
            cs_name, position_like=first_token)
        # Put our shiny new control sequence token on the input,
        # along with any spare tokens from the expansion
        return [cs_token] + list(out_queue.queue), []

    def _expand_next_input_token(self):
        first_token = next(self.instructions)

        # If the token is an unexpanded control sequence call, and expansion is
        # not suppressed, then we must resolve the call:
        # - A user control sequence will become a macro instruction token.
        # - A \let character will become its character instruction token.
        # - A primitive control sequence will become its instruction token.
        # NOTE: I've made this mistake twice now: we can't make this resolution
        # into a two-call process, where we resolve the token, put the resolved
        # token on the input, then handle it in the next call. This is because,
        # for example, \expandafter expects a single call to this method to do
        # resolution and actual expansion. Basically this method has certain
        # responsibilites to do a certain amount to a token in each call.
        if (self._expanding_control_sequences and
                first_token.instruction in unexpanded_cs_instructions):
            name = first_token.value['name']
            first_token = self.global_state.router.lookup_control_sequence(
                name, position_like=first_token)

        instr = first_token.instruction

        # A user control sequence.
        if instr == Instructions.macro:
            return self._handle_macro(first_token)
        # Waiting to absorb a balanced text, and see a "{".
        elif (self.context_mode in (ContextMode.awaiting_balanced_text_start,
                                    ContextMode.awaiting_balanced_text_or_token_variable_start)
                and instr == Instructions.left_brace):
            bal_tok = get_balanced_text_token(self.instructions)
            # Done getting balanced text, so pop context.
            self._pop_context()
            # Put the LEFT_BRACE and the balanced text on the output queue.
            return [], [first_token, bal_tok]
        # Waiting to absorb either a balanced text, or a token variable, and
        # see a token variable.
        elif (self.context_mode == ContextMode.awaiting_balanced_text_or_token_variable_start and
              instr in token_variable_start_instructions):
            # We can handle this sort of token-list argument in the parser; we
            # only had this context in case a balanced text needed to be got,
            # so we can just pop the context and put the token on the output
            # queue.
            self._pop_context()
            return [], [first_token]
        # Waiting to absorb some box contents, and see a "{".
        elif (self.context_mode in box_context_mode_map.values() and
                instr == Instructions.left_brace):
            return self._handle_making_box(first_token)
        # Such as \chardef, or \font, or a "`".
        elif (instr in short_hand_def_instructions +
                (Instructions.font, Instructions.backtick)):
            # Add an unexpanded control sequence as an instruction token to the
            # output.
            return [], [first_token, next(self.instructions)]
        # Such as \def.
        elif instr in def_instructions:
            return self._handle_def(first_token)
        # \let.
        elif instr == Instructions.let:
            return self._handle_let(first_token)
        # Such as \toks.
        elif instr in token_variable_start_instructions:
            self._push_context(ContextMode.awaiting_balanced_text_or_token_variable_start)
            return [], [first_token]
        # \expandafter.
        elif instr == Instructions.expand_after:
            # Read a token without expansion.
            unexpanded_token = next(self.instructions)
            # Then get the next token *with* expansion.
            next_input_tokens, next_output_tokens = self._expand_next_input_token()
            # Order doesn't matter because only one should have elements anyway.
            next_tokens = next_input_tokens + next_output_tokens
            # Then replace the first unexpanded token, and results of second
            # expansion, on the input queue.
            replace = [unexpanded_token] + next_tokens
            return replace, []
        # Such as \message.
        elif instr in message_instructions + hyphenation_instructions:
            # TODO: I think the balanced text contents *are* expanded, at least
            # for \[err]message. Unlike upper/lower-case. Not sure how best to
            # implement this. I guess the same way \edef works, when that's
            # implemented.
            self._push_context(ContextMode.awaiting_balanced_text_start)
            return [], [first_token]
        # Such as \ifnum.
        elif instr in if_instructions:
            return self._handle_if(first_token)
        # \string.
        elif instr == Instructions.string:
            return self._handle_string(first_token)
        # \csname.
        elif instr == Instructions.cs_name:
            return self._handle_cs_name(first_token)
        # \upper.
        elif instr in (Instructions.upper_case, Instructions.lower_case):
            return self._handle_change_case(first_token)
        # Such as \hbox.
        elif instr in explicit_box_instructions:
            # Read until box specification is finished,
            # then we will do actual group and scope changes and so on.
            self._push_context(box_context_mode_map[instr])
            return [], [first_token]
        # Just some semantic bullshit, stick it on the output queue
        # for the parser to deal with.
        else:
            return [], [first_token]
