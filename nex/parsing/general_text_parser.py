from ..rply import ParserGenerator

from ..tokens import BuiltToken

term_types = ['SPACE', 'RELAX', 'LEFT_BRACE', 'BALANCED_TEXT_AND_RIGHT_BRACE']
gen_txt_pg = ParserGenerator(term_types, cache_id="general_text")


@gen_txt_pg.production('general_text : filler LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
def general_text(p):
    return BuiltToken(type_='general_text', value=p[2].value,
                      position_like=p)


@gen_txt_pg.production('filler : optional_spaces')
@gen_txt_pg.production('filler : filler RELAX optional_spaces')
def filler(p):
    return None


@gen_txt_pg.production('optional_spaces : SPACE optional_spaces')
@gen_txt_pg.production('optional_spaces : empty')
def optional_spaces(p):
    return None


@gen_txt_pg.production('empty :')
def empty(p):
    return None


general_text_parser = gen_txt_pg.build()
