from contextlib import contextmanager
import logging
from enum import Enum

from .constants.codes import CatCode
from .constants.instructions import (Instructions,
                                     explicit_box_instructions,
                                     short_hand_def_instructions,
                                     def_instructions,
                                     if_instructions,
                                     message_instructions,
                                     unexpanded_cs_instructions,
                                     hyphenation_instructions)
from .constants.parameters import Parameters
from .tokens import InstructionToken
from .lexer import (is_control_sequence_call, is_char_cat,
                    char_cat_lex_type, control_sequence_lex_type)
from .instructioner import (Instructioner,
                            make_unexpanded_control_sequence_instruction,
                            char_cat_instr_tok)
from .state import Mode, Group
from .macro import substitute_params_with_args
from .parsing.utils import GetBuffer, safe_chunk_grabber
from .parsing import parsing
from .feedback import truncate_list
from .router import short_hand_def_type_to_token_instr
from .utils import UserError


logger = logging.getLogger(__name__)

token_variable_start_instructions = (
    Instructions.token_parameter,
    Instructions.toks_def_token,
    Instructions.toks,
)


command_parser = parsing.command_parser
condition_parser = parsing.get_parser(start='condition_wrap')
general_text_parser = parsing.get_parser(start='general_text')

shorties = short_hand_def_instructions + (
    Instructions.font,
    Instructions.backtick,
)


def stringify_instrs(ts):
    """Represent a sequence of instructions as a sequence of strings. The bit
    about in_chars means that successive characters are represented as a single
    string, which eases reading greatly."""
    ts = truncate_list(ts)
    in_chars = False
    b = ''
    for t in ts:
        if isinstance(t, InstructionToken) and isinstance(t.value, dict) and 'lex_type' in t.value and t.value['lex_type'] == char_cat_lex_type:
            if in_chars:
                b += t.value['char']
            else:
                b = t.value['char']
                in_chars = True
        else:
            if in_chars:
                yield b
                in_chars = False
            if isinstance(t, InstructionToken) and t.instruction in unexpanded_cs_instructions:
                yield f"\\{t.value['name']}"
            elif isinstance(t, InstructionToken) and t.instruction == Instructions.param_number:
                yield f'#{t.value}'
            elif isinstance(t, InstructionToken) and t.instruction in short_hand_def_type_to_token_instr.values():
                yield f'{t.value}'
            elif isinstance(t, InstructionToken):
                yield f'I.{t.instruction.name}'
            else:
                yield t
    if in_chars:
        yield b


def stringify_instr_list(ts):
    """Represent a sequence of instructions as a string."""
    return ' '.join(stringify_instrs(ts))


class ContextMode(Enum):
    normal = 1
    awaiting_balanced_text_start = 2
    awaiting_balanced_text_or_token_variable_start = 7
    awaiting_make_h_box_start = 3
    awaiting_make_v_box_start = 4
    awaiting_make_v_top_start = 5
    # These contexts are not used in practice, because the contextual grabbing
    # can be handled in the same call as the context-initiating instruction is
    # seen.
    # # Inhibited expansion contexts. I have listed the corresponding entry in
    # # the list of cases where expansion is suppressed, in the TeXbook, page
    # # 215.
    # # Entry 2.
    # absorbing_conditional_text = 12
    # # Entry 3.
    # absorbing_macro_arguments = 13
    # # Entry 4.
    # absorbing_new_control_sequence_name = 14
    # # Entry 5, and the latter part of entry 7.
    # absorbing_misc_unexpanded_arguments = 15
    # # Entry 6.
    # absorbing_macro_parameter_text = 16
    # # First part of entry 7.
    # absorbing_macro_replacement_text = 17
    # # Entry 10.
    # absorbing_backtick_argument = 20


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


def get_brace_sign(token):
    if token.instruction == Instructions.left_brace:
        return 1
    elif token.instruction == Instructions.right_brace:
        return -1
    else:
        return 0


