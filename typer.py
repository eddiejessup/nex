from lexer import CatCode


literals_map = {
    ('=', CatCode.other): 'EQUALS',
    ('+', CatCode.other): 'PLUS_SIGN',
    ('-', CatCode.other): 'MINUS_SIGN',

    ('0', CatCode.other): 'ZERO',
    ('1', CatCode.other): 'ONE',
    ('2', CatCode.other): 'TWO',
    ('3', CatCode.other): 'THREE',
    ('4', CatCode.other): 'FOUR',
    ('5', CatCode.other): 'FIVE',
    ('6', CatCode.other): 'SIX',
    ('7', CatCode.other): 'SEVEN',
    ('8', CatCode.other): 'EIGHT',
    ('9', CatCode.other): 'NINE',
    ('A', CatCode.other): 'A',
    ('B', CatCode.other): 'B',
    ('C', CatCode.other): 'C',
    ('D', CatCode.other): 'D',
    ('E', CatCode.other): 'E',
    ('F', CatCode.other): 'F',
    ('A', CatCode.letter): 'A',
    ('B', CatCode.letter): 'B',
    ('C', CatCode.letter): 'C',
    ('D', CatCode.letter): 'D',
    ('E', CatCode.letter): 'E',
    ('F', CatCode.letter): 'F',

    ('\'', CatCode.other): 'SINGLE_QUOTE',
    ('"', CatCode.other): 'DOUBLE_QUOTE',
    ('`', CatCode.other): 'BACKTICK',
}


category_map = {
    CatCode.space: 'SPACE',
    CatCode.begin_group: 'LEFT_BRACE',
    CatCode.end_group: 'RIGHT_BRACE',
    CatCode.active: 'ACTIVE_CHARACTER',
}


# tokens += tuple(set(literals_map.values()))


def get_char_cat_pair_terminal_type(char_cat_pair_token):
    v = char_cat_pair_token.value
    char, cat = v['char'], v['cat']
    if cat in (CatCode.letter, CatCode.other):
        if (char, cat) in literals_map:
            terminal_token_type = literals_map[(char, cat)]
        else:
            terminal_token_type = 'MISC_CHAR_CAT_PAIR'
    elif cat in category_map:
        terminal_token_type = category_map[cat]
    return terminal_token_type
