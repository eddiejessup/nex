import logging

from rply import ParserGenerator

from utils import post_mortem
from common import Token, TerminalToken
from lexer import CatCode, MathCode, GlyphCode, DelimiterCode, MathClass
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander, parse_replacement_text
from registers import registers

from expander import terminal_primitive_control_sequences_map, short_hand_def_map
from typer import literal_types, PhysicalUnit, units_in_scaled_points
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


prec = (
    ('left', 'SPACE'),
    # ('left', 'UNEXPANDED_CONTROL_SEQUENCE'),
)


pg = ParserGenerator(tokens,
                     precedence=prec,
                     cache_id="main_parser")


class DigitCollection(object):

    def __init__(self, base):
        self.base = base
        self.digits = []


def evaluate_size(size_token):
    if isinstance(size_token, Token):
        if size_token.type == 'backtick_integer':
            unexpanded_token = size_token.value
            if unexpanded_token.type == 'UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE':
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
        elif size_token.type == 'dimen':
            return registers.dimen[size_token.value]
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


def evaluate_dimen(dimen_token):
    size_token, sign = dimen_token['size'], dimen_token['sign']
    number_of_units_token = size_token.value['factor']
    unit_token = size_token.value['unit']
    number_of_units = evaluate_size(number_of_units_token)
    unit, is_true_unit = unit_token['unit'], unit_token['true']
    number_of_scaled_points = units_in_scaled_points[unit] * number_of_units
    # TODO: deal with 'true' and 'not-true' scales properly
    mag_parameter = 1000.0
    if is_true_unit:
        number_of_scaled_points *= 1000.0 / mag_parameter
    if sign == '-':
        number_of_scaled_points *= -1
    return number_of_scaled_points


@pg.production('commands : commands command')
def commands_extend(parser_state, p):
    v = p[0]
    v.append(p[1])
    return v


@pg.production('commands : command')
def commands(parser_state, p):
    return [p[0]]


@pg.production('command : assignment')
@pg.production('command : character')
@pg.production('command : PAR')
@pg.production('command : SPACE')
@pg.production('command : message')
@pg.production('command : write')
@pg.production('command : RELAX')
def command(parser_state, p):
    return p[0]


@pg.production('assignment : macro_assignment')
@pg.production('assignment : non_macro_assignment')
def assignment(parser_state, p):
    return p[0]


@pg.production('write : IMMEDIATE write')
def immediate_write(parser_state, p):
    return p[1]
    p[0].value['prefix'] = 'immediate'


@pg.production('write : WRITE number general_text')
def write(parser_state, p):
    return Token(type_='write',
                 value={'stream_number': p[1], 'content': p[2]})


@pg.production('message : ERROR_MESSAGE general_text')
@pg.production('message : MESSAGE general_text')
def message(parser_state, p):
    return Token(type_='message',
                 value={'content': p[1]})


@pg.production('general_text : filler implicit_left_brace BALANCED_TEXT RIGHT_BRACE')
def general_text(parser_state, p):
    return p[2]


@pg.production('filler : optional_spaces')
@pg.production('filler : filler RELAX optional_spaces')
def filler(parser_state, p):
    return None


@pg.production('implicit_left_brace : LEFT_BRACE')
def implicit_left_brace(parser_state, p):
    return p[0]


@pg.production('macro_assignment : prefix macro_assignment')
def macro_assignment_prefix(parser_state, p):
    v = p[1]
    # TODO: actually do something about this in expander.
    v.value['prefixes'].add(p[0])
    return v


@pg.production('prefix : GLOBAL')
@pg.production('prefix : LONG')
@pg.production('prefix : OUTER')
def prefix(parser_state, p):
    return p[0].type


@pg.production('macro_assignment : definition')
def macro_assignment(parser_state, p):
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': p[0]})
    name = p[0].value['name']
    parser_state.e.control_sequences[name] = macro_token
    return macro_token


@pg.production('definition : DEF control_sequence definition_text')
def definition(parser_state, p):
    def_token = Token(type_='definition',
                      value={'name': p[1].value['name'],
                             'text': p[2]})
    return def_token


