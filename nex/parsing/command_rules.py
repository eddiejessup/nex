from ..tokens import BuiltToken, CommandToken
from ..constants.commands import Commands

from .utils import make_literal_token, get_literal_production_rule


def get_command_token(c, p):
    return CommandToken(c, value=p[0].value, position_like=p)


def add_command_rules(pg):
    # Mode-independent commands, that do not directly affect list-building.

    @pg.production('command : assignment')
    def command_assignment(p):
        return get_command_token(Commands.assign, p)

    @pg.production('command : RELAX')
    def command_relax(p):
        return get_command_token(Commands.relax, p)

    @pg.production('command : RIGHT_BRACE')
    def command_right_brace(p):
        return get_command_token(Commands.right_brace, p)

    @pg.production('command : BEGIN_GROUP')
    def command_begin_group(p):
        return get_command_token(Commands.begin_group, p)

    @pg.production('command : END_GROUP')
    def command_end_group(p):
        return get_command_token(Commands.end_group, p)

    @pg.production('command : show_token')
    def command_show_token(p):
        return get_command_token(Commands.show_token, p)

    @pg.production('command : show_box')
    def command_show_box(p):
        return get_command_token(Commands.show_box, p)

    @pg.production('command : SHOW_LISTS')
    def command_show_lists(p):
        return get_command_token(Commands.show_lists, p)

    @pg.production('command : show_the')
    def command_show_the(p):
        return get_command_token(Commands.show_the, p)

    @pg.production('command : ship_out')
    def command_ship_out(p):
        return get_command_token(Commands.ship_out, p)

    @pg.production('command : ignore_spaces')
    def command_ignore_spaces(p):
        return get_command_token(Commands.ignore_spaces, p)

    @pg.production('command : after_assignment')
    def command_set_after_assignment_token(p):
        return get_command_token(Commands.set_after_assignment_token, p)

    @pg.production('command : after_group')
    def command_add_to_after_group_tokens(p):
        return get_command_token(Commands.add_to_after_group_tokens, p)

    # [Upper and lowercase are handled in banisher.]

    @pg.production('command : message')
    def command_message(p):
        return get_command_token(Commands.message, p)

    @pg.production('command : error_message')
    def command_error_message(p):
        return get_command_token(Commands.error_message, p)

    @pg.production('command : open_input')
    def command_open_input(p):
        return get_command_token(Commands.open_input, p)

    @pg.production('command : close_input')
    def command_close_input(p):
        return get_command_token(Commands.close_input, p)

    @pg.production('command : open_output')
    def command_open_output(p):
        return get_command_token(Commands.open_output, p)

    @pg.production('command : close_output')
    def command_close_output(p):
        return get_command_token(Commands.close_output, p)

    @pg.production('command : write')
    def command_write(p):
        return get_command_token(Commands.write, p)

    # Almost mode-independent commands, that just deal with different types of
    # lists.

    @pg.production('command : special')
    def command_do_special(p):
        return get_command_token(Commands.do_special, p)

    @pg.production('command : add_penalty')
    def command_add_penalty(p):
        return get_command_token(Commands.add_penalty, p)

    @pg.production('command : add_kern')
    def command_add_kern(p):
        return get_command_token(Commands.add_kern, p)

    @pg.production('command : add_math_kern')
    def command_add_math_kern(p):
        return get_command_token(Commands.add_math_kern, p)

    @pg.production('command : UN_PENALTY')
    def command_un_penalty(p):
        return get_command_token(Commands.un_penalty, p)

    @pg.production('command : UN_KERN')
    def command_un_kern(p):
        return get_command_token(Commands.un_kern, p)

    @pg.production('command : UN_GLUE')
    def command_un_glue(p):
        return get_command_token(Commands.un_glue, p)

    @pg.production('command : mark')
    def command_mark(p):
        return get_command_token(Commands.mark, p)

    @pg.production('command : insert')
    def command_insert(p):
        return get_command_token(Commands.insert, p)

    @pg.production('command : v_adjust')
    def command_vertical_adjust(p):
        return get_command_token(Commands.vertical_adjust, p)

    # These are a bit cheaty to put in the mode-independent section.
    # They are described separately in each mode in the TeXBook.

    @pg.production('command : add_leaders')
    def command_add_leaders(p):
        return get_command_token(Commands.add_leaders, p)

    @pg.production('command : SPACE')
    def command_add_space(p):
        return get_command_token(Commands.add_space, p)

    @pg.production('command : box')
    def command_add_box(p):
        return get_command_token(Commands.add_box, p)

    @pg.production('command : INDENT')
    def command_indent(p):
        return get_command_token(Commands.indent, p)

    @pg.production('command : NO_INDENT')
    def command_no_indent(p):
        return get_command_token(Commands.no_indent, p)

    @pg.production('command : PAR')
    def command_par(p):
        return get_command_token(Commands.par, p)

    @pg.production('command : LEFT_BRACE')
    def command_left_brace(p):
        return get_command_token(Commands.left_brace, p)

    # Vertical commands.

    @pg.production('command : vertical_glue')
    def command_vertical_glue(p):
        return get_command_token(Commands.add_vertical_glue, p)

    @pg.production('command : move_box_left')
    def command_move_box_left(p):
        return get_command_token(Commands.move_box_left, p)

    @pg.production('command : move_box_right')
    def command_move_box_right(p):
        return get_command_token(Commands.move_box_right, p)

    @pg.production('command : horizontal_rule')
    def command_add_horizontal_rule(p):
        return get_command_token(Commands.add_horizontal_rule, p)

    @pg.production('command : h_align')
    def command_horizontal_align(p):
        return get_command_token(Commands.horizontal_align, p)

    @pg.production('command : unpack_horizontal_box')
    def command_unpack_horizontal_box(p):
        return get_command_token(Commands.unpack_horizontal_box, p)

    @pg.production('command : END')
    def command_end(p):
        return get_command_token(Commands.end, p)

    @pg.production('command : DUMP')
    def command_dump(p):
        return get_command_token(Commands.dump, p)

    # Horizontal commands.

    @pg.production('command : horizontal_glue')
    def command_horizontal_glue(p):
        return get_command_token(Commands.add_horizontal_glue, p)

    @pg.production('command : CONTROL_SPACE')
    def command_add_control_space(p):
        return get_command_token(Commands.add_control_space, p)

    @pg.production('command : raise_box')
    def command_raise_box(p):
        return get_command_token(Commands.raise_box, p)

    @pg.production('command : lower_box')
    def command_lower_box(p):
        return get_command_token(Commands.lower_box, p)

    @pg.production('command : vertical_rule')
    def command_add_vertical_rule(p):
        return get_command_token(Commands.add_vertical_rule, p)

    @pg.production('command : v_align')
    def command_vertical_align(p):
        return get_command_token(Commands.vertical_align, p)

    @pg.production('command : unpack_vertical_box')
    def command_unpack_vertical_box(p):
        return get_command_token(Commands.unpack_vertical_box, p)

    @pg.production('command : character')
    def command_add_character_explicit(p):
        return get_command_token(Commands.add_character_explicit, p)

    @pg.production('command : CHAR_DEF_TOKEN')
    def command_add_character_token(p):
        return get_command_token(Commands.add_character_token, p)

    @pg.production('command : character_code')
    def command_add_character_code(p):
        return get_command_token(Commands.add_character_code, p)

    @pg.production('command : solo_accent')
    @pg.production('command : paired_accent')
    def command_paired_accent(p):
        return get_command_token(Commands.add_accent, p)

    @pg.production('command : ITALIC_CORRECTION')
    def command_add_italic_correction(p):
        return get_command_token(Commands.add_italic_correction, p)

    @pg.production('command : discretionary')
    def command_discretionary(p):
        return get_command_token(Commands.add_discretionary, p)

    @pg.production('command : DISCRETIONARY_HYPHEN')
    def command_discretionary_hyphen(p):
        return get_command_token(Commands.add_discretionary_hyphen, p)

    @pg.production('command : MATH_SHIFT')
    def command_math_shift(p):
        return get_command_token(Commands.do_math_shift, p)

    # Command grammar.

    @pg.production('show_token : SHOW_TOKEN ARBITRARY_TOKEN')
    def show_token(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1],
                          position_like=p)

    @pg.production('show_box : SHOW_BOX number')
    def show_box(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1],
                          position_like=p)

    @pg.production('show_the : SHOW_THE internal_quantity')
    def show_the(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1],
                          position_like=p)

    # Things that can follow 'show_the'.
    # Parameter.
    @pg.production('internal_quantity : INTEGER_PARAMETER')
    @pg.production('internal_quantity : DIMEN_PARAMETER')
    @pg.production('internal_quantity : GLUE_PARAMETER')
    @pg.production('internal_quantity : MU_GLUE_PARAMETER')
    # Register.
    @pg.production('internal_quantity : count_register')
    @pg.production('internal_quantity : dimen_register')
    @pg.production('internal_quantity : skip_register')
    @pg.production('internal_quantity : mu_skip_register')
    @pg.production('internal_quantity : code_variable')
    # Special 'register' as the TeXBook calls it. Seems more like a parameter
    # to me...
    @pg.production('internal_quantity : SPECIAL_INTEGER')
    @pg.production('internal_quantity : SPECIAL_DIMEN')
    @pg.production('internal_quantity : dimen_font_variable')
    @pg.production('internal_quantity : integer_font_variable')
    @pg.production('internal_quantity : LAST_PENALTY')
    @pg.production('internal_quantity : LAST_KERN')
    @pg.production('internal_quantity : LAST_GLUE')
    # Defined character.
    @pg.production('internal_quantity : CHAR_DEF_TOKEN')
    @pg.production('internal_quantity : MATH_CHAR_DEF_TOKEN')
    @pg.production('internal_quantity : font')
    @pg.production('internal_quantity : token_variable')
    def internal_quantity(p):
        return p[0]

    @pg.production('ship_out : SHIP_OUT box')
    def ship_out(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1].value,
                          position_like=p)

    @pg.production('ignore_spaces : IGNORE_SPACES optional_spaces')
    def ignore_spaces(p):
        return BuiltToken(type_=p[0].type,
                          value=None,
                          position_like=p)

    @pg.production('after_assignment : AFTER_ASSIGNMENT ARBITRARY_TOKEN')
    @pg.production('after_group : AFTER_GROUP ARBITRARY_TOKEN')
    def after_event(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1],
                          position_like=p)

    @pg.production('message : MESSAGE general_text')
    def message(p):
        return BuiltToken(type_='message',
                          value={'content': p[1]},
                          position_like=p)

    @pg.production('error_message : ERROR_MESSAGE general_text')
    def error_message(p):
        return BuiltToken(type_='error_message',
                          value={'content': p[1]},
                          position_like=p)

    @pg.production('open_input : OPEN_INPUT number equals file_name')
    @pg.production('open_output : OPEN_OUTPUT number equals file_name')
    def open_io(p):
        return BuiltToken(type_=p[0].type,
                          value={'stream_nr': p[1],
                                 'file_name': p[3]},
                          position_like=p)

    @pg.production('close_input : CLOSE_INPUT number')
    @pg.production('close_output : CLOSE_OUTPUT number')
    def close_io(p):
        return BuiltToken(type_=p[0].type,
                          value={'stream_nr': p[1]},
                          position_like=p)

    @pg.production('write : IMMEDIATE write')
    def immediate_write(p):
        p[1].value['prefix'] = 'immediate'
        return p[1]

    @pg.production('write : WRITE number general_text')
    def write(p):
        return BuiltToken(type_=p[0].type,
                          value={'stream_number': p[1],
                                 'content': p[2],
                                 'prefix': None},
                          position_like=p)

    @pg.production('special : SPECIAL general_text')
    def special(p):
        return BuiltToken(type_=p[0].type,
                          value={'content': p[1]},
                          position_like=p)

    @pg.production('add_penalty : ADD_PENALTY number')
    def add_penalty(p):
        return BuiltToken(type_=p[0].type, value=p[1],
                          position_like=p)

    @pg.production('add_kern : KERN dimen')
    @pg.production('add_math_kern : MATH_KERN mu_dimen')
    def add_kern(p):
        return BuiltToken(type_=p[0].type, value=p[1],
                          position_like=p)

    @pg.production('mark : MARK general_text')
    def mark(p):
        return BuiltToken(type_=p[0].type,
                          value={'content': p[1]},
                          position_like=p)

    @pg.production('insert : INSERT number filler LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
    def insert(p):
        return BuiltToken(type_=p[0].type,
                          value={'number': p[1],
                                 'content': p[4]},
                          position_like=p)

    @pg.production('v_adjust : V_ADJUST filler LEFT_BRACE VERTICAL_MODE_MATERIAL_AND_RIGHT_BRACE')
    def v_adjust(p):
        return BuiltToken(type_=p[0].type,
                          value={'content': p[3]},
                          position_like=p)

    @pg.production('vertical_glue : V_FIL')
    @pg.production('vertical_glue : V_FILL')
    @pg.production('vertical_glue : V_STRETCH_OR_SHRINK')
    @pg.production('vertical_glue : V_FIL_NEG')
    @pg.production('vertical_glue : normal_vertical_glue')
    def vertical_glue(p):
        return BuiltToken(type_='vertical_glue',
                          value=p[0],
                          position_like=p)

    @pg.production('horizontal_glue : H_FIL')
    @pg.production('horizontal_glue : H_FILL')
    @pg.production('horizontal_glue : H_STRETCH_OR_SHRINK')
    @pg.production('horizontal_glue : H_FIL_NEG')
    @pg.production('horizontal_glue : normal_horizontal_glue')
    def horizontal_glue(p):
        return BuiltToken(type_='horizontal_glue',
                          value=p[0],
                          position_like=p)

    @pg.production('normal_vertical_glue : V_SKIP glue')
    @pg.production('normal_horizontal_glue : H_SKIP glue')
    def normal_glue(p):
        return BuiltToken(type_=p[0].type,
                          value=p[1].value,
                          position_like=p)

    @pg.production('add_leaders : leaders box_or_rule vertical_glue')
    @pg.production('add_leaders : leaders box_or_rule horizontal_glue')
    def add_leaders(p):
        return BuiltToken(type_='leaders',
                          value={
                            'type': p[0].type,
                            'box': p[1],
                            'glue': p[2],
                          },
                          position_like=p)

    @pg.production('box_or_rule : box')
    @pg.production('box_or_rule : vertical_rule')
    @pg.production('box_or_rule : horizontal_rule')
    def box_or_rule(p):
        return p[0]

    @pg.production('leaders : LEADERS')
    @pg.production('leaders : CENTERED_LEADERS')
    @pg.production('leaders : EXPANDED_LEADERS')
    def leaders(p):
        return BuiltToken(type_=p[0].type, value=None,
                          position_like=p)

    @pg.production('unpack_horizontal_box : UN_H_BOX number')
    @pg.production('unpack_horizontal_box : UN_H_COPY number')
    @pg.production('unpack_vertical_box : UN_V_BOX number')
    @pg.production('unpack_vertical_box : UN_V_COPY number')
    def un_box(p):
        return BuiltToken(type_='un_box',
                          value={'nr': p[1], 'cmd_type': p[0].type},
                          position_like=p)

    @pg.production('move_box_left : MOVE_LEFT dimen box')
    @pg.production('move_box_right : MOVE_RIGHT dimen box')
    @pg.production('raise_box : RAISE_BOX dimen box')
    @pg.production('lower_box : LOWER_BOX dimen box')
    def shifted_box(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'offset': p[1],
                            'box': p[2],
                          },
                          position_like=p)

    @pg.production('h_align : H_ALIGN box_specification LEFT_BRACE ALIGNMENT_MATERIAL RIGHT_BRACE')
    @pg.production('v_align : V_ALIGN box_specification LEFT_BRACE ALIGNMENT_MATERIAL RIGHT_BRACE')
    def align(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'box_specification': p[1],
                            'alignment_material': p[3],
                          },
                          position_like=p)

    @pg.production('vertical_rule : V_RULE rule_specification')
    @pg.production('horizontal_rule : H_RULE rule_specification')
    def rule(p):
        return BuiltToken(type_=p[0].type, value=p[1].value,
                          position_like=p)

    @pg.production('paired_accent : solo_accent character_like')
    def accent_with_character(p):
        t = BuiltToken(type_='ACCENT', value=p[0].value, position_like=p)
        t.value['target_char'] = p[1]
        return t

    @pg.production('character_like : character')
    @pg.production('character_like : CHAR_DEF_TOKEN')
    @pg.production('character_like : character_code')
    def character_like(p):
        return p[0]

    @pg.production('character_code : CHAR number')
    def character_code(p):
        return BuiltToken(type_='char',
                          value={'code': p[1]},
                          position_like=p)

    @pg.production('solo_accent : ACCENT number optional_assignments')
    def accent_without_character(p):
        return BuiltToken(type_='ACCENT', value={'assignments': p[2],
                                                 'accent_code': p[1],
                                                 'target_char': None},
                          position_like=p)

    @pg.production('discretionary : DISCRETIONARY general_text general_text general_text')
    def discretionary(p):
        return BuiltToken(type_=p[0].type,
                          value={
                            'item_1': p[1],
                            'item_2': p[2],
                            'item_3': p[3],
                          },
                          position_like=p)

    # End of commands. The remainder below are intermediate productions.

    @pg.production('optional_assignments : empty')
    def optional_assignments_none(p):
        return BuiltToken(type_='assignments', value=[], position_like=p)

    @pg.production('optional_assignments : assignment optional_assignments')
    def optional_assignments(p):
        t = BuiltToken(type_=p[1].type, value=p[1].value, position_like=p)
        t.value.append(p[0])
        return t

    @pg.production('rule_specification : rule_dimension rule_specification')
    def rule_specification(p):
        t = p[1]
        # TODO: does this give the correct overwrite order?
        # Presumably, repeating the same axis should obey the last one.
        dim_type = p[0].value['axis']
        t.value[dim_type] = p[0].value['dimen']
        return t

    @pg.production('rule_specification : optional_spaces')
    def rule_specification_empty(p):
        dims = {'width': None, 'height': None, 'depth': None}
        return BuiltToken(type_='rule_specification', value=dims,
                          position_like=p)

    # TODO: these literals are getting unclear. Introduce some convention to
    # make clear which (non-terminal) tokens represent literals.
    @pg.production('rule_dimension : width dimen')
    @pg.production('rule_dimension : height dimen')
    @pg.production('rule_dimension : depth dimen')
    def rule_dimension(p):
        return BuiltToken(type_='rule_dimension',
                          value={'axis': p[0].value, 'dimen': p[1]},
                          position_like=p)

    @pg.production(get_literal_production_rule('width'))
    @pg.production(get_literal_production_rule('height'))
    @pg.production(get_literal_production_rule('depth'))
    def literal_dimension(p):
        return make_literal_token(p)

    @pg.production('file_name : character')
    @pg.production('file_name : file_name character')
    def file_name(p):
        # TODO: Move this logic out of parser.
        if len(p) > 1:
            s = p[0].value + p[1].value['char']
        else:
            s = p[0].value['char']
        return BuiltToken(type_='file_name',
                          value=s,
                          position_like=p)
