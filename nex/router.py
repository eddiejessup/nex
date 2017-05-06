from .tokens import BuiltToken, InstructionToken, InternalToken
from .utils import get_unique_id, NoSuchControlSequence
from .tex_parameters import parameter_instr_to_names
from .lexer import control_sequence_lex_type, char_cat_lex_type
from .constants.primitive_control_sequences import Instructions


# Control sequence to instruction map.
I = Instructions
primitive_control_sequences_map = {
    'catcode': I.cat_code,
    'mathcode': I.math_code,
    'uccode': I.upper_case_code,
    'lccode': I.lower_case_code,
    'sfcode': I.space_factor_code,
    'delcode': I.delimiter_code,
    'let': I.let,
    'advance': I.advance,
    'par': I.par,
    'relax': I.relax,
    'immediate': I.immediate,
    'font': I.font,
    'skewchar': I.skew_char,
    'hyphenchar': I.hyphen_char,
    'fontdimen': I.font_dimen,
    'textfont': I.text_font,
    'scriptfont': I.script_font,
    'scriptscriptfont': I.script_script_font,
    'undefined': I.undefined,
    'global': I.global_mod,
    'long': I.long_mod,
    'outer': I.outer_mod,
    'setbox': I.set_box,
    'box': I.box,
    'copy': I.copy,
    'unhbox': I.un_h_box,
    'unhcopy': I.un_h_copy,
    'unvbox': I.un_v_box,
    'unvcopy': I.un_v_copy,
    'lastbox': I.last_box,
    'vsplit': I.v_split,
    'ht': I.box_dimen_height,
    'wd': I.box_dimen_width,
    'dp': I.box_dimen_depth,
    'kern': I.kern,
    'mkern': I.math_kern,
    'vrule': I.v_rule,
    'hrule': I.h_rule,
    'input': I.input,
    'end': I.end,
    'char': I.char,
    'indent': I.indent,
    'message': I.message,
    'errmessage': I.error_message,
    'write': I.write,
    'hyphenation': I.hyphenation,
    'patterns': I.patterns,
    'hskip': I.h_skip,
    'hfil': I.h_fil,
    'hfill': I.h_fill,
    'hss': I.h_stretch_or_shrink,
    'hfilneg': I.h_fil_neg,
    'vskip': I.v_skip,
    'vfil': I.v_fil,
    'vfill': I.v_fill,
    'vss': I.v_stretch_or_shrink,
    'vfilneg': I.v_fil_neg,
    'hbox': I.h_box,
    'vbox': I.v_box,
    'vtop': I.v_top,
    'count': I.count,
    'dimen': I.dimen,
    'skip': I.skip,
    'muskip': I.mu_skip,
    'toks': I.toks,
    'chardef': I.char_def,
    'mathchardef': I.math_char_def,
    'countdef': I.count_def,
    'dimendef': I.dimen_def,
    'skipdef': I.skip_def,
    'muskipdef': I.mu_skip_def,
    'toksdef': I.toks_def,
    'def': I.def_,
    'gdef': I.g_def,
    'edef': I.e_def,
    'xdef': I.x_def,
    'ifnum': I.if_num,
    'iftrue': I.if_true,
    'iffalse': I.if_false,
    'ifcase': I.if_case,
    'string': I.string,
    'csname': I.cs_name,
    'endcsname': I.end_cs_name,
    'expandafter': I.expand_after,
    'uppercase': I.upper_case,
    'lowercase': I.lower_case,
    'cr': I.cr,
    'else': I.else_,
    'fi': I.end_if,
    'or': I.or_,
}


short_hand_def_type_to_token_instr = {
    Instructions.char_def.value: Instructions.char_def_token,
    Instructions.math_char_def.value: Instructions.math_char_def_token,
    Instructions.count_def.value: Instructions.count_def_token,
    Instructions.dimen_def.value: Instructions.dimen_def_token,
    Instructions.skip_def.value: Instructions.skip_def_token,
    Instructions.mu_skip_def.value: Instructions.mu_skip_def_token,
    Instructions.toks_def.value: Instructions.toks_def_token,
}


primitive_canon_tokens = {}
for prim_cs, prim_instruction in primitive_control_sequences_map.items():
    # Terminals are tokens that may be passed to the parser. Non-terminals
    # are tokens that will be consumed by the banisher before the parser
    # sees them.
    primitive_canon_token = InstructionToken.from_instruction(
        prim_instruction,
        value={'canonical_name': prim_cs,
               'name': prim_cs,
               'lex_type': control_sequence_lex_type},
        line_nr='abstract')
    primitive_canon_tokens[prim_cs] = primitive_canon_token


def make_route_token(type_, route_id):
    return InternalToken(type_=type_, value=route_id)


