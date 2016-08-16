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

    'BALANCED_TEXT',

    'CHARACTER',
)


primitive_control_sequences_map = {
    'catcode': 'CAT_CODE',
    'mathcode': 'MATH_CODE',
    'uccode': 'UPPER_CASE_CODE',
    'lccode': 'LOWER_CASE_CODE',
    'sfcode': 'SPACE_FACTOR_CODE',
    'delcode': 'DELIMITER_CODE',

    'def': 'DEF',

    'count': 'COUNT',

    'par': 'PAR',
    'relax': 'RELAX',
    'immediate': 'IMMEDIATE',

    'message': 'MESSAGE',
    'write': 'WRITE',
}

short_hand_def_map = {
    'chardef': 'CHAR_DEF',
    'mathchardef': 'MATH_CHAR_DEF',
    'countdef': 'COUNT_DEF',
    'dimendef': 'DIMEN_DEF',
    'skipdef': 'SKIP_DEF',
    'muskipdef': 'MU_SKIP_DEF',
    'toksdef': 'TOKS_DEF',
}
primitive_control_sequences_map.update(short_hand_def_map)

short_hand_def_token_map = {
    '{}_token'.format(k): '{}_TOKEN'.format(v)
    for k, v in short_hand_def_map.items()
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
tokens += tuple(set(short_hand_def_token_map.values()))

read_control_sequence_name_tokens = (
    'def',
)
read_control_sequence_name_tokens += tuple(set(short_hand_def_map.keys()))


class LexMode(Enum):
    expand = 1
    read_balanced_text = 2
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

    def fetch_state_tokens_in_balanced_text(self):
        brace_counter = 1
        state_tokens = []
        while True:
            state_token = next(self.state_tokens)
            if state_token['type'] == 'char_cat_pair':
                char, cat = state_token['char'], state_token['cat']
                if cat == CatCode.begin_group:
                    brace_counter += 1
                elif cat == CatCode.end_group:
                    brace_counter -= 1
                if brace_counter == 0:
                    break
            state_tokens.append(state_token)
        return state_tokens

    def fetch_state_token_tokens(self):
        if self.lex_mode == LexMode.read_balanced_text:
            state_tokens = self.fetch_state_tokens_in_balanced_text()
            token = PLYToken(type_='BALANCED_TEXT', value=state_tokens)
            self.lex_mode = LexMode.expand
            return [token]
        else:
            state_token = next(self.state_tokens)
            return self.state_token_tokens(state_token)

    def fetch_state_token_tokens_no_expand(self):
        '''
        Fetch a single state token, in no-expand lex mode, and convert it into
        its terminal tokens.
        '''
        old_lex_mode = self.lex_mode
        self.lex_mode = LexMode.no_expand
        tokens = self.fetch_state_token_tokens()
        self.lex_mode = old_lex_mode
        return tokens

    def state_token_tokens_control_sequence(self, state_token):
        tokens = []
        name = state_token['name']
        if self.lex_mode == LexMode.no_expand:
            if len(name) == 1:
                type_ = 'SINGLE_CHAR_CONTROL_SEQUENCE'
            else:
                type_ = 'CONTROL_SEQUENCE'
            tokens.append(PLYToken(type_=type_, value=state_token))
        elif name in self.state.control_sequences:
            control_sequence_state_tokens = self.expand_control_sequence(name)
            for cs_state_token in control_sequence_state_tokens:
                cs_terminal_tokens = self.state_token_tokens(cs_state_token)
                tokens.extend(cs_terminal_tokens)
        elif name in primitive_control_sequences_map:
            token_type = primitive_control_sequences_map[name]
            tokens.append(PLYToken(type_=token_type, value=state_token))
            if name in read_control_sequence_name_tokens:
                next_tokens = self.fetch_state_token_tokens_no_expand()
                assert len(next_tokens) == 1
                tokens.extend(next_tokens)
        elif name in ('global', 'long', 'outer'):
            tokens.append(PLYToken(type_='PREFIX', value=state_token))
        else:
            import pdb; pdb.set_trace()
        return tokens

    def state_token_tokens_char(self, state_token):
        tokens = []
        char, cat = state_token['char'], state_token['cat']
        if cat in (CatCode.letter, CatCode.other):
            if (char, cat) in literals_map:
                type_ = literals_map[(char, cat)]
            else:
                type_ = 'CHARACTER'
        elif cat in category_map:
            type_ = category_map[cat]
        else:
            import pdb; pdb.set_trace()
        token = PLYToken(type_, value=state_token)
        tokens.append(token)
        # TODO: this will probably break when using backticks for
        # open-quotes.
        # Maybe move this to parse rule, at seen_BACKTICK?
        if type_ == 'BACKTICK':
            next_tokens = self.fetch_state_token_tokens_no_expand()
            assert len(next_tokens) == 1
            tokens.extend(next_tokens)
        return tokens

    def state_token_tokens(self, state_token):
        '''
        Converts a single state token into one or more terminal tokens.
        One important case where one state token produces many terminal tokens,
        is when the state token is a macro call, which is expanded into the
        stored state tokens.
        '''
        tokens = []
        if state_token['type'] == 'control_sequence':
            tokens = self.state_token_tokens_control_sequence(state_token)
        elif state_token['type'] == 'char_cat_pair':
            tokens = self.state_token_tokens_char(state_token)
        elif state_token['type'] in short_hand_def_token_map:
            type_ = short_hand_def_token_map[state_token['type']]
            token = PLYToken(type_=type_, value=state_token['value'])
            tokens.append(token)
        else:
            import pdb; pdb.set_trace()
        logger.info(tokens)
        return tokens

    def token(self):
        if not self.tokens_stack:
            try:
                tokens = self.fetch_state_token_tokens()
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
