from enum import Enum

from .tokens import InstructionToken, BaseToken
from .utils import get_unique_id, NoSuchControlSequence
from .accessors import (Parameters, param_to_instr,
                        Specials, special_to_instr)
from .lexer import control_sequence_lex_type, char_cat_lex_type
from .instructioner import (make_primitive_control_sequence_instruction,
                            make_parameter_control_sequence_instruction,
                            make_special_control_sequence_instruction)
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
    'accent': I.accent,
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

special_control_sequence_map = {
    'spacefactor': Specials.space_factor,
    'prevgraf': Specials.prev_graf,
    'deadcycles': Specials.dead_cycles,
    'insertpenalties': Specials.insert_penalties,
    'prevdepth': Specials.prev_depth,
    'pagegoal': Specials.page_goal,
    'pagetotal': Specials.page_total,
    'pagestretch': Specials.page_stretch,
    'pagefilstretch': Specials.page_fil_stretch,
    'pagefillstretch': Specials.page_fill_stretch,
    'pagefilllstretch': Specials.page_filll_stretch,
    'pageshrink': Specials.page_shrink,
    'pagedepth': Specials.page_depth,
}

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


def get_initial_router():
    # Router needs a map from a control sequence name, to the parameter and the
    # instruction type of the parameter (integer, dimen and so on).
    param_map = {n: (p, param_to_instr[p])
                 for n, p in param_control_sequence_map.items()}
    special_map = {n: (p, special_to_instr[p])
                   for n, p in special_control_sequence_map.items()}
    return CSRouter(param_control_sequences=param_map,
                    special_control_sequences=special_map,
                    primitive_control_sequences=primitive_control_sequence_map,
                    enclosing_scope=None)


def get_local_router(enclosing_scope):
    return CSRouter(param_control_sequences={},
                    special_control_sequences={},
                    primitive_control_sequences={},
                    enclosing_scope=enclosing_scope)


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
            import pdb; pdb.set_trace()

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