def get_initial_router():
    control_sequences = {}

    macros = {}
    let_chars = {}
    font_ids = {}

    parameters = {}
    for param_instr, param_canonical_names in parameter_instr_to_names.items():
        for param_canonical_name in param_canonical_names:
            # Add a router for the canonical name to the primitive.
            route_id = param_canonical_name
            route_token = make_route_token('parameter', route_id)
            control_sequences[param_canonical_name] = route_token

            param_canon_token = InstructionToken.from_instruction(
                param_instr,
                value={'canonical_name': param_canonical_name,
                       'name': param_canonical_name},
                line_nr='abstract',
            )
            parameters[route_id] = param_canon_token

    primitives = {}
    for prim_canon_name, prim_canon_token in primitive_canon_tokens.items():
        # Add a router for the canonical name to the primitive.
        route_id = prim_canon_name
        route_token = make_route_token('primitive', route_id)
        control_sequences[prim_canon_name] = route_token

        # Make that route resolve to the primitive canonical token.
        primitives[route_id] = prim_canon_token

    router = CSRouter(control_sequences,
                      macros, let_chars, parameters, primitives, font_ids,
                      enclosing_scope=None)
    return router


def get_local_router(enclosing_scope):
    control_sequences = {}

    macros = {}
    let_chars = {}
    parameters = {}
    primitives = {}
    font_ids = {}

    router = CSRouter(control_sequences,
                      macros, let_chars, parameters, primitives, font_ids,
                      enclosing_scope)
    return router


class CSRouter(object):

    def __init__(self, control_sequences,
                 macros, let_chars, parameters, primitives, font_ids,
                 enclosing_scope=None):
        self.control_sequences = control_sequences

        self.macros = macros
        self.let_chars = let_chars
        self.parameters = parameters
        self.primitives = primitives
        self.font_ids = font_ids

        self.enclosing_scope = enclosing_scope

    def _set_route_token(self, name, route_token):
        self.control_sequences[name] = route_token

    def _resolve_control_sequence_to_route_token(self, name):
        # If the route token exists in this scope, return it.
        if name in self.control_sequences:
            route_token = self.control_sequences[name]
        # Otherwise, if there's an enclosing scope, ask it for it.
        elif self.enclosing_scope is not None:
            route_token = self.enclosing_scope.cs_router._resolve_control_sequence_to_route_token(name)
        # If we are the outermost scope, the control sequence is unknown.
        else:
            raise NoSuchControlSequence(name)
        return route_token

    def _resolve_route_token_to_raw_value(self, r):
        type_ = r.type
        route_id = r.value
        value_maps_map = {
            'parameter': self.parameters,
            'primitive': self.primitives,
            'macro': self.macros,
            'let_character': self.let_chars,
            'font': self.font_ids,
        }
        value_map = value_maps_map[type_]
        try:
            v = value_map[route_id]
        except:
            v = self.enclosing_scope.cs_router._resolve_route_token_to_raw_value(r)
        return v

    def resolve_control_sequence_to_token(self, name, position_like=None):
        route_token = self._resolve_control_sequence_to_route_token(name)
        canon_token = self._resolve_route_token_to_raw_value(route_token)
        token = canon_token.copy(position_like=position_like)
        # Amend canonical tokens to give them the proper control sequence
        # 'name'.
        if isinstance(token.value, dict) and 'name' in token.value:
            token.value['name'] = name
        return token

    def _copy_control_sequence(self, target_name, new_name):
        # Make a new control sequence that is routed to the same spot as the
        # current one.
        target_route_token = self._resolve_control_sequence_to_route_token(target_name)
        self._set_route_token(new_name, target_route_token)

    def do_let_assignment(self, new_name, target_token):
        if target_token.value['lex_type'] == control_sequence_lex_type:
            target_name = target_token.value['name']
            self._copy_control_sequence(target_name, new_name)
        elif target_token.value['lex_type'] == char_cat_lex_type:
            self._set_let_character(new_name, target_token)
        else:
            import pdb; pdb.set_trace()

    def set_macro(self, name, text, def_type, prefixes=None):
        route_id = get_unique_id()
        route_token = make_route_token('macro', route_id)
        self._set_route_token(name, route_token)

        if prefixes is None:
            prefixes = set()
        macro_token = InstructionToken(
            Instructions.macro,
            value={'name': name,
                   'prefixes': prefixes,
                   'text': text,
                   'def_type': def_type},
            line_nr='abstract',
        )
        self.macros[route_id] = macro_token

    def do_short_hand_definition(self, name, def_type, code):
        def_token_instr = short_hand_def_type_to_token_instr[def_type]
        terminal_token = InstructionToken(
            def_token_instr,
            value=code,
            line_nr='abstract'
        )
        text = BuiltToken(type_='definition_text',
                          value={'parameter_text': [],
                                 'replacement_text': [terminal_token]})
        self.set_macro(name, text, def_type='sdef', prefixes=None)

    def _set_let_character(self, name, char_cat_token):
        route_id = get_unique_id()
        route_token = make_route_token('let_character', route_id)
        self._set_route_token(name, route_token)
        self.let_chars[route_id] = char_cat_token

    def define_new_font_control_sequence(self, name, font_id):
        route_id = get_unique_id()
        route_token = make_route_token('font', route_id)
        self._set_route_token(name, route_token)

        # Note, this token just records the font id; the information
        # is stored in the global font state, because it has internal
        # state that might be modified later; we need to know where to get
        # at it.
        font_id_token = InstructionToken.from_instruction(
            Instructions.font_def_token,
            value=font_id,
            line_nr='abstract'
        )
        self.font_ids[route_id] = font_id_token
