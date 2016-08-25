import logging
import yacc

from utils import post_mortem
from common import Token, TerminalToken
from lexer import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander, parse_replacement_text
from registers import registers

from expander import terminal_primitive_control_sequences_map, short_hand_def_map
from typer import literal_types
from banisher import special_terminal_control_sequence_types


short_hand_def_to_token_map = {
    k: '{}_TOKEN'.format(k)
    for k in short_hand_def_map.values()
}


tokens = ()
tokens += tuple(terminal_primitive_control_sequences_map.values())
tokens += tuple(short_hand_def_to_token_map.values())
tokens += tuple(literal_types)
tokens += tuple(special_terminal_control_sequence_types)
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


def p_commands_extend(p):
    '''
    commands : commands command
    '''
    p[0] = p[1]
    p[0].append(p[2])


def p_commands(p):
    '''
    commands : command
    '''
    p[0] = [p[1]]


def p_command(p):
    '''
    command : assignment
            | character
            | PAR
            | SPACE
            | message
            | write
            | RELAX
    '''
    p[0] = p[1]


def p_assignment(p):
    '''
    assignment : macro_assignment
               | non_macro_assignment
    '''
    p[0] = p[1]


def p_immediate_write(p):
    '''
    write : IMMEDIATE write
    '''
    p[0] = p[2]
    p[0].value['prefix'] = 'immediate'


def p_write(p):
    '''
    write : WRITE number general_text
    '''
    p[0] = Token(type_='write',
                 value={'stream_number': p[2], 'content': p[3]})


def p_message(p):
    '''
    message : MESSAGE general_text
            | ERROR_MESSAGE general_text
    '''
    p[0] = Token(type_='message',
                 value={'content': p[2]})


def p_general_text(p):
    '''
    general_text : filler implicit_left_brace BALANCED_TEXT RIGHT_BRACE
    '''
    p[0] = p[3]


def p_filler(p):
    '''
    filler : optional_spaces
           | filler RELAX optional_spaces
    '''
    pass


def p_implicit_left_brace(p):
    '''
    implicit_left_brace : LEFT_BRACE
    '''
    p[0] = p[1]


def p_macro_assignment_prefix(p):
    '''
    macro_assignment : prefix macro_assignment
    '''
    p[0] = p[2]
    # TODO: actually do something about this in expander.
    p[0].value['prefixes'].add(p[1])


def p_prefix(p):
    '''
    prefix : GLOBAL
           | LONG
           | OUTER
    '''
    p[0] = p[1].type


def p_macro_assignment(p):
    '''
    macro_assignment : definition
    '''
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': p[1]})
    name = p[1].value['name']
    lex_wrapper.e.control_sequences[name] = macro_token
    p[0] = macro_token


def p_definition(p):
    '''
    definition : DEF control_sequence definition_text
    '''
    def_token = Token(type_='definition',
                      value={'name': p[2].value['name'],
                             'text': p[3]})
    p[0] = def_token


def p_definition_text(p):
    '''
    definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT RIGHT_BRACE
    '''
    # TODO: maybe move this parsing logic to inside the Expander.
    replacement_text = parse_replacement_text(p[3])
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': p[1],
                                  'replacement_text': replacement_text})
    p[0] = def_text_token


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


def p_non_macro_assignment_global(p):
    '''
    non_macro_assignment : GLOBAL non_macro_assignment
    '''
    p[0] = p[2]
    p[0].value['global'] = True


def p_non_macro_assignment(p):
    '''
    non_macro_assignment : simple_assignment
    '''
    p[0] = p[1]


def p_simple_assignment(p):
    '''
    simple_assignment : variable_assignment
                      | arithmetic
                      | code_assignment
                      | let_assignment
                      | short_hand_definition
    '''
    p[0] = p[1]


def p_variable_assignment(p):
    '''
    variable_assignment : integer_variable equals number
    '''
    # import pdb; pdb.set_trace()
    value = evaluate_number(p[3])
    if p[1].type == 'count':
        registers.count[p[1].value] = value
    p[0] = Token(type_='variable_assignment',
                 value={'variable': p[1], 'value': p[3]})


def p_arithmetic_integer_variable(p):
    '''
    arithmetic : ADVANCE integer_variable optional_by number
    '''
    # import pdb; pdb.set_trace()
    value = evaluate_number(p[4])
    if p[2].type == 'count':
        registers.count[p[2].value] += value
    p[0] = Token(type_='advance', value={'target': p[2], 'value': p[4]})


def p_optional_by(p):
    '''
    optional_by : by
                | optional_spaces
    '''
    pass


def p_by(p):
    '''
    by : non_active_uncased_b non_active_uncased_y
    '''
    pass


