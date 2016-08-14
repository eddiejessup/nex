from collections import deque
import logging

import ply.yacc as yacc
from ply.lex import Lexer, LexToken

from process import State, chars, CatCode


logger = logging.getLogger(__name__)

tokens = (
    'CONTROL_SEQUENCE',
    'SINGLE_CHAR_CONTROL_SEQUENCE',

    'PREFIX',

    'SPACE',
    'LEFT_BRACE',
    'RIGHT_BRACE',
    'ACTIVE_CHARACTER',

    'CHARACTER',

    'CHAR_DEF_TOKEN',
)


primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'chardef': 'CHAR_DEF',
    'par': 'PAR',
    'def': 'DEF',
    'message': 'MESSAGE',
    'relax': 'RELAX',
}


category_map = {
    CatCode.space: 'SPACE',
    CatCode.begin_group: 'LEFT_BRACE',
    CatCode.end_group: 'RIGHT_BRACE',
    CatCode.active: 'ACTIVE_CHARACTER',
}


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
    'D': 'D',
    'E': 'E',
    'F': 'F',

    '\'': 'SINGLE_QUOTE',
    '"': 'DOUBLE_QUOTE',
    '`': 'BACKTICK',
}


tokens += tuple(literals_map.values())
tokens += tuple(primitive_control_sequences_map.values())

suppress_expansion_tokens = (
    'chardef',
    'def',
)


class DigitCollection(object):

    def __init__(self, base):
        self.base = base
        self.digits = []


class PLYLexer(Lexer):

    def input(self, chars):
        self.state = State(chars)
        self.state_tokens = self.state.get_tokens()
        self.tokens_stack = deque()

    def expand_control_sequence(self, name):
        return self.state.control_sequences[name]

    def state_token_tokens(self):
        state_token = next(self.state_tokens)
        tokens = []
        if state_token['type'] == 'control_sequence':
            name = state_token['name']
            if not self.state.expanding_tokens:
                if len(name) == 1:
                    tokens.append(PLYToken(type_='SINGLE_CHAR_CONTROL_SEQUENCE',
                                           value=state_token))
                else:
                    tokens.append(PLYToken(type_='CONTROL_SEQUENCE',
                                           value=state_token))
            elif name in self.state.control_sequences:
                tokens.extend(self.expand_control_sequence(name))
            elif name in primitive_control_sequences_map:
                token_type = primitive_control_sequences_map[name]
                tokens.append(PLYToken(type_=token_type, value=state_token))
                if name in suppress_expansion_tokens:
                    self.state.disable_expansion()
            elif name in ('global', 'long', 'outer'):
                tokens.append(PLYToken(type_='PREFIX', value=state_token))
            else:
                import pdb; pdb.set_trace()
        elif state_token['type'] == 'char_cat_pair':
            char, cat = state_token['char'], state_token['cat']
            if cat in (CatCode.letter, CatCode.other):
                if char in literals_map and cat == CatCode.other:
                    type_ = literals_map[char]
                    # TODO: this will probably break when using backticks for
                    # open-quotes.
                    # Maybe move this to parse rule, at seen_BACKTICK?
                    if type_ == 'BACKTICK':
                        self.state.disable_expansion()
                else:
                    type_ = 'CHARACTER'
            elif cat in category_map:
                type_ = category_map[cat]
            else:
                import pdb; pdb.set_trace()
            token = PLYToken(type_, value=state_token)
            tokens.append(token)
            logger.info(token)
        else:
            import pdb; pdb.set_trace()
        return tokens

    def token(self):
        if not self.tokens_stack:
            try:
                tokens = self.state_token_tokens()
            except StopIteration:
                return
            self.tokens_stack.extend(tokens)
        token = self.tokens_stack.popleft()
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


def is_backtick(value):
    return isinstance(value, dict) and value['type'] == 'backtick'


