from ..tokens import BuiltToken
from ..constants.units import Unit
from ..accessors import glue_keys

from . import utils as pu


def add_glue_rules(pg):
    @pg.production('mu_glue : internal_mu_glue')
    @pg.production('glue : internal_glue')
    def glue_internal(p):
        return BuiltToken(type_='glue', value=p[0], parents=p)

    @pg.production('mu_glue : mu_dimen mu_stretch mu_shrink')
    @pg.production('glue : dimen stretch shrink')
    def glue_explicit(p):
        # Wrap up arguments in a dict.
        dimens = dict(zip(glue_keys, tuple(p)))
        glue_spec = BuiltToken(type_='explicit', value=dimens, parents=p)
        return BuiltToken(type_='glue', value=glue_spec, parents=p)

    @pg.production('internal_mu_glue : mu_skip_register')
    @pg.production('internal_glue : skip_register')
    @pg.production('internal_mu_glue : MU_GLUE_PARAMETER')
    @pg.production('internal_mu_glue : LAST_GLUE')
    @pg.production('internal_glue : GLUE_PARAMETER')
    @pg.production('internal_glue : LAST_GLUE')
    def internal_glue(p):
        return p[0]

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
                                      parents=p)
        size_token = BuiltToken(type_='size',
                                value=dimen_size_token,
                                parents=p)
        sign_token = BuiltToken(type_='signs', value=[], parents=p)
        return BuiltToken(type_='dimen', value={'signs': sign_token,
                                                'size': size_token},
                          parents=p)

    @pg.production('fil_dimen : optional_signs factor fil_unit optional_spaces')
    def fil_dimen(p):
        dimen_size_token = BuiltToken(type_='dimen',
                                      value={'factor': p[1], 'unit': p[2].value},
                                      parents=p)
        size_token = BuiltToken(type_='size',
                                value=dimen_size_token,
                                parents=p)
        return BuiltToken(type_='dimen', value={'signs': p[0], 'size': size_token},
                          parents=p)

    @pg.production('fil_unit : fil_unit NON_ACTIVE_UNCASED_L')
    def fil_unit_append(p):
        # Add one infinity for every letter 'l'.
        unit = p[0]
        unit.value['number_of_fils'] += 1
        return unit

    @pg.production('fil_unit : fil')
    def fil_unit(p):
        unit = {'unit': Unit.fil, 'number_of_fils': 1}
        return BuiltToken(type_='fil_unit',
                          value=unit,
                          parents=p)

    @pg.production(pu.get_literal_production_rule('minus'))
    @pg.production(pu.get_literal_production_rule('plus'))
    @pg.production(pu.get_literal_production_rule('fil'))
    def literal(p):
        return pu.make_literal_token(p)
