from collections import deque
from enum import Enum
from string import ascii_letters
import logging

from .constants.codes import CatCode
from .constants.parameters import param_to_instr
from .constants.specials import special_to_instr
from .constants.instructions import (Instructions, if_instructions,
                                     unexpanded_cs_instructions)
from .constants import control_sequences
from .tokens import InstructionToken, BaseToken
from .utils import get_unique_id
from .lexer import (Lexer, make_char_cat_lex_token,
                    control_sequence_lex_type, char_cat_lex_type)
from .macro import parse_replacement_text, parse_parameter_text


logger = logging.getLogger(__name__)


short_hand_def_type_to_token_instr = {
    Instructions.char_def.value: Instructions.char_def_token,
    Instructions.math_char_def.value: Instructions.math_char_def_token,
    Instructions.count_def.value: Instructions.count_def_token,
    Instructions.dimen_def.value: Instructions.dimen_def_token,
    Instructions.skip_def.value: Instructions.skip_def_token,
    Instructions.mu_skip_def.value: Instructions.mu_skip_def_token,
    Instructions.toks_def.value: Instructions.toks_def_token,
    Instructions.font.value: Instructions.font_def_token,
}


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

non_active_letters_map = {
    'a': Instructions.non_active_uncased_a,
    'b': Instructions.non_active_uncased_b,
    'c': Instructions.non_active_uncased_c,
    'd': Instructions.non_active_uncased_d,
    'e': Instructions.non_active_uncased_e,
    'f': Instructions.non_active_uncased_f,
    'g': Instructions.non_active_uncased_g,
    'h': Instructions.non_active_uncased_h,
    'i': Instructions.non_active_uncased_i,
    'j': Instructions.non_active_uncased_j,
    'k': Instructions.non_active_uncased_k,
    'l': Instructions.non_active_uncased_l,
    'm': Instructions.non_active_uncased_m,
    'n': Instructions.non_active_uncased_n,
    'o': Instructions.non_active_uncased_o,
    'p': Instructions.non_active_uncased_p,
    'q': Instructions.non_active_uncased_q,
    'r': Instructions.non_active_uncased_r,
    's': Instructions.non_active_uncased_s,
    't': Instructions.non_active_uncased_t,
    'u': Instructions.non_active_uncased_u,
    'v': Instructions.non_active_uncased_v,
    'w': Instructions.non_active_uncased_w,
    'x': Instructions.non_active_uncased_x,
    'y': Instructions.non_active_uncased_y,
    'z': Instructions.non_active_uncased_z,
    'A': Instructions.non_active_uncased_a,
    'B': Instructions.non_active_uncased_b,
    'C': Instructions.non_active_uncased_c,
    'D': Instructions.non_active_uncased_d,
    'E': Instructions.non_active_uncased_e,
    'F': Instructions.non_active_uncased_f,
    'G': Instructions.non_active_uncased_g,
    'H': Instructions.non_active_uncased_h,
    'I': Instructions.non_active_uncased_i,
    'J': Instructions.non_active_uncased_j,
    'K': Instructions.non_active_uncased_k,
    'L': Instructions.non_active_uncased_l,
    'M': Instructions.non_active_uncased_m,
    'N': Instructions.non_active_uncased_n,
    'O': Instructions.non_active_uncased_o,
    'P': Instructions.non_active_uncased_p,
    'Q': Instructions.non_active_uncased_q,
    'R': Instructions.non_active_uncased_r,
    'S': Instructions.non_active_uncased_s,
    'T': Instructions.non_active_uncased_t,
    'U': Instructions.non_active_uncased_u,
    'V': Instructions.non_active_uncased_v,
    'W': Instructions.non_active_uncased_w,
    'X': Instructions.non_active_uncased_x,
    'Y': Instructions.non_active_uncased_y,
    'Z': Instructions.non_active_uncased_z,
}

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
        raise ValueError(f'Confused by char-cat pair: ({char}, {cat})')


def make_char_cat_pair_instruction_token(char_cat_lex_token):
    v = char_cat_lex_token.value
    char, cat = v['char'], v['cat']
    instruction = get_char_cat_pair_instruction(char, cat)
    value = char_cat_lex_token.value
    value['lex_type'] = char_cat_lex_token.type
    token = InstructionToken(
        instruction,
        value=value,
        position_like=char_cat_lex_token
    )
    return token