def evaluate(value):
    if is_backtick(value):
        unexpanded_token = value['token']
        if unexpanded_token['type'] == 'control_sequence':
            expanded_tokens = evaluate(value['token'])
            # Check the target token expands to just one token.
            assert len(expanded_tokens) == 1
            expanded_token = expanded_tokens[0]
            # Check the single token is one character.
            assert len(expanded_token) == 1
        elif unexpanded_token['type'] == 'character':
            expanded_token = unexpanded_token['char']
        return ord(expanded_token)
    if is_control_sequence(value):
        name = value['name']
        value = lexer.state.control_sequences[name]
    return value


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
    command : char_def
            | macro_assignment
            | action
    '''
    p[0] = p[1]


def p_merged_space(p):
    '''
    space : SPACE
          | space SPACE
    '''
    p[0] = {'type': 'space'}


def p_message(p):
    '''
    message : MESSAGE general_text
    '''
    p[0] = {'type': 'message', 'content': p[2]}


def p_general_text(p):
    '''
    general_text : filler implicit_left_brace balanced_text RIGHT_BRACE
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
    macro_assignment : PREFIX macro_assignment
    '''
    p[0] = p[2]
    p[0]['prefix'] = p[1]['name']


def p_macro_assignment(p):
    '''
    macro_assignment : definition
    '''
    p[0] = p[1]
    lexer.state.enable_expansion()


def p_definition(p):
    '''
    definition : DEF control_sequence definition_text
    '''
    p[0] = {'type': 'definition', 'name': p[2]['name'], 'content': p[3]}


def p_definition_text(p):
    '''
    definition_text : LEFT_BRACE balanced_text RIGHT_BRACE
    '''
    p[0] = p[2]


def p_balanced_text(p):
    '''
    balanced_text : action
                  | balanced_text action
    '''
    if len(p) < 3:
        p[0] = [p[1]]
    else:
        p[0] = p[1]
        p[0].append(p[2])


def p_action(p):
    '''
    action : control_sequence
           | character
           | cat_code
           | PAR
           | space
           | message
    '''
    p[0] = p[1]


def p_character(p):
    '''
    character : CHARACTER
              | EQUALS
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
    p[0] = {'type': 'character', 'char': p[1]['char'], 'cat': p[1]['cat']}


def p_control_sequence(p):
    '''
    control_sequence : CONTROL_SEQUENCE
                     | SINGLE_CHAR_CONTROL_SEQUENCE
    '''
    p[0] = p[1]


def p_control_sequence_active(p):
    '''
    control_sequence : ACTIVE_CHARACTER
    '''
    # We will prefix active characters with @.
    # This really needs changing, but will do for now.
    p[0] = {'name': '@' + p[1]['char'], 'type': 'control_sequence'}


def p_chardef(p):
    '''
    char_def : CHAR_DEF CONTROL_SEQUENCE seen_CONTROL_SEQUENCE equals number
    '''
    char_code = evaluate(p[5]['size'])
    token = PLYToken(type_='CHAR_DEF_TOKEN', value=char_code)
    control_sequence_name = p[2]['name']
    lexer.state.control_sequences[control_sequence_name] = [token]
    p[0] = {'type': 'char_def', 'name': control_sequence_name,
            'char_code': char_code}


def p_seen_CONTROL_SEQUENCE(p):
    '''
    seen_CONTROL_SEQUENCE :
    '''
    lexer.state.enable_expansion()


def p_cat_code(p):
    '''
    cat_code : CAT_CODE number equals number
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


def p_normal_integer_internal_integer(p):
    '''
    normal_integer : internal_integer
    '''
    p[0] = p[1]


def p_internal_integer(p):
    '''
    internal_integer : CHAR_DEF_TOKEN one_optional_space
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
    p[0] = {'type': 'backtick', 'token': p[2]}
    lexer.state.enable_expansion()


def p_character_token(p):
    '''
    character_token : SINGLE_CHAR_CONTROL_SEQUENCE
                    | character
    '''
    # TODO: make this possible.
    '''
                    | active character
    '''
    p[0] = p[1]


def process_digits(p, base):
    new_digit = p[1]['char']
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
    import pdb; pdb.set_trace()
    print("Syntax error in input!")


# Build the parser
parser = yacc.yacc(debug=True)

result = parser.parse(chars, lexer=lexer)
# result = parser.parse(s)
print()
print('Parsed:')
for s in result:
    print(s)
