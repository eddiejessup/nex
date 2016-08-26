from common import Token
from typer import PhysicalUnit, non_active_literals, hex_letters_map

words = [
    'by',
    'true',
    'minus',
    'plus',
]


letter_to_non_active_uncased_type_map = {}
for c in non_active_literals:
    token_type = 'NON_ACTIVE_UNCASED_{}'.format(c)
    if c.upper() in hex_letters_map.values():
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


def add_character_productions(pg):

    def character(parser_state, p):
        return Token(type_='character', value=p[0].value)
    for char_type in normal_char_types:
        rule = 'character : {}'.format(char_type)
        f = pg.production(rule)
        character = f(character)

    @pg.production(word_to_pr('fil'))
    def fil(parser_state, p):
        # Represents the number of infinities.
        # Obviously that's a sentence that should appear in a program
        # about type-setting...
        return 1

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

    @pg.production(word_to_pr('pt', target='physical_unit'))
    def physical_unit(parser_state, p):
        return PhysicalUnit.point

    @pg.production('non_active_uncased_b : B')
    @pg.production('non_active_uncased_b : NON_ACTIVE_UNCASED_b')
    def non_active_uncased_b(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_e : NON_ACTIVE_UNCASED_e')
    @pg.production('non_active_uncased_e : E')
    def non_active_uncased_e(parser_state, p):
        return p[0]

    @pg.production('non_active_uncased_f : NON_ACTIVE_UNCASED_f')
    @pg.production('non_active_uncased_f : F')
    def non_active_uncased_f(parser_state, p):
        return p[0]
