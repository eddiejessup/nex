from ..tokens import BuiltToken
from ..constants.units import Unit, MuUnit, InternalUnit

from . import utils as pu


def digit_coll_to_size_tok(dc, parents):
    new_dec_const_tok = BuiltToken(type_='decimal_constant',
                                   value=dc,
                                   parents=parents)
    new_size_tok = BuiltToken(type_='size', value=new_dec_const_tok,
                              parents=parents)
    return new_size_tok


def add_dimen_rules(pg):
    @pg.production('mu_dimen : optional_signs unsigned_mu_dimen')
    @pg.production('dimen : optional_signs unsigned_dimen')
    def maybe_mu_dimen(p):
        return BuiltToken(type_='dimen',
                          value={'signs': p[0], 'size': p[1]},
                          parents=p)

    @pg.production('unsigned_mu_dimen : normal_mu_dimen')
    @pg.production('unsigned_mu_dimen : coerced_mu_dimen')
    @pg.production('unsigned_dimen : normal_dimen')
    @pg.production('unsigned_dimen : coerced_dimen')
    def maybe_mu_unsigned_dimen(p):
        return p[0]

    @pg.production('coerced_dimen : internal_glue')
    @pg.production('coerced_mu_dimen : internal_mu_glue')
    def maybe_mu_coerced_dimen(p):
        raise NotImplementedError

    @pg.production('normal_dimen : internal_dimen')
    def normal_dimen_internal(p):
        return p[0]

    @pg.production('normal_mu_dimen : factor mu_unit')
    @pg.production('normal_dimen : factor unit_of_measure')
    def normal_maybe_mu_dimen_explicit(p):
        dimen = BuiltToken(type_='dimen',
                           value={'factor': p[0], 'unit': p[1].value},
                           parents=p)
        return BuiltToken(type_='size',
                          value=dimen,
                          parents=p)

    @pg.production('internal_dimen : DIMEN_PARAMETER')
    @pg.production('internal_dimen : dimen_register')
    @pg.production('internal_dimen : SPECIAL_DIMEN')
    @pg.production('internal_dimen : LAST_KERN')
    def internal_dimen(p):
        return BuiltToken(type_='size', value=p[0], parents=p)

    @pg.production('internal_dimen : box_dimension number')
    def internal_dimen_box_dimen(p):
        box_reg_token = BuiltToken(type_=p[0].type, value=p[1], parents=p)
        return BuiltToken(type_='size', value=box_reg_token, parents=p)

    @pg.production('box_dimension : BOX_DIMEN_HEIGHT')
    @pg.production('box_dimension : BOX_DIMEN_WIDTH')
    @pg.production('box_dimension : BOX_DIMEN_DEPTH')
    def box_dimension(p):
        return p[0]

    @pg.production('factor : normal_integer')
    @pg.production('factor : decimal_constant')
    def factor_number(p):
        return p[0]

    @pg.production('decimal_constant : COMMA')
    def decimal_constant_comma(p):
        digit_coll = pu.DigitCollection(base=10)
        return digit_coll_to_size_tok(digit_coll, parents=p)

    @pg.production('decimal_constant : POINT')
    def decimal_constant_point(p):
        digit_coll = pu.DigitCollection(base=10)
        digit_coll.digits = [p[0]]
        return digit_coll_to_size_tok(digit_coll, parents=p)

    @pg.production('decimal_constant : digit decimal_constant')
    def decimal_constant_prepend(p):
        size_tok = p[1]
        dec_const_tok = size_tok.value
        digit_coll = dec_const_tok.value
        digit_coll.digits = [p[0]] + digit_coll.digits
        return digit_coll_to_size_tok(digit_coll, parents=p)

    @pg.production('decimal_constant : decimal_constant digit')
    def decimal_constant_append(p):
        size_tok = p[0]
        dec_const_tok = size_tok.value
        digit_coll = dec_const_tok.value
        digit_coll.digits = digit_coll.digits + [p[1]]
        return digit_coll_to_size_tok(digit_coll, parents=p)

    @pg.production(pu.get_literal_production_rule('mu', target='mu_unit') + ' one_optional_space')
    def unit_of_mu_measure(p):
        return BuiltToken(type_='unit_of_measure',
                          value={'unit': MuUnit.mu},
                          parents=p)

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
                          value={'unit': p[0].value},
                          parents=p)

    @pg.production(pu.get_literal_production_rule('em'))
    def em(p):
        return BuiltToken(type_='internal_unit',
                          value=InternalUnit.em,
                          parents=p)

    @pg.production(pu.get_literal_production_rule('ex'))
    def ex(p):
        return BuiltToken(type_='internal_unit',
                          value=InternalUnit.ex,
                          parents=p)

    @pg.production('unit_of_measure : optional_true physical_unit one_optional_space')
    def unit_of_measure(p):
        is_true = p[0] is not None
        if is_true:
            assert p[0].value == 'true'
        return BuiltToken(type_='unit_of_measure',
                          value={'unit': p[1].value, 'true': is_true},
                          parents=p)

    @pg.production('optional_true : true')
    @pg.production('optional_true : empty')
    def optional_true(p):
        return p[0]

    @pg.production(pu.get_literal_production_rule('true'))
    def literal_true(p):
        return pu.make_literal_token(p)

    def make_unit_tok(unit, p):
        return BuiltToken(type_='physical_unit', value=unit, parents=p)

    @pg.production(pu.get_literal_production_rule('pt', target='physical_unit'))
    def physical_unit_point(p):
        return make_unit_tok(Unit.point, p)

    @pg.production(pu.get_literal_production_rule('pc', target='physical_unit'))
    def physical_unit_pica(p):
        return make_unit_tok(Unit.pica, p)

    @pg.production(pu.get_literal_production_rule('in', target='physical_unit'))
    def physical_unit_inch(p):
        return make_unit_tok(Unit.inch, p)

    @pg.production(pu.get_literal_production_rule('bp', target='physical_unit'))
    def physical_unit_big_point(p):
        return make_unit_tok(Unit.big_point, p)

    @pg.production(pu.get_literal_production_rule('cm', target='physical_unit'))
    def physical_unit_centimetre(p):
        return make_unit_tok(Unit.centimetre, p)

    @pg.production(pu.get_literal_production_rule('mm', target='physical_unit'))
    def physical_unit_millimetre(p):
        return make_unit_tok(Unit.millimetre, p)

    @pg.production(pu.get_literal_production_rule('dd', target='physical_unit'))
    def physical_unit_didot_point(p):
        return make_unit_tok(Unit.didot_point, p)

    @pg.production(pu.get_literal_production_rule('cc', target='physical_unit'))
    def physical_unit_cicero(p):
        return make_unit_tok(Unit.cicero, p)

    @pg.production(pu.get_literal_production_rule('sp', target='physical_unit'))
    def physical_unit_scaled_point(p):
        return make_unit_tok(Unit.scaled_point, p)