@pg.production('definition_text : PARAMETER_TEXT LEFT_BRACE BALANCED_TEXT RIGHT_BRACE')
def definition_text(parser_state, p):
    # TODO: maybe move this parsing logic to inside the Expander.
    replacement_text = parse_replacement_text(p[2].value)
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': p[0].value,
                                  'replacement_text': replacement_text})
    return def_text_token


@pg.production('character : MISC_CHAR_CAT_PAIR')
@pg.production('character : EQUALS')
@pg.production('character : GREATER_THAN')
@pg.production('character : LESS_THAN')
@pg.production('character : PLUS_SIGN')
@pg.production('character : MINUS_SIGN')
@pg.production('character : ZERO')
@pg.production('character : ONE')
@pg.production('character : TWO')
@pg.production('character : THREE')
@pg.production('character : FOUR')
@pg.production('character : FIVE')
@pg.production('character : SIX')
@pg.production('character : SEVEN')
@pg.production('character : EIGHT')
@pg.production('character : NINE')
@pg.production('character : A')
@pg.production('character : B')
@pg.production('character : C')
@pg.production('character : D')
@pg.production('character : E')
@pg.production('character : F')
@pg.production('character : SINGLE_QUOTE')
@pg.production('character : DOUBLE_QUOTE')
@pg.production('character : BACKTICK')
def character(parser_state, p):
    return Token(type_='character', value=p[0].value)


@pg.production('control_sequence : UNEXPANDED_CONTROL_SEQUENCE')
@pg.production('control_sequence : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE')
def control_sequence(parser_state, p):
    return Token(type_=p[0].type, value={'name': p[0].value})


@pg.production('control_sequence : ACTIVE_CHARACTER')
def control_sequence_active(parser_state, p):
    # We will prefix active characters with @.
    # This really needs changing, but will do for now.
    v = p[0]
    v.value['name'] = v.value['char']
    return v


@pg.production('non_macro_assignment : GLOBAL non_macro_assignment')
def non_macro_assignment_global(parser_state, p):
    v = p[1]
    v.value['global'] = True
    return v


@pg.production('non_macro_assignment : simple_assignment')
def non_macro_assignment(parser_state, p):
    return p[0]


@pg.production('simple_assignment : variable_assignment')
@pg.production('simple_assignment : arithmetic')
@pg.production('simple_assignment : code_assignment')
@pg.production('simple_assignment : let_assignment')
@pg.production('simple_assignment : short_hand_definition')
def simple_assignment(parser_state, p):
    return p[0]


@pg.production('variable_assignment : integer_variable equals number')
def variable_assignment_integer(parser_state, p):
    value = evaluate_number(p[2])
    if p[0].type == 'count':
        registers.count[p[0].value] = value
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('variable_assignment : dimen_variable equals dimen')
def variable_assignment_dimen(parser_state, p):
    value = evaluate_dimen(p[2])
    if p[0].type == 'dimen':
        registers.dimen[p[0].value] = value
    return Token(type_='variable_assignment',
                 value={'variable': p[0], 'value': p[2]})


@pg.production('arithmetic : ADVANCE integer_variable optional_by number')
def arithmetic_integer_variable(parser_state, p):
    value = evaluate_number(p[3])
    if p[1].type == 'count':
        registers.count[p[1].value] += value
    return Token(type_='advance', value={'target': p[1], 'value': p[3]})


@pg.production('optional_by : by')
@pg.production('optional_by : optional_spaces')
def optional_by(parser_state, p):
    return None


@pg.production('by : non_active_uncased_b non_active_uncased_y')
def by(parser_state, p):
    return None


@pg.production('non_active_uncased_b : B')
@pg.production('non_active_uncased_b : NON_ACTIVE_b')
@pg.production('non_active_uncased_b : NON_ACTIVE_B')
def non_active_uncased_b(parser_state, p):
    return None


@pg.production('non_active_uncased_y : NON_ACTIVE_y')
@pg.production('non_active_uncased_y : NON_ACTIVE_Y')
def non_active_uncased_y(parser_state, p):
    return None


@pg.production('non_active_uncased_t : NON_ACTIVE_t')
@pg.production('non_active_uncased_t : NON_ACTIVE_T')
def non_active_uncased_t(parser_state, p):
    return None


