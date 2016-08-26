from rply import ParserGenerator

from common import Token

from expander import (terminal_primitive_control_sequences_map,
                      short_hand_def_to_token_map,
                      composite_terminal_control_sequence_types)
from registers import registers
from typer import literal_types, PhysicalUnit, units_in_scaled_points, unexpanded_cs_types


from character_parsing import add_character_productions

tokens = ()
tokens += tuple(terminal_primitive_control_sequences_map.values())
tokens += tuple(short_hand_def_to_token_map.values())
tokens += tuple(literal_types)
tokens += tuple(unexpanded_cs_types)
tokens += tuple(composite_terminal_control_sequence_types)
tokens = tuple(set(tokens))

prec = (
    ('left', 'SPACE'),
    # ('left', 'UNEXPANDED_CONTROL_SEQUENCE'),
)


pg = ParserGenerator(tokens,
                     precedence=prec,
                     cache_id="changeme")


class DigitCollection(object):

    def __init__(self, base):
        self.base = base
        self.digits = []


def evaluate_size(size_token):
    if isinstance(size_token, Token):
        if size_token.type == 'backtick_integer':
            unexpanded_token = size_token.value
            if unexpanded_token.type == 'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE':
                # If we have a single character control sequence in this context,
                # it is just a way of specifying a character in a way that
                # won't invoke its special effects.
                char = unexpanded_token.value
            elif unexpanded_token.type == 'character':
                char = unexpanded_token.value['char']
            else:
                import pdb; pdb.set_trace()
            return ord(char)
        elif size_token.type == 'control_sequence':
            # size_token = lexer.state.control_sequences[name]
            raise NotImplementedError
        elif size_token.type == 'count':
            return registers.count[size_token.value]
        elif size_token.type == 'dimen':
            return registers.dimen[size_token.value]
        else:
            import pdb; pdb.set_trace()
    else:
        return size_token


def evaluate_number(number_token):
    size_token = number_token['size']
    number = evaluate_size(size_token)
    sign = number_token['sign']
    if sign == '-':
        number *= -1
    return number


def evaluate_dimen(dimen_token):
    size_token, sign = dimen_token['size'], dimen_token['sign']
    number_of_units_token = size_token.value['factor']
    unit_token = size_token.value['unit']
    number_of_units = evaluate_size(number_of_units_token)
    unit, is_true_unit = unit_token['unit'], unit_token['true']
    number_of_scaled_points = units_in_scaled_points[unit] * number_of_units
    # TODO: deal with 'true' and 'not-true' scales properly
    mag_parameter = 1000.0
    if is_true_unit:
        number_of_scaled_points *= 1000.0 / mag_parameter
    if sign == '-':
        number_of_scaled_points *= -1
    return number_of_scaled_points


@pg.production('character : MISC_CHAR_CAT_PAIR')
@pg.production('character : EQUALS')
@pg.production('character : GREATER_THAN')
@pg.production('character : LESS_THAN')
@pg.production('character : PLUS_SIGN')
@pg.production('character : MINUS_SIGN')
@pg.production('character : ZERO')
@pg.production('character : ONE')
@pg.production('character : TWO')
@pg.production('character : THREE')
@pg.production('character : FOUR')
@pg.production('character : FIVE')
@pg.production('character : SIX')
@pg.production('character : SEVEN')
@pg.production('character : EIGHT')
@pg.production('character : NINE')
@pg.production('character : A')
@pg.production('character : B')
@pg.production('character : C')
@pg.production('character : D')
@pg.production('character : E')
@pg.production('character : F')
@pg.production('character : SINGLE_QUOTE')
@pg.production('character : DOUBLE_QUOTE')
@pg.production('character : BACKTICK')
def character(parser_state, p):
    return Token(type_='character', value=p[0].value)


@pg.production('control_sequence : UNEXPANDED_CONTROL_SEQUENCE')
@pg.production('control_sequence : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE')
def control_sequence(parser_state, p):
    return Token(type_=p[0].type, value={'name': p[0].value})


@pg.production('control_sequence : ACTIVE_CHARACTER')
def control_sequence_active(parser_state, p):
    # We will prefix active characters with @.
    # This really needs changing, but will do for now.
    v = p[0]
    v.value['name'] = v.value['char']
    return v


