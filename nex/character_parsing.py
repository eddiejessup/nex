from .common import BuiltToken
from .typer import (PhysicalUnit, MuUnit, InternalUnit,
                    non_active_literals_map, hex_letters_map)


letter_to_non_active_uncased_type_map = {}
for c, token_type in non_active_literals_map.items():
    if c in hex_letters_map.values():
        token_type = token_type.lower()
    letter_to_non_active_uncased_type_map[c] = token_type


normal_char_types = (
    'MISC_CHAR_CAT_PAIR',
    'EQUALS',
    'GREATER_THAN',
    'LESS_THAN',
    'PLUS_SIGN',
    'MINUS_SIGN',
    'ZERO',
    'ONE',
    'TWO',
    'THREE',
    'FOUR',
    'FIVE',
    'SIX',
    'SEVEN',
    'EIGHT',
    'NINE',
    'SINGLE_QUOTE',
    'DOUBLE_QUOTE',
    'BACKTICK',
    'COMMA',
    'POINT',
)
normal_char_types += tuple(letter_to_non_active_uncased_type_map.values())


def word_to_pr(word, target=None):
    if target is None:
        target = word
    rule = ' '.join(letter_to_non_active_uncased_type_map[c] for c in word)
    return '{} : {}'.format(target, rule)


def wrap(pg, func, rule):
    f = pg.production(rule)
    func = f(func)
    return func


def add_character_productions(pg):

    def character(p):
        return BuiltToken(type_='character', value=p[0].value,
                          position_like=p[0])
    for char_type in normal_char_types:
        rule = 'character : {}'.format(char_type)
        character = wrap(pg, character, rule)

    @pg.production(word_to_pr('by'))
    def by(p):
        return None

    @pg.production(word_to_pr('true'))
    def true(p):
        return True

    @pg.production(word_to_pr('minus'))
    def minus(p):
        return None

    @pg.production(word_to_pr('plus'))
    def plus(p):
        return None

    # Font related.

    @pg.production(word_to_pr('at'))
    def at(p):
        return None

    @pg.production(word_to_pr('scaled'))
    def scaled(p):
        return None

    # Box related.

    @pg.production(word_to_pr('to'))
    def to(p):
        return None

    @pg.production(word_to_pr('spread'))
    def spread(p):
        return None

    @pg.production(word_to_pr('width'))
    def width(p):
        return 'width'

    @pg.production(word_to_pr('height'))
    def height(p):
        return 'height'

    @pg.production(word_to_pr('depth'))
    def depth(p):
        return 'depth'

    # Unit related.

    @pg.production(word_to_pr('em'))
    def em(p):
        return InternalUnit.em

    @pg.production(word_to_pr('ex'))
    def ex(p):
        return InternalUnit.em

    @pg.production(word_to_pr('mu', target='mu_unit') + ' one_optional_space')
    def unit_of_mu_measure(p):
        return {'unit': MuUnit.mu}

    @pg.production(word_to_pr('fil'))
    def fil(p):
        # Represents the number of infinities.
        # Obviously that's a sentence that should appear in a program
        # about type-setting...
        return 1

    def physical_unit(p):
        string = ''.join([t.value['char'] for t in p])
        return PhysicalUnit(string)
    for unit in PhysicalUnit:
        if unit == PhysicalUnit.fil:
            continue
        rule = word_to_pr(unit.value, target='physical_unit')
        physical_unit = wrap(pg, physical_unit, rule)

    # We split out some types of these letters for parsing into hexadecimal
    # constants. Here we allow them to be considered as normal characters.

    @pg.production('non_active_uncased_a : A')
    @pg.production('non_active_uncased_a : NON_ACTIVE_UNCASED_a')
    def non_active_uncased_a(p):
        return p[0]

    @pg.production('non_active_uncased_b : B')
    @pg.production('non_active_uncased_b : NON_ACTIVE_UNCASED_b')
    def non_active_uncased_b(p):
        return p[0]

    @pg.production('non_active_uncased_c : C')
    @pg.production('non_active_uncased_c : NON_ACTIVE_UNCASED_c')
    def non_active_uncased_c(p):
        return p[0]

    @pg.production('non_active_uncased_d : D')
    @pg.production('non_active_uncased_d : NON_ACTIVE_UNCASED_d')
    def non_active_uncased_d(p):
        return p[0]

    @pg.production('non_active_uncased_e : NON_ACTIVE_UNCASED_e')
    @pg.production('non_active_uncased_e : E')
    def non_active_uncased_e(p):
        return p[0]

    @pg.production('non_active_uncased_f : NON_ACTIVE_UNCASED_f')
    @pg.production('non_active_uncased_f : F')
    def non_active_uncased_f(p):
        return p[0]
