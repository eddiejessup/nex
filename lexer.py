from enum import Enum
import logging
from collections import deque

from ply.lex import Lexer, LexToken

from process import State, CatCode


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

    # Internal tokens.
    'CHAR_DEF_TOKEN',
    'MATH_CHAR_DEF_TOKEN',
    'COUNT_DEF_TOKEN',
)


primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'mathcode': 'MATH_CODE',
    'uccode': 'UPPER_CASE_CODE',
    'lccode': 'LOWER_CASE_CODE',
    'sfcode': 'SPACE_FACTOR_CODE',
    'delcode': 'DELIMITER_CODE',

    'chardef': 'CHAR_DEF',
    'mathchardef': 'MATH_CHAR_DEF',
    'countdef': 'COUNT_DEF',

    'par': 'PAR',
    'count': 'COUNT',
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


tokens += tuple(set(literals_map.values()))
tokens += tuple(set(primitive_control_sequences_map.values()))

suppress_expansion_tokens = (
    'chardef',
    'mathchardef',
    'countdef',
    'def',
)


class LexMode(Enum):
    expand = 1
    no_expand = 3


class PLYLexer(Lexer):

    def __init__(self):
        self.lex_mode = LexMode.expand

    def input(self, chars):
        self.state = State(chars)
        self.state_tokens = self.state.get_tokens()
        self.tokens_stack = deque()

    def expand_control_sequence(self, name):
        return self.state.control_sequences[name]

    def fetch_state_token_tokens(self):
        state_token = next(self.state_tokens)
        return self.state_token_tokens(state_token)

    def state_token_tokens(self, state_token):
        tokens = []
        if state_token['type'] == 'control_sequence':
            name = state_token['name']
            if self.lex_mode == LexMode.no_expand:
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
            elif name in ('global', 'long', 'outer'):
                tokens.append(PLYToken(type_='PREFIX', value=state_token))
            else:
                import pdb; pdb.set_trace()
        elif state_token['type'] == 'char_cat_pair':
            char, cat = state_token['char'], state_token['cat']
            if cat in (CatCode.letter, CatCode.other):
                if (char, cat) in literals_map:
                    type_ = literals_map[(char, cat)]
                    # TODO: this will probably break when using backticks for
                    # open-quotes.
                    # Maybe move this to parse rule, at seen_BACKTICK?
                    if type_ == 'BACKTICK':
                        self.lex_mode = LexMode.no_expand
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
                tokens = self.fetch_state_token_tokens()
            except StopIteration:
                return
            self.tokens_stack.extend(tokens)
        token = self.tokens_stack.popleft()

        def token_suppresses_expansion(token):
            return (token.type in primitive_control_sequences_map.values() and
                    token.value['name'] in suppress_expansion_tokens)
        if token_suppresses_expansion(token):
            self.lex_mode = LexMode.no_expand
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
