from .rply import ParserGenerator

from .common import BuiltToken
from .typer import PhysicalUnit, terminal_token_types
from .special_quantities import special_quantity_types
from .tex_parameters import parameter_types, glue_keys
from .registers import register_token_type_to_register_type

from .character_parsing import add_character_productions


terminal_token_types += parameter_types
terminal_token_types += special_quantity_types

prec = (
    ('left', 'SPACE'),
)


pg = ParserGenerator(terminal_token_types,
                     precedence=prec,
                     cache_id="changeme")


class DigitCollection(object):

    def __init__(self, base):
        self.base = base
        self.digits = []


@pg.production('control_sequence : UNEXPANDED_MANY_CHAR_CONTROL_SEQUENCE')
@pg.production('control_sequence : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE')
def control_sequence(p):
    return p[0]


@pg.production('control_sequence : ACTIVE_CHARACTER')
def control_sequence_active(p):
    # We will prefix active characters with @.
    # This really needs changing, but will do for now.
    v = p[0]
    v.value['name'] = v.value['char']
    return v


add_character_productions(pg)


@pg.production('token_variable : token_register')
@pg.production('mu_glue_variable : mu_skip_register')
@pg.production('glue_variable : skip_register')
@pg.production('dimen_variable : dimen_register')
@pg.production('integer_variable : count_register')
def quantity_variable_register(p):
    return p[0]


@pg.production('token_variable : TOKEN_PARAMETER')
@pg.production('mu_glue_variable : MU_GLUE_PARAMETER')
@pg.production('glue_variable : GLUE_PARAMETER')
@pg.production('dimen_variable : DIMEN_PARAMETER')
@pg.production('integer_variable : INTEGER_PARAMETER')
def quantity_variable_parameter(p):
    return p[0]


@pg.production('token_register : TOKS number')
@pg.production('mu_skip_register : MU_SKIP number')
@pg.production('skip_register : SKIP number')
@pg.production('dimen_register : DIMEN number')
@pg.production('count_register : COUNT number')
def register_explicit(p):
    return BuiltToken(type_=p[0].type, value=p[1].value['size'],
                      position_like=p[0])


@pg.production('token_register : TOKS_DEF_TOKEN')
@pg.production('mu_skip_register : MU_SKIP_DEF_TOKEN')
@pg.production('skip_register : SKIP_DEF_TOKEN')
@pg.production('dimen_register : DIMEN_DEF_TOKEN')
@pg.production('count_register : COUNT_DEF_TOKEN')
def register_token(p):
    type_ = register_token_type_to_register_type(p[0].type)
    return BuiltToken(type_=type_, value=p[0].value,
                      position_like=p[0])


def _make_maybe_mu_glue_token(type_, p):
    # Wrap up arguments in a dict.
    dimens = dict(zip(glue_keys, tuple(p)))
    return BuiltToken(type_=type_, value=dimens,
                      position_like=p[0])


@pg.production('mu_glue : mu_dimen mu_stretch mu_shrink')
def mu_glue(p):
    return _make_maybe_mu_glue_token('mu_glue', p)


@pg.production('glue : dimen stretch shrink')
def glue(p):
    return _make_maybe_mu_glue_token('glue', p)


@pg.production('shrink : minus dimen')
@pg.production('shrink : minus fil_dimen')
@pg.production('stretch : plus dimen')
@pg.production('stretch : plus fil_dimen')
@pg.production('mu_shrink : minus mu_dimen')
@pg.production('mu_shrink : minus fil_dimen')
@pg.production('mu_stretch : plus mu_dimen')
@pg.production('mu_stretch : plus fil_dimen')
def stretch_or_shrink_non_stated(p):
    return p[1]


@pg.production('stretch : optional_spaces')
@pg.production('shrink : optional_spaces')
@pg.production('mu_stretch : optional_spaces')
@pg.production('mu_shrink : optional_spaces')
def stretch_or_shrink_omitted(p):
    return BuiltToken(type_='dimen',
                      value={'sign': '+',
                             'size': BuiltToken(type_='size', value=0)},
                      position_like=p[0])


@pg.production('fil_dimen : optional_signs factor fil_unit optional_spaces')
def fil_dimen(p):
    size_token = BuiltToken(type_='fil_size',
                            value={'factor': p[1], 'unit': p[2]},
                            position_like=p[1])
    return BuiltToken(type_='dimen', value={'sign': p[0], 'size': size_token},
                      position_like=p[1])


@pg.production('fil_unit : fil_unit NON_ACTIVE_UNCASED_l')
def fil_unit_append(p):
    # Add one infinity for every letter 'l'.
    unit = p[0]
    unit['number_of_fils'] += 1
    return unit