class Banisher:

    def __init__(self, instructions, state, reader):
        self.instructions = instructions
        self.state = state
        # The banisher needs the reader because it can execute commands,
        # and one possible command is '\input', which needs to modify the
        # reader.
        self.reader = reader
        # Context is not a TeX concept; it's used when doing this messy bit of
        # parsing.
        self.context_mode_stack = [ContextMode.normal]

    @classmethod
    def from_string(cls, s, state):
        instrs = Instructioner.from_string(s, state.codes.get_cat_code)
        return cls(instrs, state, instrs.lexer.reader)

    def _push_context(self, context_mode):
        logger.info(f'Entering {context_mode}')
        self.context_mode_stack.append(context_mode)

    def _pop_context(self):
        logger.info(f'Exiting {self.context_mode}')
        return self.context_mode_stack.pop()

    @property
    def context_mode(self):
        return self.context_mode_stack[-1]

    def advance_to_end(self):
        while True:
            try:
                ts = self.get_next_output_list()
            except EOFError:
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
        # previous one has executed. For example, Changing the escape
        # character, then calling \string on a control sequence.
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

    def _get_balanced_text_token(self):
        b_tokens = []
        brace_level = 1
        while True:
            token = self.instructions.next_unexpanded()
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

    def _handle_macro(self, first_token):
        params = first_token.value['parameter_text']
        replace_text = first_token.value['replacement_text']

        def tokens_equal(t, u):
            if t.value['lex_type'] != u.value['lex_type']:
                return False
            if t.value['lex_type'] == char_cat_lex_type:
                attr_keys = ('char', 'cat')
            elif t.value['lex_type'] == control_sequence_lex_type:
                attr_keys = ('name',)
            else:
                raise ValueError(f'Value does not look like a token: {t}')
            return all(t.value[k] == u.value[k] for k in attr_keys)
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
                next_token = self.instructions.next_unexpanded()
                if not tokens_equal(p_t, next_token):
                    raise Exception
                continue
            delim_toks = p_t.value['delim_tokens']
            if p_t.instruction == Instructions.undelimited_param:
                assert not delim_toks
                next_token = self.instructions.next_unexpanded()
                if next_token.instruction == Instructions.left_brace:
                    b_tok = self._get_balanced_text_token()
                    arg_toks.extend(b_tok.value)
                else:
                    arg_toks.append(next_token)
            elif p_t.instruction == Instructions.delimited_param:
                # To be finished, we must be balanced brace-wise.
                brace_level = 0
                while True:
                    next_token = self.instructions.next_unexpanded()
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

        if len(replace_text) > 1:
            logger.info(f"Expanding macro \"{first_token.value['name']}\" to \"{stringify_instr_list(replace_text)}\"")
            for i, arg in enumerate(arguments):
                logger.info(f"Macro argument {i + 1}: \"{stringify_instr_list(arg)}\"")
        tokens = substitute_params_with_args(replace_text, arguments)
        # Note that these tokens might themselves need more expansion.
        return tokens, []

    def _handle_if(self, first_token):
        logger.debug(f'Handling condition "{first_token.instruction.name} …"')
        with safe_chunk_grabber(self, condition_parser,
                                initial=[first_token]) as condition_grabber:
            if_token = next(condition_grabber)
        i_block_to_pick = self.state.evaluate_if_token_to_block(if_token)
        # Now get the body of the condition text.

        def get_condition_sign(token):
            if not is_control_sequence_call(token):
                return 0
            name = token.value['name']

            if self.state.router.name_means_start_condition(name):
                return 1
            elif self.state.router.name_means_end_condition(name):
                return -1
            else:
                return 0

        def is_condition_delimiter(token):
            if not is_control_sequence_call(token):
                return 0
            name = token.value['name']
            return self.state.router.name_means_delimit_condition(name)

        nr_conditions = 1
        i_block = 0
        not_skipped_tokens = []
        for t in self.instructions.iter_unexpanded():
            # Keep track of nested conditions.
            nr_conditions += get_condition_sign(t)

            # If we get the terminal \fi, return the gathered tokens.
            if nr_conditions == 0:
                break
            # If we are at the pertinent if-nesting level, then track
            # a condition block delimiter.
            elif nr_conditions == 1 and is_condition_delimiter(t):
                i_block += 1
            # If we're in the block the condition says we should pick,
            # include the token.
            elif i_block == i_block_to_pick:
                not_skipped_tokens.append(t)
            # Otherwise we are skipping tokens.
            else:
                pass

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
            if self.state.mode == Mode.vertical:
                box_group = Group.adjusted_h_box
            else:
                box_group = Group.h_box
        self.state.push_group(box_group)
        # (By later context, can tell this means a new scope.)
        self.state.push_new_scope()

        # Enter relevant mode.
        if self.context_mode in (ContextMode.awaiting_make_v_box_start,
                                 ContextMode.awaiting_make_v_top_start):
            mode = Mode.internal_vertical
        elif self.context_mode == ContextMode.awaiting_make_h_box_start:
            mode = Mode.restricted_horizontal
        # TODO: Use context manager for mode.
        outer_mode_depth = self.state.mode_depth
        self.state.push_mode(mode)

        # Done with the context.
        self._pop_context()

        box_parser = command_parser
        with safe_chunk_grabber(self, parser=box_parser) as chunk_grabber:
            # Matching right brace should trigger EndOfSubExecutor and return.
            self.state.execute_command_tokens(chunk_grabber,
                                              banisher=self,
                                              reader=self.reader)

        # [After ending the group, then TeX] packages the hbox (using the
        # size that was saved on the stack), and completes the setbox
        # command, returning to the mode it was in at the time of the
        # setbox.
        # Note: we don't do anything about packaging the box here; our purpose
        # is only to get the box contents, because this is context sensitive.
        # Packaging the box involves the box specification, which will be known
        # after parsing.
        layout_list = self.state.return_to_mode(outer_mode_depth)
        material_token = InstructionToken(
            mode_material_instruction_map[mode],
            value=layout_list,
            position_like=first_token
        )
        # Put the LEFT_BRACE on the output queue, and the box material.
        return [], [first_token, material_token]

    def _handle_def(self, first_token):
        # Get name of macro.
        cs_name_token = self.instructions.next_unexpanded()

        # Get parameter text.
        param_instrs = []
        while True:
            instr = self.instructions.next_unexpanded()
            if instr.instruction == Instructions.left_brace:
                left_brace_instr = instr
                break
            param_instrs.append(instr)

        parameter_text_token = InstructionToken(
            Instructions.parameter_text,
            value=param_instrs,
            position_like=first_token,
        )

        # Get the replacement text.
        # TODO: this is where expanded-def will be differentiated from
        # normal-def.
        replacement_text_token = self._get_balanced_text_token()

        # Add the def token, macro name, parameter text, left brace and
        # replacement text to the output queue.
        output = [first_token, cs_name_token, parameter_text_token,
                  left_brace_instr, replacement_text_token]
        return [], output

    def _handle_let(self, first_token):
        cs_name_token = self.instructions.next_unexpanded()

        # Parse the arguments of LET manually, because the target token can be
        # basically anything, and this would be a pain to tell the parser.

        let_arguments = []
        let_arguments.append(self.instructions.next_unexpanded())
        # If we find an equals, ignore that and read again.
        if let_arguments[-1].instruction == Instructions.equals:
            let_arguments.append(self.instructions.next_unexpanded())
        # If we find a space, ignore that and read again.
        if let_arguments[-1].instruction == Instructions.space:
            let_arguments.append(self.instructions.next_unexpanded())
        # Now we know the last instruction should be the let target.
        let_preamble, let_target_tok = let_arguments[:-1], let_arguments[-1]

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
            logger.info(f'Adding context due to {first_token.instruction}')
            self._push_context(ContextMode.awaiting_balanced_text_start)
            general_text_token = next(general_text_grabber)

        case_funcs_map = {
            Instructions.lower_case: self.state.codes.get_lower_case_code,
            Instructions.upper_case: self.state.codes.get_upper_case_code,
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
        target_token = self.instructions.next_unexpanded()
        logger.debug(f'Doing "string" instruction to {target_token}')
        escape_char_code = self.state.parameters.get(Parameters.escape_char)

        # If a control sequence token appears, its \string expansion consists
        # of the control sequence name (including \escapechar as an escape
        # character, if the control sequence isn't simply an active character).
        if target_token.instruction in unexpanded_cs_instructions:
            chars = []
            if escape_char_code >= 0:
                chars.append(chr(escape_char_code))
            chars += list(target_token.value['name'])
        else:
            chars = [target_token.value['char']]

        output = []
        for c in chars:
            # Each character in this token list automatically gets category
            # code [other], including the backslash that \string inserts to
            # represent an escape character. However, category [space] will be
            # assigned to the character ']' if it somehow sneaks into the name
            # of a control sequence.
            if c == ' ':
                cat = CatCode.space
            else:
                cat = CatCode.other
            t = char_cat_instr_tok(c, cat, position_like=target_token)
            output.append(t)

        return [], output

    def _handle_cs_name(self, first_token):
        chars = []

        out_queue = GetBuffer(getter=self.get_next_output_list)
        for t in out_queue:
            if t.instruction == Instructions.end_cs_name:
                break
            if is_char_cat(t):
                chars.append(t.value['char'])
            else:
                raise UserError(f'Found non-character inside '
                                f'\csname ... \endcsname block: {t}')

        cs_name = ''.join(chars)
        cs_token = make_unexpanded_control_sequence_instruction(
            cs_name, position_like=first_token)
        # Put our shiny new control sequence token on the input,
        # along with any spare tokens from the expansion
        return [cs_token] + list(out_queue.queue), []

    def _expand_next_input_token(self):
        first_token = self.instructions.next_expanded()
        instr = first_token.instruction

        # A user control sequence.
        if instr == Instructions.macro:
            return self._handle_macro(first_token)
        # Waiting to absorb a balanced text, and see a "{".
        elif (self.context_mode in (ContextMode.awaiting_balanced_text_start,
                                    ContextMode.awaiting_balanced_text_or_token_variable_start)
                and instr == Instructions.left_brace):
            logger.debug('Grabbing balanced text')
            bal_tok = self._get_balanced_text_token()
            # Done getting balanced text, so pop context.
            self._pop_context()
            # Put the LEFT_BRACE and the balanced text on the output queue.
            return [], [first_token, bal_tok]
        # Waiting to absorb either a balanced text, or a token variable, and
        # see a token variable.
        elif (self.context_mode == ContextMode.awaiting_balanced_text_or_token_variable_start and
              instr in token_variable_start_instructions):
            logger.debug('Passing on token variable')
            # We can handle this sort of token-list argument in the parser; we
            # only had this context in case a balanced text needed to be got,
            # so we can just pop the context and put the token on the output
            # queue.
            self._pop_context()
            return [], [first_token]
        # Waiting to absorb some box contents, and see a "{".
        elif (self.context_mode in box_context_mode_map.values() and
                instr == Instructions.left_brace):
            logger.debug(f'Grabbing box after {self.context_mode}')
            return self._handle_making_box(first_token)
        # Such as \chardef, or \font, or a "`".
        elif instr in shorties:
            # Add an unexpanded control sequence as an instruction token to the
            # output.
            logger.debug(f'Grabbing {instr} argument')
            return [], [first_token, self.instructions.next_unexpanded()]
        # \afterassignment, or \aftergroup.
        elif instr in (Instructions.after_assignment,
                       Instructions.after_group):
            # Add an arbitrary token as an instruction token to the output.
            logger.debug(f'Grabbing {instr} argument')
            target_token = self.instructions.next_unexpanded()
            target_token_instr = InstructionToken(
                Instructions.let_target,
                value=target_token,
                position_like=target_token,
            )
            return [], [first_token, target_token_instr]
        # Such as \def.
        elif instr in def_instructions:
            logger.debug(f'Grabbing macro definition')
            return self._handle_def(first_token)
        # \let.
        elif instr == Instructions.let:
            logger.debug(f'Grabbing let arguments')
            return self._handle_let(first_token)
        # Such as \toks.
        elif instr in token_variable_start_instructions:
            logger.info(f'Adding context due to {instr}')
            self._push_context(ContextMode.awaiting_balanced_text_or_token_variable_start)
            return [], [first_token]
        # \expandafter.
        elif instr == Instructions.expand_after:
            logger.debug(f'Evaluating expand-after')
            # Read a token without expansion.
            unexpanded_token = self.instructions.next_unexpanded()
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
            logger.info(f'Adding context due to {instr}')
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
            logger.debug(f'Doing "cs-name" instruction')
            return self._handle_cs_name(first_token)
        # \upper.
        elif instr in (Instructions.upper_case, Instructions.lower_case):
            logger.debug(f'Doing "{instr.name}" instruction')
            return self._handle_change_case(first_token)
        # Such as \hbox.
        elif instr in explicit_box_instructions:
            logger.info(f'Adding context due to {instr}')
            # Read until box specification is finished,
            # then we will do actual group and scope changes and so on.
            self._push_context(box_context_mode_map[instr])
            return [], [first_token]
        # Just some semantic bullshit, stick it on the output queue
        # for the parser to deal with.
        else:
            logger.debug(f'Passing on instruction "{instr.name}"')
            return [], [first_token]
