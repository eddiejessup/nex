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

    'CHAR_DEF_TOKEN',
)


primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'mathcode': 'MATH_CODE',
    'uccode': 'UPPER_CASE_CODE',
    'lccode': 'LOWER_CASE_CODE',
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