add_character_productions(pg)


@pg.production('glue_variable : skip_register')
def glue_variable_register(parser_state, p):
    return p[0]


@pg.production('dimen_variable : dimen_register')
def dimen_variable_register(parser_state, p):
    return p[0]


@pg.production('integer_variable : count_register')
def integer_variable_count(parser_state, p):
    return p[0]


@pg.production('count_register : COUNT number')
def count_register_explicit(parser_state, p):
    return Token(type_='count', value=p[1]['size'])


@pg.production('skip_register : SKIP_DEF_TOKEN')
def skip_register_token(parser_state, p):
    return Token(type_='skip', value=p[0].value)


@pg.production('dimen_register : DIMEN_DEF_TOKEN')
def dimen_register_token(parser_state, p):
    return Token(type_='dimen', value=p[0].value)


@pg.production('count_register : COUNT_DEF_TOKEN')
def count_register_token(parser_state, p):
    return Token(type_='count', value=p[0].value)


@pg.production('glue : dimen stretch shrink')
def glue(parser_state, p):
    import pdb; pdb.set_trace()


@pg.production('stretch : plus dimen')
@pg.production('stretch : optional_spaces')
# TODO: plus fil dimen
def stretch(parser_state, p):
    import pdb; pdb.set_trace()


@pg.production('shrink : minus dimen')
@pg.production('shrink : optional_spaces')
# TODO: plus fil dimen
def shrink(parser_state, p):
    import pdb; pdb.set_trace()


@pg.production('dimen : optional_signs unsigned_dimen')
def dimen(parser_state, p):
    return {'sign': p[0], 'size': p[1]}


@pg.production('number : optional_signs unsigned_number')
def number(parser_state, p):
    return {'sign': p[0], 'size': p[1]}


@pg.production('unsigned_number : normal_integer')
# @pg.production('unsigned_number : coerced_integer')
def unsigned_number(parser_state, p):
    return p[0]


@pg.production('unsigned_dimen : normal_dimen')
# @pg.production('unsigned_dimen : coerced_dimen')
def unsigned_dimen(parser_state, p):
    return p[0]


def get_integer_constant(collection):
    try:
        chars = [t.value['char'] for t in collection.digits]
    except TypeError:
        import pdb; pdb.set_trace()

    s = ''.join(chars)
    return int(s, base=collection.base)


def get_real_decimal_constant(collection):
    # Our function assumes the digits are in base 10.
    assert collection.base == 10
    chars = [t.value['char'] for t in collection.digits]
    s = ''.join(chars)
    return float(s)


@pg.production('normal_integer : internal_integer')
def normal_integer_internal_integer(parser_state, p):
    return p[0]


@pg.production('normal_dimen : internal_dimen')
def normal_dimen_internal_dimen(parser_state, p):
    return p[0]


@pg.production('internal_integer : CHAR_DEF_TOKEN')
@pg.production('internal_integer : MATH_CHAR_DEF_TOKEN')
def internal_integer_short_hand_token(parser_state, p):
    return p[0].value


@pg.production('internal_dimen : DIMEN_DEF_TOKEN')
def internal_dimen_short_hand_token(parser_state, p):
    return p[0].value


@pg.production('internal_integer : count_register')
def internal_integer_count_register(parser_state, p):
    # TODO: add other kinds of internal integer.
    return p[0]


@pg.production('normal_integer : integer_constant one_optional_space')
def normal_integer_integer(parser_state, p):
    return get_integer_constant(p[0])


@pg.production('normal_dimen : factor unit_of_measure')
def normal_dimen_explicit(parser_state, p):
    return Token(type_='normal_dimen',
                 value={'factor': p[0], 'unit': p[1]})


@pg.production('factor : normal_integer')
def factor_integer(parser_state, p):
    return p[0]


@pg.production('factor : decimal_constant')
def factor_decimal_constant(parser_state, p):
    return get_real_decimal_constant(p[0])


@pg.production('decimal_constant : COMMA')
def decimal_constant_comma(parser_state, p):
    return DigitCollection(base=10)


@pg.production('decimal_constant : POINT')
def decimal_constant_point(parser_state, p):
    v = DigitCollection(base=10)
    v.digits = [p[0]]
    return v


