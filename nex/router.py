from enum import Enum

from .tokens import InstructionToken, BaseToken
from .utils import get_unique_id, NoSuchControlSequence
from .tex_parameters import Parameters
from .lexer import control_sequence_lex_type, char_cat_lex_type
from .instructioner import (make_primitive_control_sequence_instruction,
                            make_parameter_control_sequence_instruction)
from .instructions import Instructions
from .expander import parse_replacement_text, parse_parameter_text


# Control sequence to instruction map.
I = Instructions
primitive_control_sequence_map = {
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

P = Parameters
param_control_sequence_map = {
    'pretolerance': P.pre_tolerance,
    'tolerance': P.tolerance,
    'hbadness': P.h_badness,
    'vbadness': P.v_badness,
    'linepenalty': P.line_penalty,
    'hyphenpenalty': P.hyphen_penalty,
    'exhyphenpenalty': P.ex_hyphen_penalty,
    'binoppenalty': P.bin_op_penalty,
    'relpenalty': P.rel_penalty,
    'clubpenalty': P.club_penalty,
    'widowpenalty': P.widow_penalty,
    'displaywidowpenalty': P.display_widow_penalty,
    'brokenpenalty': P.broken_penalty,
    'predisplaypenalty': P.pre_display_penalty,
    'postdisplaypenalty': P.post_display_penalty,
    'interlinepenalty': P.inter_line_penalty,
    'floatingpenalty': P.floating_penalty,
    'outputpenalty': P.output_penalty,
    'doublehyphendemerits': P.double_hyphen_demerits,
    'finalhyphendemerits': P.final_hyphen_demerits,
    'adjdemerits': P.adj_demerits,
    'looseness': P.looseness,
    'pausing': P.pausing,
    'holdinginserts': P.holding_inserts,
    'tracingonline': P.tracing_on_line,
    'tracingmacros': P.tracing_macros,
    'tracingstats': P.tracing_stats,
    'tracingparagraphs': P.tracing_paragraphs,
    'tracingpages': P.tracing_pages,
    'tracingoutput': P.tracing_output,
    'tracinglostchars': P.tracing_lostchars,
    'tracingcommands': P.tracing_commands,
    'tracingrestores': P.tracing_restores,
    'language': P.language,
    'uchyph': P.uc_hyph,
    'lefthyphenmin': P.left_hyphen_min,
    'righthyphenmin': P.right_hyphen_min,
    'globaldefs': P.global_defs,
    'maxdeadcycles': P.max_dead_cycles,
    'hangafter': P.hang_after,
    'fam': P.fam,
    'mag': P.mag,
    'escapechar': P.escape_char,
    'defaulthyphenchar': P.default_hyphen_char,
    'defaultskewchar': P.default_skew_char,
    'endlinechar': P.end_line_char,
    'newlinechar': P.new_line_char,
    'delimiterfactor': P.delimiter_factor,
    # THESE TIME ONES WILL BE SET IN P
    'time': P.time,
    'day': P.day,
    'month': P.month,
    'year': P.year,
    'showboxbreadth': P.show_box_breadth,
    'showboxdepth': P.show_box_depth,
    'errorcontextlines': P.error_context_lines,

    'hfuzz': P.h_fuzz,
    'vfuzz': P.v_fuzz,
    'overfullrule': P.over_full_rule,
    'hsize': P.h_size,
    'vsize': P.v_size,
    'maxdepth': P.max_depth,
    'splitmaxdepth': P.split_max_depth,
    'boxmaxdepth': P.box_max_depth,
    'lineskiplimit': P.line_skip_limit,
    'delimitershortfall': P.delimiter_short_fall,
    'nulldelimiterspace': P.null_delimiter_space,
    'scriptspace': P.script_space,
    'mathsurround': P.math_surround,
    'predisplaysize': P.pre_display_size,
    'displaywidth': P.display_width,
    'displayindent': P.display_indent,
    'parindent': P.par_indent,
    'hangindent': P.hang_indent,
    'hoffset': P.h_offset,
    'voffset': P.v_offset,

    'baselineskip': P.base_line_skip,
    'lineskip': P.line_skip,
    'parskip': P.par_skip,
    'abovedisplayskip': P.above_display_skip,
    'abovedisplayshortskip': P.above_display_short_skip,
    'belowdisplayskip': P.below_display_skip,
    'belowdisplayshortskip': P.below_display_short_skip,
    'leftskip': P.left_skip,
    'rightskip': P.right_skip,
    'topskip': P.top_skip,
    'splittopskip': P.split_top_skip,
    'tabskip': P.tab_skip,
    'spaceskip': P.space_skip,
    'xspaceskip': P.x_space_skip,
    'parfillskip': P.par_fill_skip,

    'thinmuskip': P.thin_mu_skip,
    'medmuskip': P.med_mu_skip,
    'thickmuskip': P.thick_mu_skip,

    'output': P.output,
    'everypar': P.every_par,
    'everymath': P.every_math,
    'everydisplay': P.every_display,
    'everyhbox': P.every_h_box,
    'everyvbox': P.every_v_box,
    'everyjob': P.every_job,
    'everycr': P.every_cr,
    'errhelp': P.err_help,
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


class ControlSequenceType(Enum):
    macro = 1
    let_character = 2
    parameter = 3
    primitive = 4
    font = 5


class RouteToken(BaseToken):

    def __init__(self, type_, value):
        if type_ not in ControlSequenceType:
            raise ValueError('Route token type must be a ControlSequenceType')
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
               'def_type': def_type},
        line_nr='abstract',
    )