@pg.production('fil_unit : fil')
def fil_unit(p):
    # I don't think true matters, but we add it for compatibility
    # with non-weird units.
    unit = {'unit': PhysicalUnit.fil, 'true': True,
            'number_of_fils': 1}
    return unit


def _make_quantity_token(type_, p):
    '''Small helper to avoid repetition.'''
    return BuiltToken(type_=type_, value={'sign': p[0], 'size': p[1]},
                      position_like=p[1])


@pg.production('mu_dimen : optional_signs unsigned_mu_dimen')
def mu_dimen(p):
    return _make_quantity_token('mu_dimen', p)


@pg.production('dimen : optional_signs unsigned_dimen')
def dimen(p):
    return _make_quantity_token('dimen', p)


@pg.production('number : optional_signs unsigned_number')
def number(p):
    return _make_quantity_token('number', p)


@pg.production('unsigned_mu_dimen : normal_mu_dimen')
@pg.production('unsigned_mu_dimen : coerced_mu_dimen')
@pg.production('unsigned_dimen : normal_dimen')
@pg.production('unsigned_dimen : coerced_dimen')
def maybe_mu_unsigned_dimen(p):
    return p[0]


@pg.production('coerced_dimen : internal_glue')
@pg.production('coerced_mu_dimen : internal_mu_glue')
def maybe_mu_coerced_dimen(p):
    return p[0]


@pg.production('unsigned_number : normal_integer')
@pg.production('unsigned_number : coerced_integer')
def unsigned_number(p):
    return p[0]


@pg.production('coerced_integer : internal_dimen')
def coerced_integer_dimen(p):
    return p[0]


@pg.production('coerced_integer : internal_glue')
def coerced_integer_glue(p):
    import pdb; pdb.set_trace()


@pg.production('normal_integer : internal_integer')
def normal_integer_internal_integer(p):
    return p[0]


@pg.production('normal_dimen : internal_dimen')
def normal_dimen_internal_dimen(p):
    return p[0]


# Special quantities.

@pg.production('internal_integer : SPECIAL_INTEGER')
@pg.production('internal_dimen : SPECIAL_DIMEN')
def internal_quantity_special(p):
    return p[0]


@pg.production('internal_mu_glue : mu_skip_register')
@pg.production('internal_glue : skip_register')
@pg.production('internal_dimen : dimen_register')
@pg.production('internal_integer : count_register')
def internal_quantity_register(p):
    return p[0]


@pg.production('internal_integer : CHAR_DEF_TOKEN')
@pg.production('internal_integer : MATH_CHAR_DEF_TOKEN')
def internal_integer_weird_short_hand_token(p):
    # TODO: add other kinds of internal integer.
    return p[0]


@pg.production('internal_mu_glue : MU_GLUE_PARAMETER')
@pg.production('internal_glue : GLUE_PARAMETER')
@pg.production('internal_dimen : DIMEN_PARAMETER')
@pg.production('internal_integer : INTEGER_PARAMETER')
def internal_quantity_parameter(p):
    return p[0]


@pg.production('internal_dimen : box_dimension number')
def internal_dimen_box_dimension(p):
    # TODO: Implement this.
    box_dimen_type = p[0].type
    return BuiltToken(type_='box_dimen', value=1,
                      position_like=p[0])


@pg.production('box_dimension : BOX_DIMEN_HEIGHT')
@pg.production('box_dimension : BOX_DIMEN_WIDTH')
@pg.production('box_dimension : BOX_DIMEN_DEPTH')
def box_dimension(p):
    return p[0]


@pg.production('normal_integer : integer_constant one_optional_space')
def normal_integer_integer(p):
    return p[0]


@pg.production('normal_mu_dimen : factor mu_unit')
def normal_mu_dimen_explicit(p):
    return BuiltToken(type_='normal_mu_dimen',
                      value={'factor': p[0], 'unit': p[1]},
                      position_like=p[0])


@pg.production('normal_dimen : factor unit_of_measure')
def normal_dimen_explicit(p):
    return BuiltToken(type_='normal_dimen',
                      value={'factor': p[0], 'unit': p[1]},
                      position_like=p[0])


@pg.production('factor : normal_integer')
def factor_integer(p):
    return p[0]


@pg.production('factor : decimal_constant')
def factor_decimal_constant(p):
    return p[0]


@pg.production('decimal_constant : COMMA')
def decimal_constant_comma(p):
    dc = DigitCollection(base=10)
    return BuiltToken(type_='decimal_constant', value=dc,
                      position_like=p[0])


@pg.production('decimal_constant : POINT')
def decimal_constant_point(p):
    dc = DigitCollection(base=10)
    dc.digits = [p[0]]
    return BuiltToken(type_='decimal_constant', value=dc,
                      position_like=p[0])


