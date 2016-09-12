from common_parsing import pg as common_pg


gen_txt_pg = common_pg.copy_to_extend()


@gen_txt_pg.production('general_text : filler LEFT_BRACE BALANCED_TEXT_AND_RIGHT_BRACE')
def general_text(parser_state, p):
    return p[2]


@gen_txt_pg.production('filler : optional_spaces')
@gen_txt_pg.production('filler : filler RELAX optional_spaces')
def filler(parser_state, p):
    return None


general_text_parser = gen_txt_pg.build()