def get_initial_router():
    return CSRouter(param_control_sequences=param_control_sequence_map,
                    primitive_control_sequences=primitive_control_sequence_map,
                    enclosing_scope=None)


def get_local_router(enclosing_scope):
    return CSRouter(param_control_sequences={}, primitive_control_sequences={},
                    enclosing_scope=enclosing_scope)


class CSRouter(object):

    def __init__(self, param_control_sequences, primitive_control_sequences,
                 enclosing_scope=None):
        self.control_sequences = {}
        self.macros = {}
        self.let_chars = {}
        self.parameters = {}
        self.primitives = {}
        self.font_ids = {}
        self.enclosing_scope = enclosing_scope

        for name, parameter in param_control_sequences.items():
            self._set_parameter(name, parameter)
        for name, instruction in primitive_control_sequences.items():
            self._set_primitive(name, instruction)

    def _set_route_token(self, name, route_token):
        self.control_sequences[name] = route_token

    def _set_primitive(self, name, instruction):
        # Add a route from the name to the primitive.
        route_id = name
        route_token = RouteToken(ControlSequenceType.primitive, route_id)
        self._set_route_token(name, route_token)

        # Make that route resolve to the instruction token.
        token = make_primitive_control_sequence_instruction(
            name=name, instruction=instruction)
        self.primitives[route_id] = token

    def _set_parameter(self, name, parameter):
        # Add a route from the control sequence name to the parameter.
        route_id = name
        route_token = RouteToken(ControlSequenceType.parameter, route_id)
        self._set_route_token(name, route_token)

        # Make that route resolve to the instruction token.
        token = make_parameter_control_sequence_instruction(
            name=name, parameter=parameter)
        self.parameters[route_id] = token

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
            v = self.enclosing_scope.cs_router._resolve_route_token_to_raw_value(r)
        return v

    def resolve_control_sequence_to_token(self, name, position_like=None):
        route_token = self._resolve_control_sequence_to_route_token(name)
        canon_token = self._resolve_route_token_to_raw_value(route_token)
        token = canon_token.copy(position_like=position_like)
        # Amend tokens to give them the proper control sequence name.
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

    def set_macro(self, name, replacement_text, parameter_text,
                  def_type, prefixes=None):
        route_id = get_unique_id()
        route_token = RouteToken(ControlSequenceType.macro, route_id)
        self._set_route_token(name, route_token)

        if prefixes is None:
            prefixes = set()

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

    def _set_let_character(self, name, char_cat_token):
        route_id = get_unique_id()
        route_token = RouteToken(ControlSequenceType.let_character, route_id)
        self._set_route_token(name, route_token)
        self.let_chars[route_id] = char_cat_token

    def define_new_font_control_sequence(self, name, font_id):
        route_id = get_unique_id()
        route_token = RouteToken(ControlSequenceType.font, route_id)
        self._set_route_token(name, route_token)

        # Note, this token just records the font id; the information
        # is stored in the global font state, because it has internal
        # state that might be modified later; we need to know where to get
        # at it.
        font_id_token = InstructionToken(
            Instructions.font_def_token,
            value=font_id,
            line_nr='abstract'
        )
        self.font_ids[route_id] = font_id_token
