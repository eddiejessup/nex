from ..tokens import BuiltToken
from ..units import PhysicalUnit, MuUnit, InternalUnit
from ..tex_parameters import glue_keys

from . import utils as pu


def digit_coll_to_size_tok(dc, position_like):
    new_dec_const_tok = BuiltToken(type_='decimal_constant',
                                   value=dc,
                                   position_like=position_like)
    new_size_tok = BuiltToken(type_='size', value=new_dec_const_tok,
                              position_like=position_like)
    return new_size_tok


def add_dimen_literals(pg):

    @pg.production('normal_mu_dimen : factor mu_unit')
    @pg.production('normal_dimen : factor unit_of_measure')
    def normal_maybe_mu_dimen_explicit(p):
        dimen = BuiltToken(type_='dimen',
                           value={'factor': p[0], 'unit': p[1].value},
                           position_like=p)
        return BuiltToken(type_='size',
                          value=dimen,
                          position_like=p)

    @pg.production(pu.get_literal_production_rule('mu', target='mu_unit') + ' one_optional_space')
    def unit_of_mu_measure(p):
        return BuiltToken(type_='unit_of_measure',
                          value={'unit': MuUnit.mu},
                          position_like=p)

    @pg.production('factor : normal_integer')
    @pg.production('factor : decimal_constant')
    def factor_number(p):
        return p[0]

    @pg.production('decimal_constant : COMMA')
    def decimal_constant_comma(p):
        digit_coll = pu.DigitCollection(base=10)
        return digit_coll_to_size_tok(digit_coll, position_like=p)

    @pg.production('decimal_constant : POINT')
    def decimal_constant_point(p):
        digit_coll = pu.DigitCollection(base=10)
        digit_coll.digits = [p[0]]
        return digit_coll_to_size_tok(digit_coll, position_like=p)

    @pg.production('decimal_constant : digit decimal_constant')
    def decimal_constant_prepend(p):
        size_tok = p[1]
        dec_const_tok = size_tok.value
        digit_coll = dec_const_tok.value
        digit_coll.digits = [p[0]] + digit_coll.digits
        return digit_coll_to_size_tok(digit_coll, position_like=p)

    @pg.production('decimal_constant : decimal_constant digit')
    def decimal_constant_append(p):
        size_tok = p[0]
        dec_const_tok = size_tok.value
        digit_coll = dec_const_tok.value
        digit_coll.digits = digit_coll.digits + [p[1]]
        return digit_coll_to_size_tok(digit_coll, position_like=p)

    @pg.production('unit_of_measure : optional_spaces internal_unit')
    def unit_of_measure_internal(p):
        return p[1]

    @pg.production('internal_unit : em one_optional_space')
    @pg.production('internal_unit : ex one_optional_space')
    # @pg.production('internal_unit : internal_integer')
    # @pg.production('internal_unit : internal_dimen')
    # @pg.production('internal_unit : internal_glue')
    def internal_unit(p):
        return BuiltToken(type_='unit_of_measure',
                          value={'unit': p[0]},
                          position_like=p)

    @pg.production(pu.get_literal_production_rule('em'))
    def em(p):
        return InternalUnit.em

    @pg.production(pu.get_literal_production_rule('ex'))
    def ex(p):
        return InternalUnit.ex

    @pg.production('unit_of_measure : optional_true physical_unit one_optional_space')
    def unit_of_measure(p):
        is_true = p[0] is not None
        if is_true:
            assert p[0].value == 'true'
        return BuiltToken(type_='unit_of_measure',
                          value={'unit': p[1].value, 'true': is_true},
                          position_like=p)

    @pg.production('optional_true : true')
    @pg.production('optional_true : empty')
    def optional_true(p):
        return p[0]

    @pg.production(pu.get_literal_production_rule('true'))
    def literal(p):
        return pu.make_literal_token(p)

    @pg.production(pu.get_literal_production_rule('pt', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('pc', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('in', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('bp', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('cm', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('mm', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('dd', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('cc', target='physical_unit'))
    @pg.production(pu.get_literal_production_rule('sp', target='physical_unit'))
    def physical_unit(p):
        unit = PhysicalUnit(''.join([t.value['char'] for t in p]))
        return BuiltToken(type_='physical_unit',
                          value=unit,
                          position_like=p)


def add_glue_literals(pg):
    @pg.production('mu_glue : mu_dimen mu_stretch mu_shrink')
    @pg.production('glue : dimen stretch shrink')
    def glue_explicit(p):
        # Wrap up arguments in a dict.
        dimens = dict(zip(glue_keys, tuple(p)))
        glue_spec = BuiltToken(type_='explicit', value=dimens, position_like=p)
        return BuiltToken(type_='glue', value=glue_spec, position_like=p)

    @pg.production('shrink : minus dimen')
    @pg.production('shrink : minus fil_dimen')
    @pg.production('stretch : plus dimen')
    @pg.production('stretch : plus fil_dimen')
    @pg.production('mu_shrink : minus mu_dimen')
    @pg.production('mu_shrink : minus fil_dimen')
    @pg.production('mu_stretch : plus mu_dimen')
    @pg.production('mu_stretch : plus fil_dimen')
    def stretch_or_shrink(p):
        return p[1]

    @pg.production('stretch : optional_spaces')
    @pg.production('shrink : optional_spaces')
    @pg.production('mu_stretch : optional_spaces')
    @pg.production('mu_shrink : optional_spaces')
    def stretch_or_shrink_omitted(p):
        dimen_size_token = BuiltToken(type_='internal',
                                      value=0,
                                      position_like=p)
        size_token = BuiltToken(type_='size',
                                value=dimen_size_token,
                                position_like=p)
        sign_token = BuiltToken(type_='sign', value='+', position_like=p)
        return BuiltToken(type_='dimen', value={'sign': sign_token,
                                                'size': size_token},
                          position_like=p)

    @pg.production('fil_dimen : optional_signs factor fil_unit optional_spaces')
    def fil_dimen(p):
        dimen_size_token = BuiltToken(type_='dimen',
                                      value={'factor': p[1], 'unit': p[2].value},
                                      position_like=p)
        size_token = BuiltToken(type_='size',
                                value=dimen_size_token,
                                position_like=p)
        return BuiltToken(type_='dimen', value={'sign': p[0], 'size': size_token},
                          position_like=p)

    @pg.production('fil_unit : fil_unit NON_ACTIVE_UNCASED_l')
    def fil_unit_append(p):
        # Add one infinity for every letter 'l'.
        unit = p[0]
        unit.value['number_of_fils'] += 1
        return unit

    @pg.production('fil_unit : fil')
    def fil_unit(p):
        unit = {'unit': PhysicalUnit.fil, 'number_of_fils': 1}
        return BuiltToken(type_='fil_unit',
                          value=unit,
                          position_like=p)

    @pg.production(pu.get_literal_production_rule('minus'))
    @pg.production(pu.get_literal_production_rule('plus'))
    @pg.production(pu.get_literal_production_rule('fil'))
    def literal(p):
        return pu.make_literal_token(p)
