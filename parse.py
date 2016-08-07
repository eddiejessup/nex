import logging

import ply.yacc as yacc
from ply.lex import Lexer, LexToken

from process import State, chars, CatCode


logger = logging.getLogger(__name__)

tokens = (
    'CAT_CODE',
    'SINGLE_CHAR_CONTROL_SEQUENCE',
    'CONTROL_SEQUENCE',
    'SPACE',
)


literals_map = {
    '=': 'EQUALS',
    '+': 'PLUS_SIGN',
    '-': 'MINUS_SIGN',

    '0': 'ZERO',
    '1': 'ONE',
    '2': 'TWO',
    '3': 'THREE',
    '4': 'FOUR',
    '5': 'FIVE',
    '6': 'SIX',
    '7': 'SEVEN',
    '8': 'EIGHT',
    '9': 'NINE',
    'A': 'A',
    'B': 'B',
    'C': 'C',
    'C': 'C',
    'D': 'D',
    'E': 'E',
    'F': 'F',

    '\'': 'SINGLE_QUOTE',
    '"': 'DOUBLE_QUOTE',
    '`': 'BACKTICK',
}


tokens += tuple(literals_map.values())


class DigitCollection(object):

    def __init__(self, base):
        self.base = base
        self.digits = []


class PLYLexer(Lexer):

    def input(self, chars):
        self.state = State(chars)
        self.state_tokens = self.state.get_tokens()

    def token(self):
        try:
            state_token = next(self.state_tokens)
        except StopIteration:
            return
        value = state_token
        if state_token['type'] == 'control_sequence':
            name = state_token['name']
            if name == 'catcode':
                type_ = 'CAT_CODE'
            elif len(name) == 1:
                type_ = 'SINGLE_CHAR_CONTROL_SEQUENCE'
            else:
                type_ = 'CONTROL_SEQUENCE'
        elif state_token['type'] == 'char_cat_pair':
            char, cat = state_token['char'], state_token['cat']
            if char in literals_map and cat == CatCode.other:
                type_ = literals_map[char]
            elif cat == CatCode.space:
                type_ = 'SPACE'
            else:
                type_ = 'EQUALS'
            if char == '3':
                import pdb; pdb.set_trace()
        token = PLYToken(type_, value)
        logger.info(token)
        return token


class PLYToken(LexToken):

    def __init__(self, type_, value):
        self.type = type_
        self.value = value
        self.lineno = None
        self.lexpos = None

    def __repr__(self):
        return "<Token: %r %r>" % (self.type, self.value)

    def __str__(self):
        return self.__repr__()


lexer = PLYLexer()


def is_control_sequence(value):
    return isinstance(value, dict) and value['type'] == 'control_sequence'


def evaluate_control_sequence(name):
    if len(name) == 1:
        return ord(name)
    else:
        raise NotImplementedError


def evaluate(value):
    if is_control_sequence(value):
        name = value['name']
        value = evaluate_control_sequence(name)
    return value


def p_document_extend(p):
    '''
    document : document command
    '''
    p[0] = p[1]
    p[0].append(p[2])


def p_document(p):
    '''
    document : command
    '''
    p[0] = [p[1]]


def p_command(p):
    '''
    command : cat_code
    '''
    p[0] = p[1]


def p_cat_code(p):
    '''
    cat_code : CAT_CODE number EQUALS number
    '''
    char_code, cat_num = evaluate(p[2]['size']), evaluate(p[4]['size'])
    char = chr(char_code)
    cat_code = CatCode(cat_num)
    lexer.state.char_to_cat[char] = cat_code
    p[0] = {'type': 'cat_code', 'char': char, 'cat': cat_code}


def p_number(p):
    '''
    number : optional_signs unsigned_number
    '''
    p[0] = {'sign': p[1], 'size': p[2]}


def p_unsigned_number(p):
    '''
    unsigned_number : normal_integer
    '''
    # | coerced_integer
    p[0] = p[1]


def get_constant(constant):
    return int(constant['digits'], base=constant['base'])


def p_normal_integer_integer(p):
    '''
    normal_integer : integer_constant one_optional_space
    '''
    p[0] = get_constant(p[1])


def p_normal_integer_weird_base(p):
    '''
    normal_integer : SINGLE_QUOTE octal_constant one_optional_space
                   | DOUBLE_QUOTE hexadecimal_constant one_optional_space
    '''
    p[0] = get_constant(p[2])


def p_normal_integer_character(p):
    '''
    normal_integer : BACKTICK character_token one_optional_space
    '''
    p[0] = p[2]


def p_character_token(p):
    '''
    character_token : SINGLE_CHAR_CONTROL_SEQUENCE
    '''
    '''
                    | char_cat_pair
    '''
    p[0] = p[1]


def process_digits(p, base):
    new_digit = p[1]['char']
    if len(p) > 2:
        constant = p[2]
        constant['digits'] += new_digit
    else:
        constant = {
            'base': base,
            'digits': new_digit
        }
    return constant


def p_hexadecimal_constant(p):
    '''
    hexadecimal_constant : hexadecimal_digit
                         | hexadecimal_digit hexadecimal_constant
    '''
    p[0] = process_digits(p, base=16)


def p_integer_constant(p):
    '''
    integer_constant : digit
                     | digit integer_constant
    '''
    p[0] = process_digits(p, base=10)


def p_octal_constant(p):
    '''
    octal_constant : octal_digit
                   | octal_digit octal_constant
    '''
    p[0] = process_digits(p, base=8)


def p_hexadecimal_digit(p):
    '''
    hexadecimal_digit : digit
                      | A
                      | B
                      | C
                      | D
                      | E
                      | F
    '''
    p[0] = p[1]


def p_digit(p):
    '''
    digit : octal_digit
          | EIGHT
          | NINE
    '''
    p[0] = p[1]


def p_octal_digit(p):
    '''
    octal_digit : ZERO
                | ONE
                | TWO
                | THREE
                | FOUR
                | FIVE
                | SIX
                | SEVEN
    '''
    p[0] = p[1]


def p_one_optional_space(p):
    '''
    one_optional_space : SPACE
                       |  empty
    '''
    pass


def p_optional_signs(p):
    '''
    optional_signs : optional_spaces
                   | optional_signs plus_or_minus optional_spaces
    '''
    flip_sign = lambda s: '+' if s == '-' else '-'
    if len(p) > 2:
        p[0] = p[2]
        if p[1] == '-':
            p[0] = flip_sign(p[0])
    else:
        p[0] = '+'


def p_plus_or_minus(p):
    '''
    plus_or_minus : PLUS_SIGN
                  | MINUS_SIGN
    '''
    p[0] = p[1]['char']


def p_optional_spaces(p):
    '''
    optional_spaces : empty
                    | SPACE optional_spaces
    '''
    pass


def p_empty(p):
    '''
    empty :
    '''
    pass


# Error rule for syntax errors
def p_error(p):
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc(debug=True)

result = parser.parse(chars, lexer=lexer)
# result = parser.parse(s)
print(result)
