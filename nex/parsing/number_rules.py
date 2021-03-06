from ..tokens import BuiltToken

from . import utils as pu


def process_integer_digits(p, base):
    if len(p) > 1:
        constant_token = p[1]
        collection = constant_token.value
    else:
        collection = pu.DigitCollection(base=base)
    # We work right-to-left, so the new digit should be added on the left.
    new_digit = p[0]
    collection.digits = [new_digit] + collection.digits
    return BuiltToken(type_='integer_constant', value=collection,
                      parents=p)


def add_number_rules(pg):
    @pg.production('number : optional_signs unsigned_number')
    def number(p):
        return BuiltToken(type_='number',
                          value={'signs': p[0], 'size': p[1]},
                          parents=p)

    @pg.production('unsigned_number : normal_integer')
    @pg.production('unsigned_number : coerced_integer')
    def unsigned_number(p):
        return p[0]

    @pg.production('coerced_integer : internal_dimen')
    def coerced_integer_dimen(p):
        return p[0]

    @pg.production('coerced_integer : internal_glue')
    def coerced_integer_glue(p):
        raise NotImplementedError

    @pg.production('normal_integer : internal_integer')
    def normal_integer_internal(p):
        return p[0]

    @pg.production('normal_integer : integer_constant one_optional_space')
    def normal_integer_integer(p):
        return BuiltToken(type_='size', value=p[0], parents=p)

    @pg.production('normal_integer : SINGLE_QUOTE octal_constant one_optional_space')
    @pg.production('normal_integer : DOUBLE_QUOTE hexadecimal_constant one_optional_space')
    def normal_integer_weird_base(p):
        return BuiltToken(type_='size', value=p[1], parents=p)

    @pg.production('normal_integer : BACKTICK character_token one_optional_space')
    def normal_integer_character(p):
        bt = BuiltToken(type_='backtick', value=p[1], parents=p)
        return BuiltToken(type_='size', value=bt, parents=p)

    @pg.production('internal_integer : INTEGER_PARAMETER')
    @pg.production('internal_integer : count_register')
    @pg.production('internal_integer : SPECIAL_INTEGER')
    @pg.production('internal_integer : CHAR_DEF_TOKEN')
    @pg.production('internal_integer : MATH_CHAR_DEF_TOKEN')
    @pg.production('internal_integer : LAST_PENALTY')
    def internal_integer(p):
        return BuiltToken(type_='size',
                          value=p[0],
                          parents=p)

    @pg.production('character_token : UNEXPANDED_CONTROL_SYMBOL')
    @pg.production('character_token : character')
    @pg.production('character_token : ACTIVE_CHARACTER')
    def character_token_character(p):
        return p[0]

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

    @pg.production('optional_signs : optional_spaces')
    def optional_signs_omitted(p):
        return BuiltToken(type_='signs', value=[],
                          parents=p)

    @pg.production('optional_signs : optional_signs plus_or_minus optional_spaces')
    def optional_signs(p):
        t = p[0]
        t.value.append(p[1])
        return t

    @pg.production('plus_or_minus : PLUS_SIGN')
    @pg.production('plus_or_minus : MINUS_SIGN')
    def plus_or_minus(p):
        return p[0]

    @pg.production('equals : optional_spaces')
    @pg.production('equals : optional_spaces EQUALS')
    def equals(p):
        return BuiltToken(type_='optional_equals', value=None,
                          parents=p)