def make_parameter_control_sequence_instruction(name, parameter, instruction):
    instr_tok = make_primitive_control_sequence_instruction(name, instruction)
    # This is what is used to look up the parameter value. The  'name' just
    # records the name of the control sequence used to refer to this parameter.
    instr_tok.value['parameter'] = parameter
    return instr_tok


def make_special_control_sequence_instruction(name, special, instruction):
    instr_tok = make_primitive_control_sequence_instruction(name, instruction)
    # This is what is used to look up the special value. The  'name' just
    # records the name of the control sequence used to refer to this special.
    instr_tok.value['special'] = special
    return instr_tok


def make_primitive_control_sequence_instruction(name, instruction):
    return InstructionToken(
        instruction,
        value={'name': name, 'lex_type': control_sequence_lex_type},
        line_nr='abstract'
    )


def make_unexpanded_control_sequence_instruction(name, position_like=None):
    if len(name) == 1:
        instruction = Instructions.unexpanded_control_symbol
    else:
        instruction = Instructions.unexpanded_control_word
    return InstructionToken(
        instruction,
        value={'name': name, 'lex_type': control_sequence_lex_type},
        position_like=position_like
    )


def char_cat_instr_tok(char, cat, *pos_args, **pos_kwargs):
    """Utility function to make a terminal char-cat token straight from a pair.
    """
    lex_token = make_char_cat_lex_token(char, cat, *pos_args, **pos_kwargs)
    return make_char_cat_pair_instruction_token(lex_token)


def lex_token_to_instruction_token(lex_token):
    # If we have a char-cat pair, we must type it to its terminal version,
    if lex_token.type == char_cat_lex_type:
        return make_char_cat_pair_instruction_token(lex_token)
    elif lex_token.type == control_sequence_lex_type:
        return make_unexpanded_control_sequence_instruction(
            lex_token.value, position_like=lex_token)
    # Aren't any other types of lexed tokens.
    else:
        raise Exception


def make_macro_token(name, replacement_text, parameter_text,
                     def_type=None, prefixes=None):
    if prefixes is None:
        prefixes = set()
    return InstructionToken(
        Instructions.macro,
        value={'name': name,
               'prefixes': prefixes,
               'replacement_text': parse_replacement_text(replacement_text),
               'parameter_text': parse_parameter_text(parameter_text),
               'def_type': def_type,
               'lex_type': control_sequence_lex_type},
        line_nr='abstract',
    )


class NoSuchControlSequence(Exception):

    def __init__(self, name):
        self.name = name


class ControlSequenceType(Enum):
    macro = 1
    let_character = 2
    parameter = 3
    primitive = 4
    font = 5
    special = 6


class RouteToken(BaseToken):

    def __init__(self, type_, value):
        if type_ not in ControlSequenceType:
            raise ValueError('Route token {type_} not a ControlSequenceType')
        super().__init__(type_, value)