@pg.production('decimal_constant : digit decimal_constant')
def decimal_constant_prepend(p):
    dc = p[1].value
    dc.digits = [p[0]] + dc.digits
    return BuiltToken(type_='decimal_constant', value=dc,
                      position_like=p[0])


@pg.production('decimal_constant : decimal_constant digit')
def decimal_constant_append(p):
    dc = p[0].value
    dc.digits = dc.digits + [p[1]]
    return BuiltToken(type_='decimal_constant', value=dc,
                      position_like=p[0])


@pg.production('unit_of_measure : optional_spaces internal_unit')
def unit_of_measure_internal(p):
    return p[1]


@pg.production('internal_unit : em one_optional_space')
@pg.production('internal_unit : ex one_optional_space')
# @pg.production('internal_unit : internal_integer')
# @pg.production('internal_unit : internal_dimen')
# @pg.production('internal_unit : internal_glue')
def internal_unit(p):
    return {'unit': p[0]}


@pg.production('unit_of_measure : optional_true physical_unit one_optional_space')
def unit_of_measure(p):
    return {'unit': p[1], 'true': bool(p[0])}


@pg.production('optional_true : true')
@pg.production('optional_true : empty')
def optional_true(p):
    return p[0]


@pg.production('normal_integer : SINGLE_QUOTE octal_constant one_optional_space')
@pg.production('normal_integer : DOUBLE_QUOTE hexadecimal_constant one_optional_space')
def normal_integer_weird_base(p):
    t = p[1]
    t._copy_position_from_token(p[0])
    return t


@pg.production('normal_integer : BACKTICK character_token one_optional_space')
def normal_integer_character(p):
    return BuiltToken(type_='backtick_integer', value=p[1],
                      position_like=p[0])


@pg.production('character_token : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE')
@pg.production('character_token : character')
# TODO: make this possible.
# @pg.production('character_token : ACTIVE_CHARACTER')
def character_token_character(p):
    return p[0]


def process_integer_digits(p, base):
    if len(p) > 1:
        token = p[1]
        collection = token.value
    else:
        collection = DigitCollection(base=base)
    # We work right-to-left, so the new digit should be added on the left.
    collection.digits = [p[0]] + collection.digits
    new_token = BuiltToken(type_='integer_constant', value=collection,
                           position_like=p[0])
    return new_token


@pg.production('hexadecimal_constant : hexadecimal_digit')
@pg.production('hexadecimal_constant : hexadecimal_digit hexadecimal_constant')
def hexadecimal_constant(p):
    return process_integer_digits(p, base=16)


@pg.production('integer_constant : digit')
@pg.production('integer_constant : digit integer_constant')
def integer_constant(p):
    return process_integer_digits(p, base=10)


@pg.production('octal_constant : octal_digit')
@pg.production('octal_constant : octal_digit octal_constant')
def octal_constant(p):
    return process_integer_digits(p, base=8)


@pg.production('hexadecimal_digit : digit')
@pg.production('hexadecimal_digit : A')
@pg.production('hexadecimal_digit : B')
@pg.production('hexadecimal_digit : C')
@pg.production('hexadecimal_digit : D')
@pg.production('hexadecimal_digit : E')
@pg.production('hexadecimal_digit : F')
def hexadecimal_digit(p):
    return p[0]


@pg.production('digit : octal_digit')
@pg.production('digit : EIGHT')
@pg.production('digit : NINE')
def digit(p):
    return p[0]


@pg.production('octal_digit : ZERO')
@pg.production('octal_digit : ONE')
@pg.production('octal_digit : TWO')
@pg.production('octal_digit : THREE')
@pg.production('octal_digit : FOUR')
@pg.production('octal_digit : FIVE')
@pg.production('octal_digit : SIX')
@pg.production('octal_digit : SEVEN')
def octal_digit(p):
    return p[0]


@pg.production('one_optional_space : SPACE')
@pg.production('one_optional_space : empty')
def one_optional_space(p):
    return None


@pg.production('optional_signs : optional_spaces')
@pg.production('optional_signs : optional_signs plus_or_minus optional_spaces')
def optional_signs(p):
    flip_sign = lambda s: '+' if s == '-' else '-'
    if len(p) > 1:
        v = p[1]
        if v == '-':
            return flip_sign(p[0])
    else:
        return '+'


@pg.production('plus_or_minus : PLUS_SIGN')
@pg.production('plus_or_minus : MINUS_SIGN')
def plus_or_minus(p):
    return p[0].value['char']


@pg.production('equals : optional_spaces')
@pg.production('equals : optional_spaces EQUALS')
def equals(p):
    return None


@pg.production('optional_spaces : SPACE optional_spaces')
@pg.production('optional_spaces : empty')
def optional_spaces(p):
    return None


@pg.production('empty :')
def empty(p):
    return None
