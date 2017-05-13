from ..tokens import BuiltToken

from . import utils as pu


def process_integer_digits(p, base):
    if len(p) > 1:
        size_token = p[1]
        constant_token = size_token.value
        collection = constant_token.value
    else:
        collection = pu.DigitCollection(base=base)
    # We work right-to-left, so the new digit should be added on the left.
    new_digit = p[0]
    collection.digits = [new_digit] + collection.digits
    new_constant_token = BuiltToken(type_='integer_constant', value=collection,
                                    position_like=p)
    new_size_token = BuiltToken(type_='size', value=new_constant_token)
    return new_size_token


def add_number_rules(pg):
    @pg.production('number : optional_signs unsigned_number')
    def number(p):
        return BuiltToken(type_='number',
                          value={'sign': p[0], 'size': p[1]},
                          position_like=p)

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
        # TODO: Make size token here, rather than in integer_constant
        return p[0]

    @pg.production('normal_integer : SINGLE_QUOTE octal_constant one_optional_space')
    @pg.production('normal_integer : DOUBLE_QUOTE hexadecimal_constant one_optional_space')
    def normal_integer_weird_base(p):
        t = p[1]
        t._copy_position_from_token(p)
        return t

    @pg.production('normal_integer : BACKTICK character_token one_optional_space')
    def normal_integer_character(p):
        bt = BuiltToken(type_='backtick', value=p[1], position_like=p)
        return BuiltToken(type_='size', value=bt, position_like=p)

    @pg.production('internal_integer : INTEGER_PARAMETER')
    @pg.production('internal_integer : count_register')
    @pg.production('internal_integer : SPECIAL_INTEGER')
    @pg.production('internal_integer : CHAR_DEF_TOKEN')
    @pg.production('internal_integer : MATH_CHAR_DEF_TOKEN')
    def internal_integer(p):
        return BuiltToken(type_='size',
                          value=p[0],
                          position_like=p)

    @pg.production('character_token : UNEXPANDED_CONTROL_SYMBOL')
    @pg.production('character_token : character')
    # TODO: make this possible.
    # @pg.production('character_token : ACTIVE_CHARACTER')
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
    @pg.production('optional_signs : optional_signs plus_or_minus optional_spaces')
    def optional_signs(p):
        def flip_sign(s):
            return '+' if s == '-' else '-'

        if len(p) > 1:
            added_s = p[1].value
            if added_s == '-':
                current_s = p[0].value
                s = flip_sign(current_s)
        else:
            s = '+'
        return BuiltToken(type_='sign', value=s,
                          position_like=p)

    @pg.production('plus_or_minus : PLUS_SIGN')
    @pg.production('plus_or_minus : MINUS_SIGN')
    def plus_or_minus(p):
        return BuiltToken(type_='sign', value=p[0].value['char'],
                          position_like=p)

    @pg.production('equals : optional_spaces')
    @pg.production('equals : optional_spaces EQUALS')
    def equals(p):
        return BuiltToken(type_='optional_equals', value=None,
                          position_like=p)