class CSRouter:

    def __init__(self,
                 param_control_sequences,
                 special_control_sequences,
                 primitive_control_sequences,
                 enclosing_scope=None):
        self.control_sequences = {}
        self.macros = {}
        self.let_chars = {}
        self.parameters = {}
        self.specials = {}
        self.primitives = {}
        self.font_ids = {}
        self.enclosing_scope = enclosing_scope

        for name, tpl in param_control_sequences.items():
            parameter, instr = tpl
            self._set_parameter(name, parameter, instr)
        for name, tpl in special_control_sequences.items():
            special, instr = tpl
            self._set_special(name, special, instr)
        for name, instruction in primitive_control_sequences.items():
            self._set_primitive(name, instruction)

    @classmethod
    def default_initial(cls):
        # Router needs a map from a control sequence name, to the parameter and
        # the instruction type of the parameter (integer, dimen and so on).
        params = {
            n: (p, param_to_instr[p])
            for n, p in control_sequences.param_control_sequences.items()
        }
        specials = {
            n: (p, special_to_instr[p])
            for n, p in control_sequences.special_control_sequences.items()
        }
        primitives = control_sequences.primitive_control_sequences
        return cls(
            param_control_sequences=params,
            special_control_sequences=specials,
            primitive_control_sequences=primitives,
            enclosing_scope=None)

    @classmethod
    def default_local(cls, enclosing_scope):
        return cls(param_control_sequences={},
                   special_control_sequences={},
                   primitive_control_sequences={},
                   enclosing_scope=enclosing_scope)

    def _name_means_instruction(self, name, instructions):
        try:
            tok = self.lookup_control_sequence(name)
        except NoSuchControlSequence:
            return False
        if isinstance(tok, InstructionToken):
            return tok.instruction in instructions
        else:
            return False

    def name_means_delimit_condition(self, name):
        """Test if a control sequence corresponds to an instruction to split
        blocks of conditional text. Concretely, this means a control sequence
        is '\else' or '\or'."""
        return self._name_means_instruction(name, (Instructions.else_,
                                                   Instructions.or_))

    def name_means_end_condition(self, name):
        """Test if a control sequence corresponds to an instruction to split
        blocks of conditional text. Concretely, this means a control sequence
        is '\fi'."""
        return self._name_means_instruction(name, (Instructions.end_if,))

    def name_means_start_condition(self, name):
        """Test if a control sequence corresponds to an instruction to split
        blocks of conditional text. Concretely, this means a control sequence
        is one of '\ifnum', '\ifcase' and so on."""
        return self._name_means_instruction(name, if_instructions)

    def lookup_control_sequence(self, name, position_like=None):
        route_token = self._lookup_route_token(name)
        canon_token = self._resolve_route_token_to_raw_value(route_token)
        token = canon_token.copy(position_like=position_like)
        # Amend tokens to give them the proper control sequence name.
        if isinstance(token.value, dict) and 'name' in token.value:
            token.value['name'] = name
        return token

    def set_macro(self, name, replacement_text, parameter_text,
                  def_type, prefixes=None):
        if prefixes is None:
            prefixes = set()

        route_id = self._set_route_token(name, ControlSequenceType.macro)

        macro_token = make_macro_token(name,
                                       replacement_text=replacement_text,
                                       parameter_text=parameter_text,
                                       def_type=def_type, prefixes=prefixes)
        self.macros[route_id] = macro_token

    def do_short_hand_definition(self, name, def_type, code):
        def_token_instr = short_hand_def_type_to_token_instr[def_type]
        instr_token = InstructionToken(
            def_token_instr,
            value=code,
            line_nr='abstract'
        )
        self.set_macro(name, replacement_text=[instr_token],
                       parameter_text=[], def_type='sdef', prefixes=None)

    def define_new_font_control_sequence(self, name, font_id):
        # Note, this token just records the font id; the information
        # is stored in the global font state, because it has internal
        # state that might be modified later; we need to know where to get
        # at it.
        self.do_short_hand_definition(name=name,
                                      def_type=Instructions.font.value,
                                      code=font_id)

    def do_let_assignment(self, new_name, target_token):
        if target_token.value['lex_type'] == control_sequence_lex_type:
            target_name = target_token.value['name']
            self._copy_control_sequence(target_name, new_name)
        elif target_token.value['lex_type'] == char_cat_lex_type:
            self._set_let_character(new_name, target_token)
        else:
            raise ValueError(f'Let target does not look like a token: '
                             f'{target_token}')

    def _set_primitive(self, name, instruction):
        # Get a route from the name to a primitive.
        route_id = self._set_route_token(name, ControlSequenceType.primitive)
        # Make that route resolve to the instruction token.
        token = make_primitive_control_sequence_instruction(
            name=name, instruction=instruction)
        self.primitives[route_id] = token

    def _set_parameter(self, name, parameter, instr):
        # Get a route from the name to a parameter.
        route_id = self._set_route_token(name, ControlSequenceType.parameter)

        # Make that route resolve to the parameter token.
        token = make_parameter_control_sequence_instruction(
            name=name, parameter=parameter, instruction=instr)
        self.parameters[route_id] = token

    def _set_special(self, name, special, instr):
        # Get a route from the name to a special.
        route_id = self._set_route_token(name, ControlSequenceType.special)

        # Make that route resolve to the special token.
        token = make_special_control_sequence_instruction(
            name=name, special=special, instruction=instr)
        self.specials[route_id] = token

    def _copy_control_sequence(self, target_name, new_name):
        # Make a new control sequence that is routed to the same spot as the
        # current one.
        target_route_token = self._lookup_route_token(target_name)
        self.control_sequences[new_name] = target_route_token

    def _set_let_character(self, name, char_cat_token):
        route_id = self._set_route_token(name,
                                         ControlSequenceType.let_character)
        self.let_chars[route_id] = char_cat_token

    def _set_route_token(self, name, cs_type):
        route_id = get_unique_id()
        route_token = RouteToken(cs_type, route_id)
        self.control_sequences[name] = route_token
        return route_id

    def _lookup_route_token(self, name):
        # If the route token exists in this scope, return it.
        if name in self.control_sequences:
            route_token = self.control_sequences[name]
        # Otherwise, if there's an enclosing scope, ask it for it.
        elif self.enclosing_scope is not None:
            route_token = self.enclosing_scope._lookup_route_token(name)
        # If we are the outermost scope, the control sequence is unknown.
        else:
            raise NoSuchControlSequence(name)
        return route_token

    def _resolve_route_token_to_raw_value(self, r):
        type_ = r.type
        route_id = r.value
        value_maps_map = {
            ControlSequenceType.parameter: self.parameters,
            ControlSequenceType.special: self.specials,
            ControlSequenceType.primitive: self.primitives,
            ControlSequenceType.macro: self.macros,
            ControlSequenceType.let_character: self.let_chars,
            ControlSequenceType.font: self.font_ids,
        }
        value_map = value_maps_map[type_]
        try:
            v = value_map[route_id]
        except KeyError:
            v = self.enclosing_scope._resolve_route_token_to_raw_value(r)
        return v


