from ..tokens import BuiltToken

from . import utils as pu


def add_character_rules(pg):
    @pg.production('one_optional_space : SPACE')
    @pg.production('one_optional_space : empty')
    def one_optional_space(p):
        return None

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
    @pg.production('character : SINGLE_QUOTE')
    @pg.production('character : DOUBLE_QUOTE')
    @pg.production('character : BACKTICK')
    @pg.production('character : COMMA')
    @pg.production('character : POINT')
    def character(p):
        return BuiltToken(type_='character', value=p[0].value,
                          parents=p)

    # Add character productions for letters.
    for letter_type in pu.letter_to_non_active_uncased_type_map.values():
        rule = 'character : {}'.format(letter_type)
        character = pu.wrap(pg, character, rule)

    # We split out some types of these letters for parsing into hexadecimal
    # constants. Here we allow them to be considered as normal characters.
    @pg.production('non_active_uncased_a : A')
    @pg.production('non_active_uncased_a : NON_ACTIVE_UNCASED_A')
    @pg.production('non_active_uncased_b : B')
    @pg.production('non_active_uncased_b : NON_ACTIVE_UNCASED_B')
    @pg.production('non_active_uncased_c : C')
    @pg.production('non_active_uncased_c : NON_ACTIVE_UNCASED_C')
    @pg.production('non_active_uncased_d : D')
    @pg.production('non_active_uncased_d : NON_ACTIVE_UNCASED_D')
    @pg.production('non_active_uncased_e : E')
    @pg.production('non_active_uncased_e : NON_ACTIVE_UNCASED_E')
    @pg.production('non_active_uncased_f : F')
    @pg.production('non_active_uncased_f : NON_ACTIVE_UNCASED_F')
    def non_active_uncased_hex_letter(p):
        return p[0]

    @pg.production('optional_spaces : SPACE optional_spaces')
    @pg.production('optional_spaces : empty')
    def optional_spaces(p):
        return None
