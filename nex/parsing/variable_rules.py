from ..tokens import BuiltToken

from ..accessors import short_hand_reg_def_token_type_to_reg_type


def add_variable_rules(pg):
    @pg.production('token_variable : token_register')
    @pg.production('mu_glue_variable : mu_skip_register')
    @pg.production('glue_variable : skip_register')
    @pg.production('dimen_variable : dimen_register')
    @pg.production('integer_variable : count_register')
    def quantity_variable_register(p):
        return p[0]

    @pg.production('token_variable : TOKEN_PARAMETER')
    @pg.production('mu_glue_variable : MU_GLUE_PARAMETER')
    @pg.production('glue_variable : GLUE_PARAMETER')
    @pg.production('dimen_variable : DIMEN_PARAMETER')
    @pg.production('integer_variable : INTEGER_PARAMETER')
    def quantity_variable_parameter(p):
        return p[0]

    @pg.production('token_register : TOKS number')
    @pg.production('mu_skip_register : MU_SKIP number')
    @pg.production('skip_register : SKIP number')
    @pg.production('dimen_register : DIMEN number')
    @pg.production('count_register : COUNT number')
    def quantity_register_explicit(p):
        return BuiltToken(type_=p[0].type, value=p[1], position_like=p)

    @pg.production('token_register : TOKS_DEF_TOKEN')
    @pg.production('mu_skip_register : MU_SKIP_DEF_TOKEN')
    @pg.production('skip_register : SKIP_DEF_TOKEN')
    @pg.production('dimen_register : DIMEN_DEF_TOKEN')
    @pg.production('count_register : COUNT_DEF_TOKEN')
    def register_token(p):
        reg_type = short_hand_reg_def_token_type_to_reg_type[p[0].type]
        internal_nr_tok = BuiltToken(type_='internal_number',
                                     value=p[0].value)
        nr_tok = BuiltToken(type_='number', value=internal_nr_tok)
        return BuiltToken(type_=reg_type, value=nr_tok, position_like=p)