def p_non_active_uncased_b(p):
    '''
    non_active_uncased_b : B
                         | NON_ACTIVE_b
                         | NON_ACTIVE_B
    '''
    pass


def p_non_active_uncased_y(p):
    '''
    non_active_uncased_y : NON_ACTIVE_y
                         | NON_ACTIVE_Y
    '''
    pass


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


def p_short_hand_definition(p):
    '''
    short_hand_definition : short_hand_def control_sequence equals number
    '''
    # TODO: does this remove signs from assignment? Isn't that bad?
    code = evaluate_number(p[4])
    def_type = p[1].type
    def_token_type = short_hand_def_to_token_map[def_type]
    primitive_token = TerminalToken(type_=def_token_type, value=code)
    control_sequence_name = p[2].value['name']
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': [],
                                  'replacement_text': [primitive_token]})
    def_token = Token(type_='definition',
                      value={'name': control_sequence_name,
                             'text': def_text_token})
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': def_token})
    lex_wrapper.e.control_sequences[control_sequence_name] = macro_token
    # Just for the sake of output.
    p[0] = macro_token


def p_let_assignment_control_sequence(p):
    '''
    let_assignment : LET control_sequence equals one_optional_space control_sequence
    '''
    # TODO allow char_cat_pair.
    target_name = p[5].value['name']
    target_contents = lex_wrapper.e.control_sequences[target_name]
    new_name = p[2].value['name']
    lex_wrapper.e.control_sequences[new_name] = target_contents
    p[0] = Token(type_='let_assignment',
                 value={'name': new_name,
                        'target_name': target_name,
                        'target_contents': target_contents})


def p_short_hand_def(p):
    '''
    short_hand_def : CHAR_DEF
                   | MATH_CHAR_DEF
                   | COUNT_DEF
                   | DIMEN_DEF
                   | SKIP_DEF
                   | MU_SKIP_DEF
                   | TOKS_DEF
    '''
    p[0] = p[1]


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


def p_code_assignment(p):
    '''
    code_assignment : code_name number equals number
    '''
    code_type, char_number, code_number = p[1], p[2], p[4]
    char_size, code_size = evaluate_number(char_number), evaluate_number(code_number)
    char = chr(char_size)
    code_type_to_char_map = {
        'CAT_CODE': lex_wrapper.lex.char_to_cat,
        'MATH_CODE': lex_wrapper.lex.char_to_math_code,
        'UPPER_CASE_CODE': lex_wrapper.lex.upper_case_code,
        'LOWER_CASE_CODE': lex_wrapper.lex.lower_case_code,
        'SPACE_FACTOR_CODE': lex_wrapper.lex.space_factor_code,
        'DELIMITER_CODE': lex_wrapper.lex.delimiter_code,
    }
    if code_type == 'CAT_CODE':
        code = CatCode(code_size)
    elif code_type == 'MATH_CODE':
        parts = split_hex_code(code_size, hex_length=4, inds=(1, 2))
        math_class_i, family, position = parts
        math_class = MathClass(math_class_i)
        glyph_code = GlyphCode(family, position)
        code = MathCode(math_class, glyph_code)
    elif code_type in ('UPPER_CASE_CODE', 'LOWER_CASE_CODE'):
        code = chr(code_size)
    elif code_type == 'SPACE_FACTOR_CODE':
        code = code_size
    elif code_type == 'DELIMITER_CODE':
        parts = split_hex_code(code_size, hex_length=6, inds=(1, 3, 4))
        small_family, small_position, large_family, large_position = parts
        small_glyph_code = GlyphCode(small_family, small_position)
        large_glyph_code = GlyphCode(large_family, large_position)
        code = DelimiterCode(small_glyph_code, large_glyph_code)
    char_map = code_type_to_char_map[code_type]
    char_map[char] = code
    p[0] = {'type': 'code_assignment', 'code_type': code_type,
            'char': char, 'code': code}


def p_code_name_cat(p):
    '''
    code_name : CAT_CODE
              | MATH_CODE
              | UPPER_CASE_CODE
              | LOWER_CASE_CODE
              | SPACE_FACTOR_CODE
              | DELIMITER_CODE
    '''
    p[0] = p[1].type


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
    # TODO: make this possible.
    '''
                    | active character
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
    print("Syntax error in input!")
    post_mortem(lex_wrapper)

# Build the parser
parser = yacc.yacc(debug=True)


class LexWrapper(object):

    def __init__(self):
        pass

    def input(self, file_name):
        self.r = Reader(file_name)
        self.lex = Lexer(self.r)
        self.e = Expander()
        self.b = Banisher(self.lex, self.e)

    def token(self):
        try:
            return self.b.next_token
        except EndOfFile:
            return None

lex_wrapper = LexWrapper()
