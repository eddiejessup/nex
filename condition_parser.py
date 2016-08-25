import logging
import yacc
import operator

from common import Token
from registers import registers

from expander import terminal_primitive_control_sequences_map, short_hand_def_map
from typer import literal_types, unexpanded_cs_types


short_hand_def_to_token_map = {
    k: '{}_TOKEN'.format(k)
    for k in short_hand_def_map.values()
}


tokens = ()
tokens += tuple(terminal_primitive_control_sequences_map.values())
tokens += tuple(short_hand_def_to_token_map.values())
tokens += tuple(literal_types)
tokens += tuple(unexpanded_cs_types)
tokens = tuple(set(tokens))

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


class DigitCollection(object):

    def __init__(self, base):
        self.base = base
        self.digits = []


def evaluate_size(size_token):
    if isinstance(size_token, Token):
        if size_token.type == 'backtick_integer':
            unexpanded_token = size_token.value
            if unexpanded_token.type == 'CONTROL_SEQUENCE':
                # If we have a single character control sequence in this context,
                # it is just a way of specifying a character in a way that
                # won't invoke its special effects.
                char = unexpanded_token.value
            elif unexpanded_token.type == 'character':
                char = unexpanded_token.value['char']
            else:
                import pdb; pdb.set_trace()
            return ord(char)
        elif size_token.type == 'control_sequence':
            # size_token = lexer.state.control_sequences[name]
            raise NotImplementedError
        elif size_token.type == 'count':
            return registers.count[size_token.value]
        else:
            import pdb; pdb.set_trace()
    else:
        return size_token


def evaluate_number(number_token):
    size_token = number_token['size']
    number = evaluate_size(size_token)
    sign = number_token['sign']
    if sign == '-':
        number *= -1
    return number


precedence = (
    ('left', 'SPACE'),
    ('left', 'UNEXPANDED_CONTROL_SEQUENCE'),
)


def p_condition_if_num(p):
    '''
    condition : IF_NUM number relation number
    '''
    nr_1 = evaluate_number(p[2])
    nr_2 = evaluate_number(p[4])
    relation = p[3].value['char']
    operator_map = {
        '<': operator.lt,
        '=': operator.eq,
        '>': operator.gt,
    }
    op = operator_map[relation]
    outcome = op(nr_1, nr_2)
    p[0] = outcome


def p_relation(p):
    '''
    relation : LESS_THAN
             | EQUALS
             | GREATER_THAN
    '''
    p[0] = p[1]


def p_character(p):
    '''
    character : MISC_CHAR_CAT_PAIR
              | EQUALS
              | GREATER_THAN
              | LESS_THAN
              | PLUS_SIGN
              | MINUS_SIGN
              | ZERO
              | ONE
              | TWO
              | THREE
              | FOUR
              | FIVE
              | SIX
              | SEVEN
              | EIGHT
              | NINE
              | A
              | B
              | C
              | D
              | E
              | F
              | SINGLE_QUOTE
              | DOUBLE_QUOTE
              | BACKTICK
    '''
    p[0] = Token(type_='character', value=p[1].value)


def p_control_sequence(p):
    '''
    control_sequence : UNEXPANDED_CONTROL_SEQUENCE
                     | UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE
    '''
    p[0] = Token(type_=p[1].type, value={'name': p[1].value})


def p_control_sequence_active(p):
    '''
    control_sequence : ACTIVE_CHARACTER
    '''
    # We will prefix active characters with @.
    # This really needs changing, but will do for now.
    p[0] = p[1]
    p[0].value['name'] = p[0].value['char']


def p_integer_variable_count(p):
    '''
    integer_variable : count_register
    '''
    p[0] = p[1]


def p_count_register(p):
    '''
    count_register : COUNT number
    '''
    p[0] = Token(type_='count', value=p[2]['size'])


def p_integer_variable_count_def(p):
    '''
    integer_variable : COUNT_DEF_TOKEN
    '''
    p[0] = Token(type_='count', value=p[1])


def split_at(s, inds):
    inds = [0] + list(inds) + [len(s)]
    return [s[inds[i]:inds[i + 1]] for i in range(0, len(inds) - 1)]


def split_hex_code(n, hex_length, inds):
    # Get the zero-padded string representation of the number in base 16.
    n_hex = format(n, '0{}x'.format(hex_length))
    # Check the number is of the correct magnitude.
    assert len(n_hex) == hex_length
    # Split the hex string into pieces, at the given indices.
    parts_hex = split_at(n_hex, inds)
    # Convert each part from hex to decimal.
    parts = [int(part, base=16) for part in parts_hex]
    return parts


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


def p_normal_integer_internal_integer(p):
    '''
    normal_integer : internal_integer
    '''
    p[0] = p[1]


def p_internal_integer_short_hand_token(p):
    '''
    internal_integer : CHAR_DEF_TOKEN
                     | MATH_CHAR_DEF_TOKEN
                     | COUNT_DEF_TOKEN
    '''
    p[0] = p[1]


def p_internal_integer_count_register(p):
    '''
    internal_integer : count_register
    '''
    # TODO: add other kinds of internal integer.
    p[0] = p[1]


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
    p[0] = Token(type_='backtick_integer', value=p[2])


def p_character_token_control_sequence(p):
    '''
    character_token : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE
    '''
    # TODO: make this possible.
    '''
                    | active character
    '''
    p[0] = p[1]


def p_character_token_character(p):
    '''
    character_token : character
    '''
    p[0] = p[1]


def process_digits(p, base):
    new_digit = p[1].value['char']
    if len(p) > 2:
        constant = p[2]
        # We work right-to-left, so the new digit should be added on the left.
        constant['digits'] = new_digit + constant['digits']
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
                       | empty
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
    p[0] = p[1].value['char']


def p_equals(p):
    '''
    equals : optional_spaces
           | optional_spaces EQUALS
    '''
    pass


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
    raise ValueError
    print("Syntax error in input!")


# Build the parser
condition_parser = yacc.yacc(debug=True)


class PreLexedLexer(object):

    def __init__(self):
        pass

    def input(self, tokens):
        self.tokens = iter(tokens)

    def token(self):
        try:
            return next(self.tokens)
        except StopIteration:
            return None

dummy_lexer = PreLexedLexer()
