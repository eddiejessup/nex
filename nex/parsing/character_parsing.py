from ..tokens import BuiltToken
from ..constants.units import PhysicalUnit, MuUnit, InternalUnit
from ..constants.primitive_control_sequences import Instructions
from ..lex_typer import non_active_letters_map


letter_to_non_active_uncased_type_map = {}
for c, instr in non_active_letters_map.items():
    type_ = instr.value
    #  For hex characters, need to look for the composite production, not the
    #  terminal production, because could be, for example, 'A' or
    #  'NON_ACTIVE_UNCASED_a', so we should look for the composite production,
    #  'non_active_uncased_a'.
    if c in ('A', 'B', 'C', 'D', 'E', 'F'):
        type_ = type_.lower()
    letter_to_non_active_uncased_type_map[c] = type_


normal_char_types = (
    Instructions.misc_char_cat_pair.value,
    Instructions.equals.value,
    Instructions.greater_than.value,
    Instructions.less_than.value,
    Instructions.plus_sign.value,
    Instructions.minus_sign.value,
    Instructions.zero.value,
    Instructions.one.value,
    Instructions.two.value,
    Instructions.three.value,
    Instructions.four.value,
    Instructions.five.value,
    Instructions.six.value,
    Instructions.seven.value,
    Instructions.eight.value,
    Instructions.nine.value,
    Instructions.single_quote.value,
    Instructions.double_quote.value,
    Instructions.backtick.value,
    Instructions.comma.value,
    Instructions.point.value,
) + tuple(letter_to_non_active_uncased_type_map.values())


def word_to_pr(word, target=None):
    if target is None:
        target = word
    rule = ' '.join(letter_to_non_active_uncased_type_map[c] for c in word)
    return '{} : {}'.format(target, rule)


def wrap(pg, func, rule):
    f = pg.production(rule)
    func = f(func)
    return func


def make_literal_token(p):
    s = ''.join(t.value['char'] for t in p)
    return BuiltToken(type_='literal', value=s,
                      position_like=p)


def add_character_productions(pg):

    # Add production for each instruction that may act as a 'character'
    # production.
    def character(p):
        return BuiltToken(type_='character', value=p[0].value,
                          position_like=p)
    for char_type in normal_char_types:
        rule = 'character : {}'.format(char_type)
        character = wrap(pg, character, rule)

    @pg.production(word_to_pr('by'))
    def by(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('true'))
    def true(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('minus'))
    def minus(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('plus'))
    def plus(p):
        return make_literal_token(p)

    # Font related.

    @pg.production(word_to_pr('at'))
    def at(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('scaled'))
    def scaled(p):
        return make_literal_token(p)

    # Box related.

    @pg.production(word_to_pr('to'))
    def to(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('spread'))
    def spread(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('width'))
    def width(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('height'))
    def height(p):
        return make_literal_token(p)

    @pg.production(word_to_pr('depth'))
    def depth(p):
        return make_literal_token(p)

    # Unit related.

    @pg.production(word_to_pr('em'))
    def em(p):
        return InternalUnit.em

    @pg.production(word_to_pr('ex'))
    def ex(p):
        return InternalUnit.em

    @pg.production(word_to_pr('mu', target='mu_unit') + ' one_optional_space')
    def unit_of_mu_measure(p):
        return BuiltToken(type_='unit_of_measure',
                          value={'unit': MuUnit.mu},
                          position_like=p)

    @pg.production(word_to_pr('fil'))
    def fil(p):
        # Represents the number of infinities.
        # Obviously that's a sentence that should appear in a program
        # about type-setting...
        return make_literal_token(p)

    def physical_unit(p):
        string = ''.join([t.value['char'] for t in p])
        return BuiltToken(type_='physical_unit',
                          value=PhysicalUnit(string),
                          position_like=p)
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