@pg.production('non_active_uncased_r : NON_ACTIVE_r')
@pg.production('non_active_uncased_r : NON_ACTIVE_R')
def non_active_uncased_r(parser_state, p):
    return None


@pg.production('non_active_uncased_u : NON_ACTIVE_u')
@pg.production('non_active_uncased_u : NON_ACTIVE_U')
def non_active_uncased_u(parser_state, p):
    return None


@pg.production('non_active_uncased_e : NON_ACTIVE_e')
@pg.production('non_active_uncased_e : NON_ACTIVE_E')
@pg.production('non_active_uncased_e : E')
def non_active_uncased_e(parser_state, p):
    return None


@pg.production('non_active_uncased_p : NON_ACTIVE_p')
@pg.production('non_active_uncased_e : NON_ACTIVE_P')
def non_active_uncased_p(parser_state, p):
    return None


@pg.production('integer_variable : count_register')
def integer_variable_count(parser_state, p):
    return p[0]


@pg.production('count_register : COUNT number')
def count_register(parser_state, p):
    return Token(type_='count', value=p[1]['size'])


@pg.production('integer_variable : COUNT_DEF_TOKEN')
def integer_variable_count_def(parser_state, p):
    return Token(type_='count', value=p[0])


@pg.production('dimen_variable : DIMEN_DEF_TOKEN')
def dimen_variable_dimen_def(parser_state, p):
    return Token(type_='dimen', value=p[0])


@pg.production('short_hand_definition : short_hand_def control_sequence equals number')
def short_hand_definition(parser_state, p):
    code = evaluate_number(p[3])
    def_type = p[0].type
    def_token_type = short_hand_def_to_token_map[def_type]
    primitive_token = TerminalToken(type_=def_token_type, value=code)
    control_sequence_name = p[1].value['name']
    def_text_token = Token(type_='definition_text',
                           value={'parameter_text': [],
                                  'replacement_text': [primitive_token]})
    def_token = Token(type_='definition',
                      value={'name': control_sequence_name,
                             'text': def_text_token})
    macro_token = Token(type_='macro',
                        value={'prefixes': set(),
                               'definition': def_token})
    parser_state.e.control_sequences[control_sequence_name] = macro_token
    # Just for the sake of output.
    return macro_token


@pg.production('let_assignment : LET control_sequence equals one_optional_space control_sequence')
def let_assignment_control_sequence(parser_state, p):
    # TODO allow char_cat_pair.
    target_name = p[4].value['name']
    target_contents = parser_state.e.control_sequences[target_name]
    new_name = p[1].value['name']
    parser_state.e.control_sequences[new_name] = target_contents
    return Token(type_='let_assignment',
                 value={'name': new_name,
                        'target_name': target_name,
                        'target_contents': target_contents})


@pg.production('short_hand_def : CHAR_DEF')
@pg.production('short_hand_def : MATH_CHAR_DEF')
@pg.production('short_hand_def : COUNT_DEF')
@pg.production('short_hand_def : DIMEN_DEF')
@pg.production('short_hand_def : SKIP_DEF')
@pg.production('short_hand_def : MU_SKIP_DEF')
@pg.production('short_hand_def : TOKS_DEF')
def short_hand_def(parser_state, p):
    return p[0]


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


