from common import Token
from typer import PhysicalUnit, MuUnit, non_active_literals_map, hex_letters_map


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

    def character(parser_state, p):
        return Token(type_='character', value=p[0].value)
    for char_type in normal_char_types:
        rule = 'character : {}'.format(char_type)
        character = wrap(pg, character, rule)

    @pg.production(word_to_pr('by'))
    def by(parser_state, p):
        return None

    @pg.production(word_to_pr('true'))
    def true(parser_state, p):
        return True

    @pg.production(word_to_pr('minus'))
    def minus(parser_state, p):
        return None

    @pg.production(word_to_pr('plus'))
    def plus(parser_state, p):
        return None

    @pg.production(word_to_pr('mu', target='mu_unit') + ' one_optional_space')
    def unit_of_mu_measure(parser_state, p):
        return {'unit': MuUnit.mu}

    @pg.production(word_to_pr('fil'))
    def fil(parser_state, p):
        # Represents the number of infinities.
        # Obviously that's a sentence that should appear in a program
        # about type-setting...
        return 1

    def physical_unit(parser_state, p):
        string = ''.join([t.value['char'] for t in p])
        return PhysicalUnit(string)
    for unit in PhysicalUnit:
        if unit == PhysicalUnit.fil:
            continue
        rule = word_to_pr(unit.value, target='physical_unit')
        physical_unit = wrap(pg, physical_unit, rule)

    @pg.production('non_active_uncased_a : A')
    @pg.production('non_active_uncased_a : NON_ACTIVE_UNCASED_a')
    def non_active_uncased_a(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_b : B')
    @pg.production('non_active_uncased_b : NON_ACTIVE_UNCASED_b')
    def non_active_uncased_b(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_c : C')
    @pg.production('non_active_uncased_c : NON_ACTIVE_UNCASED_c')
    def non_active_uncased_c(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_d : D')
    @pg.production('non_active_uncased_d : NON_ACTIVE_UNCASED_d')
    def non_active_uncased_d(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_e : NON_ACTIVE_UNCASED_e')
    @pg.production('non_active_uncased_e : E')
    def non_active_uncased_e(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_f : NON_ACTIVE_UNCASED_f')
    @pg.production('non_active_uncased_f : F')
    def non_active_uncased_f(parser_state, p):
        return p[0]
