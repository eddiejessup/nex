from enum import Enum

from .constants.parameters import param_to_instr
from .constants.specials import special_to_instr
from .constants.instructions import Instructions, if_instructions
from .constants import control_sequences
from .tokens import InstructionToken, BaseToken
from .utils import get_unique_id
from .lexer import control_sequence_lex_type, char_cat_lex_type
from .instructioner import (make_primitive_control_sequence_instruction,
                            make_parameter_control_sequence_instruction,
                            make_special_control_sequence_instruction)
from .macro import parse_replacement_text, parse_parameter_text


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
