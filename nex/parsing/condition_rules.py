from ..tokens import BuiltToken


def add_condition_rules(pg):
    @pg.production('condition : IF_NUM number relation number')
    def condition_if_num(p):
        return BuiltToken(
            type_=p[0].type,
            value={'left_number': p[1],
                   'right_number': p[3],
                   'relation': p[2]},
            parents=p,
        )

    @pg.production('condition : IF_DIMEN dimen relation dimen')
    def condition_if_dimen(p):
        return BuiltToken(
            type_=p[0].type,
            value={'left_dimen': p[1],
                   'right_dimen': p[3],
                   'relation': p[2]},
            parents=p,
        )

    @pg.production('condition : IF_ODD number')
    def condition_if_odd(p):
        return BuiltToken(
            type_=p[0].type,
            value={'number': p[1]},
            parents=p
        )

    @pg.production('condition : IF_V_MODE')
    @pg.production('condition : IF_H_MODE')
    @pg.production('condition : IF_M_MODE')
    @pg.production('condition : IF_INNER_MODE')
    def condition_if_mode(p):
        return BuiltToken(
            type_=p[0].type,
            value=None,
            parents=p
        )

    # @pg.production('condition : IF_CHAR somethingsomething')
    # def condition_if_char(p):
    #     return BuiltToken(type_=p[0].type, value=None)

    # @pg.production('condition : IF_CAT somethingsomething')
    # def condition_if_cat(p):
    #     return BuiltToken(type_=p[0].type, value=None)

    # @pg.production('condition : IF_TOKEN somethingsomething')
    # def condition_if_token(p):
    #     return BuiltToken(type_=p[0].type, value=None)

    @pg.production('condition : IF_VOID number')
    @pg.production('condition : IF_H_BOX number')
    @pg.production('condition : IF_V_BOX number')
    def condition_if_box(p):
        return BuiltToken(
            type_=p[0].type,
            value={'number': p[1]},
            parents=p,
        )

    @pg.production('condition : IF_END_OF_FILE number')
    def condition_if_end_of_file(p):
        return BuiltToken(
            type_=p[0].type,
            value={'number': p[1]},
            parents=p,
        )

    @pg.production('condition : IF_TRUE')
    @pg.production('condition : IF_FALSE')
    def condition_if_boolean(p):
        return BuiltToken(
            type_=p[0].type,
            value=None,
            parents=p,
        )

    @pg.production('condition : IF_CASE number')
    def condition_if_case(p):
        return BuiltToken(
            type_=p[0].type,
            value={'number': p[1]},
            parents=p,
        )

    @pg.production('relation : LESS_THAN')
    @pg.production('relation : EQUALS')
    @pg.production('relation : GREATER_THAN')
    def relation(p):
        return p[0]