@pg.production('decimal_constant : digit decimal_constant')
def decimal_constant_prepend(parser_state, p):
    v = p[1]
    v.digits = [p[0]] + v.digits
    return v


@pg.production('decimal_constant : decimal_constant digit')
def decimal_constant_append(parser_state, p):
    v = p[0]
    v.digits = v.digits + [p[1]]
    return v


@pg.production('unit_of_measure : optional_true physical_unit one_optional_space')
def unit_of_measure(parser_state, p):
    return {'unit': p[1], 'true': bool(p[0])}


@pg.production('optional_true : true')
@pg.production('optional_true : empty')
def optional_true(parser_state, p):
    return p[0]


@pg.production('normal_integer : SINGLE_QUOTE octal_constant one_optional_space')
@pg.production('normal_integer : DOUBLE_QUOTE hexadecimal_constant one_optional_space')
def normal_integer_weird_base(parser_state, p):
    return get_integer_constant(p[1])


@pg.production('normal_integer : BACKTICK character_token one_optional_space')
def normal_integer_character(parser_state, p):
    return Token(type_='backtick_integer', value=p[1])


@pg.production('character_token : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE')
@pg.production('character_token : character')
# TODO: make this possible.
# @pg.production('character_token : ACTIVE_CHARACTER')
def character_token_character(parser_state, p):
    return p[0]


def process_integer_digits(p, base):
    if len(p) > 1:
        collection = p[1]
    else:
        collection = DigitCollection(base=base)
    # We work right-to-left, so the new digit should be added on the left.
    collection.digits = [p[0]] + collection.digits
    return collection


@pg.production('hexadecimal_constant : hexadecimal_digit')
@pg.production('hexadecimal_constant : hexadecimal_digit hexadecimal_constant')
def hexadecimal_constant(parser_state, p):
    return process_integer_digits(p, base=16)


@pg.production('integer_constant : digit')
@pg.production('integer_constant : digit integer_constant')
def integer_constant(parser_state, p):
    return process_integer_digits(p, base=10)


@pg.production('octal_constant : octal_digit')
@pg.production('octal_constant : octal_digit octal_constant')
def octal_constant(parser_state, p):
    return process_integer_digits(p, base=8)


@pg.production('hexadecimal_digit : digit')
@pg.production('hexadecimal_digit : A')
@pg.production('hexadecimal_digit : B')
@pg.production('hexadecimal_digit : C')
@pg.production('hexadecimal_digit : D')
@pg.production('hexadecimal_digit : E')
@pg.production('hexadecimal_digit : F')
def hexadecimal_digit(parser_state, p):
    return p[0]


@pg.production('digit : octal_digit')
@pg.production('digit : EIGHT')
@pg.production('digit : NINE')
def digit(parser_state, p):
    return p[0]


@pg.production('octal_digit : ZERO')
@pg.production('octal_digit : ONE')
@pg.production('octal_digit : TWO')
@pg.production('octal_digit : THREE')
@pg.production('octal_digit : FOUR')
@pg.production('octal_digit : FIVE')
@pg.production('octal_digit : SIX')
@pg.production('octal_digit : SEVEN')
def octal_digit(parser_state, p):
    return p[0]


@pg.production('one_optional_space : SPACE')
@pg.production('one_optional_space : empty')
def one_optional_space(parser_state, p):
    return None


@pg.production('optional_signs : optional_spaces')
@pg.production('optional_signs : optional_signs plus_or_minus optional_spaces')
def optional_signs(parser_state, p):
    flip_sign = lambda s: '+' if s == '-' else '-'
    if len(p) > 1:
        v = p[1]
        if v == '-':
            return flip_sign(v)
    else:
        return '+'


@pg.production('plus_or_minus : PLUS_SIGN')
@pg.production('plus_or_minus : MINUS_SIGN')
def plus_or_minus(parser_state, p):
    return p[0].value['char']


# @pg.production('equals : optional_spaces')
# @pg.production('equals : optional_spaces')
# @pg.production('equals : optional_spaces EQUALS')
@pg.production('equals : EQUALS')
def eq(parser_state, p):
    return None


@pg.production('optional_spaces : SPACE optional_spaces')
@pg.production('optional_spaces : empty')
def optional_spaces(parser_state, p):
    return None


@pg.production('empty :')
def empty(parser_state, p):
    return None