@pg.production('code_assignment : code_name number equals number')
def code_assignment(parser_state, p):
    code_type, char_number, code_number = p[0], p[1], p[3]
    char_size, code_size = evaluate_number(char_number), evaluate_number(code_number)
    char = chr(char_size)
    code_type_to_char_map = {
        'CAT_CODE': parser_state.lex.char_to_cat,
        'MATH_CODE': parser_state.lex.char_to_math_code,
        'UPPER_CASE_CODE': parser_state.lex.upper_case_code,
        'LOWER_CASE_CODE': parser_state.lex.lower_case_code,
        'SPACE_FACTOR_CODE': parser_state.lex.space_factor_code,
        'DELIMITER_CODE': parser_state.lex.delimiter_code,
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
    return {'type': 'code_assignment', 'code_type': code_type,
            'char': char, 'code': code}


@pg.production('code_name : CAT_CODE')
@pg.production('code_name : MATH_CODE')
@pg.production('code_name : UPPER_CASE_CODE')
@pg.production('code_name : LOWER_CASE_CODE')
@pg.production('code_name : SPACE_FACTOR_CODE')
@pg.production('code_name : DELIMITER_CODE')
def code_name_cat(parser_state, p):
    return p[0].type


@pg.production('number : optional_signs unsigned_number')
def number(parser_state, p):
    return {'sign': p[0], 'size': p[1]}


@pg.production('dimen : optional_signs unsigned_dimen')
def dimen(parser_state, p):
    return {'sign': p[0], 'size': p[1]}


@pg.production('unsigned_number : normal_integer')
# @pg.production('unsigned_number : coerced_integer')
def unsigned_number(parser_state, p):
    return p[0]


@pg.production('unsigned_dimen : normal_dimen')
# @pg.production('unsigned_dimen : coerced_dimen')
def unsigned_dimen(parser_state, p):
    return p[0]


def get_integer_constant(collection):
    try:
        chars = [t.value['char'] for t in collection.digits]
    except TypeError:
        import pdb; pdb.set_trace()

    s = ''.join(chars)
    return int(s, base=collection.base)


def get_real_decimal_constant(collection):
    # Our function assumes the digits are in base 10.
    assert collection.base == 10
    chars = [t.value['char'] for t in collection.digits]
    s = ''.join(chars)
    return float(s)


@pg.production('normal_integer : internal_integer')
def normal_integer_internal_integer(parser_state, p):
    return p[0]


@pg.production('normal_dimen : internal_dimen')
def normal_dimen_internal_dimen(parser_state, p):
    return p[0]


@pg.production('internal_integer : CHAR_DEF_TOKEN')
@pg.production('internal_integer : MATH_CHAR_DEF_TOKEN')
@pg.production('internal_integer : COUNT_DEF_TOKEN')
def internal_integer_short_hand_token(parser_state, p):
    return p[0].value


@pg.production('internal_dimen : DIMEN_DEF_TOKEN')
def internal_dimen_short_hand_token(parser_state, p):
    return p[0].value


@pg.production('internal_integer : count_register')
def internal_integer_count_register(parser_state, p):
    # TODO: add other kinds of internal integer.
    return p[0]


@pg.production('normal_integer : integer_constant one_optional_space')
def normal_integer_integer(parser_state, p):
    return get_integer_constant(p[0])


@pg.production('normal_dimen : factor unit_of_measure')
def normal_dimen_explicit(parser_state, p):
    return Token(type_='normal_dimen',
                 value={'factor': p[0], 'unit': p[1]})


@pg.production('factor : normal_integer')
def factor_integer(parser_state, p):
    return p[0]


@pg.production('factor : decimal_constant')
def factor_decimal_constant(parser_state, p):
    return get_real_decimal_constant(p[0])


@pg.production('decimal_constant : COMMA')
def decimal_constant_comma(parser_state, p):
    return DigitCollection(base=10)


@pg.production('decimal_constant : POINT')
def decimal_constant_point(parser_state, p):
    v = DigitCollection(base=10)
    v.digits = [p[0]]
    return v


@pg.production('decimal_constant : digit decimal_constant')
def decimal_constant_prepend(parser_state, p):
    v = p[1]
    v.digits = [p[0]] + p[0].digits
    return v


@pg.production('decimal_constant : decimal_constant digit')
def decimal_constant_append(parser_state, p):
    v = p[0]
    v.digits = p[0].digits + [p[1]]
    return v


@pg.production('unit_of_measure : optional_true physical_unit one_optional_space')
def unit_of_measure(parser_state, p):
    return {'unit': p[1], 'true': bool(p[0])}


@pg.production('optional_true : true')
@pg.production('optional_true : empty')
def optional_true(parser_state, p):
    return p[0]


@pg.production('true : non_active_uncased_t non_active_uncased_r non_active_uncased_u non_active_uncased_e')
def true(parser_state, p):
    return True


@pg.production('physical_unit : non_active_uncased_p non_active_uncased_t')
def physical_unit(parser_state, p):
    return PhysicalUnit.point


@pg.production('normal_integer : SINGLE_QUOTE octal_constant one_optional_space')
@pg.production('normal_integer : DOUBLE_QUOTE hexadecimal_constant one_optional_space')
def normal_integer_weird_base(parser_state, p):
    return get_integer_constant(p[1])


@pg.production('normal_integer : BACKTICK character_token one_optional_space')
def normal_integer_character(parser_state, p):
    return Token(type_='backtick_integer', value=p[1])


@pg.production('character_token : UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE')
@pg.production('character_token : character')
# TODO: make this possible.
# @pg.production('character_token : ACTIVE_CHARACTER')
def character_token_character(parser_state, p):
    return p[0]


def process_integer_digits(p, base):
    if len(p) > 1:
        collection = p[1]
    else:
        collection = DigitCollection(base=base)
    # We work right-to-left, so the new digit should be added on the left.
    collection.digits = [p[0]] + collection.digits
    return collection


@pg.production('hexadecimal_constant : hexadecimal_digit')
@pg.production('hexadecimal_constant : hexadecimal_digit hexadecimal_constant')
def hexadecimal_constant(parser_state, p):
    return process_integer_digits(p, base=16)


@pg.production('integer_constant : digit')
@pg.production('integer_constant : digit integer_constant')
def integer_constant(parser_state, p):
    return process_integer_digits(p, base=10)


@pg.production('octal_constant : octal_digit')
@pg.production('octal_constant : octal_digit octal_constant')
def octal_constant(parser_state, p):
    return process_integer_digits(p, base=8)


@pg.production('hexadecimal_digit : digit')
@pg.production('hexadecimal_digit : A')
@pg.production('hexadecimal_digit : B')
@pg.production('hexadecimal_digit : C')
@pg.production('hexadecimal_digit : D')
@pg.production('hexadecimal_digit : E')
@pg.production('hexadecimal_digit : F')
def hexadecimal_digit(parser_state, p):
    return p[0]


@pg.production('digit : octal_digit')
@pg.production('digit : EIGHT')
@pg.production('digit : NINE')
def digit(parser_state, p):
    return p[0]


@pg.production('octal_digit : ZERO')
@pg.production('octal_digit : ONE')
@pg.production('octal_digit : TWO')
@pg.production('octal_digit : THREE')
@pg.production('octal_digit : FOUR')
@pg.production('octal_digit : FIVE')
@pg.production('octal_digit : SIX')
@pg.production('octal_digit : SEVEN')
def octal_digit(parser_state, p):
    return p[0]


@pg.production('one_optional_space : SPACE')
@pg.production('one_optional_space : empty')
def one_optional_space(parser_state, p):
    return None


@pg.production('optional_signs : optional_spaces')
@pg.production('optional_signs : optional_signs plus_or_minus optional_spaces')
def optional_signs(parser_state, p):
    flip_sign = lambda s: '+' if s == '-' else '-'
    if len(p) > 1:
        v = p[1]
        if v == '-':
            return flip_sign(v)
    else:
        return '+'


@pg.production('plus_or_minus : PLUS_SIGN')
@pg.production('plus_or_minus : MINUS_SIGN')
def plus_or_minus(parser_state, p):
    return p[0].value['char']


# @pg.production('equals : optional_spaces')
# @pg.production('equals : optional_spaces')
# @pg.production('equals : optional_spaces EQUALS')
@pg.production('equals : EQUALS')
def eq(parser_state, p):
    return None


@pg.production('optional_spaces : SPACE optional_spaces')
@pg.production('optional_spaces : empty')
def optional_spaces(parser_state, p):
    return None


@pg.production('empty :')
def empty(parser_state, p):
    return None


@pg.error
def error(parser_state, p):
    print("Syntax error in input!")
    post_mortem(parser_state, parser)
    raise ValueError

# Build the parser
parser = pg.build()


class LexWrapper(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self.r = Reader(file_name)
        self.lex = Lexer(self.r)
        self.e = Expander()
        self.b = Banisher(self.lex, self.e)

    def __next__(self):
        try:
            return self.b.next_token
        except EndOfFile:
            return None