class Instructioner:

    def __init__(self, lexer, resolve_cs_func):
        self.lexer = lexer
        self.resolve_control_sequence = resolve_cs_func
        # TODO: Use GetBuffer.
        self.output_buffer = deque()

    @classmethod
    def from_string(cls, resolve_cs_func, *args, **kwargs):
        lexer = Lexer.from_string(*args, **kwargs)
        return cls(lexer, resolve_cs_func=resolve_cs_func)

    def replace_tokens_on_input(self, tokens):
        if logger.isEnabledFor(logging.DEBUG):
            if len(tokens) == 1:
                s = tokens[0]
            elif len(tokens) > 3:
                s = f'[{tokens[0]} … {tokens[-1]}]'
            else:
                s = tokens
            logger.debug(f'Replacing "{s}" on input instruction queue')
        self.output_buffer.extendleft(reversed(tokens))

    def iter_unexpanded(self):
        while True:
            yield self.next_unexpanded()

    def next_unexpanded(self):
        retrieving = self.output_buffer
        if retrieving:
            t = self.output_buffer.popleft()
        else:
            new_lex_token = next(self.lexer)
            t = lex_token_to_instruction_token(new_lex_token)
        if t.char_nr is not None and logger.isEnabledFor(logging.INFO):
            source = 'Retrieved' if retrieving else 'Read'
            if self.lexer.reader.current_buffer.name != 'plain.tex':
                logger.info(f'{source}: {t.get_position_str(self.lexer.reader)}')
        return t

    def next_expanded(self):
        instr_tok = self.next_unexpanded()
        # If the token is an unexpanded control sequence call, and expansion is
        # not suppressed, then we must resolve the call:
        # - A user control sequence will become a macro instruction token.
        # - A \let character will become its character instruction token.
        # - A primitive control sequence will become its instruction token.
        # NOTE: I've made this mistake twice now: we can't make this resolution
        # into a two-call process, where we resolve the token, put the resolved
        # token on the input, then handle it in the next call. This is because,
        # for example, \expandafter expects a single call to the banisher to
        # both resolve *and* expand a macro. Basically this method must do a
        # certain amount to a token in each call.
        if instr_tok.instruction in unexpanded_cs_instructions:
            name = instr_tok.value['name']
            try:
                instr_tok = self.resolve_control_sequence(
                    name, position_like=instr_tok)
            except NoSuchControlSequence:
                # Might be that we are parsing too far in a chunk, and just
                # need to execute a command before this can be understood. Put
                # the token back on the input, potentially to read again.
                self.replace_tokens_on_input([instr_tok])
                raise
        return instr_tok

    def advance_to_end(self, expand=True):
        while True:
            try:
                if expand:
                    yield self.next_expanded()
                else:
                    yield self.next_unexpanded()
            except EOFError:
                return
