from collections import deque

from common import Token, TerminalToken
from typer import get_char_cat_pair_terminal_type

# tokens = (
#     'CONTROL_SEQUENCE',
#     'SINGLE_CHAR_CONTROL_SEQUENCE',

#     'PREFIX',

#     'SPACE',
#     'LEFT_BRACE',
#     'RIGHT_BRACE',
#     'ACTIVE_CHARACTER',

#     'BALANCED_TEXT',

#     'CHARACTER',
# )

# read_control_sequence_name_tokens = (
#     'def',
# )
# read_control_sequence_name_tokens += tuple(set(short_hand_def_map.keys()))


# def fetch_state_tokens_in_balanced_text(self):
#     brace_counter = 1
#     state_tokens = []
#     while True:
#         state_token = next(self.state_tokens)
#         if state_token.type == 'CHAR_CAT_PAIR':
#             char, cat = state_token.value['char'], state_token.value['cat']
#             if cat == CatCode.begin_group:
#                 brace_counter += 1
#             elif cat == CatCode.end_group:
#                 brace_counter -= 1
#             if brace_counter == 0:
#                 break
#         state_tokens.append(state_token)
#     return state_tokens


# def fetch_state_token_tokens(self):
#     if self.lex_mode == LexMode.read_balanced_text:
#         state_tokens = self.fetch_state_tokens_in_balanced_text()
#         token = Token(type_='BALANCED_TEXT', value=state_tokens)
#         self.lex_mode = LexMode.expand
#         return [token]
#     else:
#         state_token = next(self.state_tokens)
#         return self.state_token_tokens(state_token)


# def fetch_state_token_tokens_no_expand(self):
#     '''
#     Fetch a single state token, in no-expand lex mode, and convert it into
#     its terminal tokens.
#     '''
#     old_lex_mode = self.lex_mode
#     self.lex_mode = LexMode.no_expand
#     tokens = self.fetch_state_token_tokens()
#     self.lex_mode = old_lex_mode
#     return tokens

#     def state_token_tokens_control_sequence(self, state_token):
#         tokens = []
#         name = state_token.value['name']
#         if len(name) == 1:
#             type_ = 'SINGLE_CHAR_CONTROL_SEQUENCE'
#         else:
#             type_ = 'CONTROL_SEQUENCE'
#             tokens.append(Token(type_=type_, value=state_token))
#         elif name in primitive_control_sequences_map:
#             token_type = primitive_control_sequences_map[name]
#             tokens.append(Token(type_=token_type, value=state_token))
#         elif name in ('global', 'long', 'outer'):
#             tokens.append(Token(type_='PREFIX', value=state_token))


# class LexMode(Enum):
#     expand = 1
#     read_balanced_text = 2
#     no_expand = 3


            # if name in read_control_sequence_name_tokens:
            #     next_tokens = self.fetch_state_token_tokens_no_expand()
            #     assert len(next_tokens) == 1
            #     tokens.extend(next_tokens)


class Banisher(object):

    def __init__(self, lexer, expander):
        self.lexer = lexer
        self.expander = expander
        # Input buffer.
        self.input_tokens_stack = deque()
        # Output buffer.
        self.output_terminal_tokens_stack = deque()
        self.expanding_control_sequences = True

    @property
    def _next_lex_token(self):
        return self.lexer.next_token

    @property
    def next_token(self):
        if not self.output_terminal_tokens_stack:
            self.populate_output_stack()
        return self.output_terminal_tokens_stack.popleft()

    def populate_input_stack(self):
        fresh_lex_token = self._next_lex_token
        self.input_tokens_stack.append(fresh_lex_token)

    def pop_next_token(self):
        if not self.input_tokens_stack:
            self.populate_input_stack()
        return self.input_tokens_stack.popleft()

    def is_syntactic_token(self, primitive_token):
        if primitive_token.type == 'BACKTICK':
            return True
        return False

    def populate_output_stack(self):
        # To reduce my own confusion:
        # a primitive token is one that is not a lex token. But it might not be
        # a terminal token either, if it needs combining with other tokens
        # to make a terminal token. For instance, a primitive token might be a
        # \def that needs combining with the rest of its bits to make a
        # DEFINITION terminal token.
        # But I might blur the line between these two sometimes.

        # A terminal token is simply a token that is accepted by the parser.

        # Might be a lex token, a primitive token or a terminal token.
        first_token = self.pop_next_token()

        # If we get a lex token, we need to make it a terminal token, and run again.
        if not isinstance(first_token, TerminalToken):
            # If we have a char-cat pair, we must type it to its terminal version,
            if first_token.type == 'CHAR_CAT_PAIR':
                terminal_token_type = get_char_cat_pair_terminal_type(first_token)
                terminal_token = TerminalToken(type_=terminal_token_type,
                                               value=first_token.value)
                self.input_tokens_stack.appendleft(terminal_token)
            elif first_token.type == 'CONTROL_SEQUENCE':
                name = first_token.value
                if self.expanding_control_sequences:
                    # Replace it with its contents and go again.
                    # This might be expanding a user control sequence,
                    # or just mapping a lex token to its primitive token equivalent.
                    # import pdb; pdb.set_trace()
                    expanded_first_token = self.expander.expand_to_token_list(name)
                    self.input_tokens_stack.extendleft(expanded_first_token[::-1])
                else:
                    # Convert to a primitive unexpanded control sequence.
                    terminal_token = TerminalToken(type_='UNEXPANDED_CONTROL_SEQUENCE', value=name)
                    self.input_tokens_stack.appendleft(terminal_token)
            else:
                import pdb; pdb.set_trace()
            # Run again, hopefully now seeing a primitive token.
            # (Might not, if the expansion needs more expansion, but the
            # ultimate escape route is to see a primitive token.)
            self.populate_output_stack()
        # We might be able to make some terminal output, hooray.
        else:
            # Complicated syntactic token that might affect lexing.
            if self.is_syntactic_token(first_token):
                type_ = first_token.type
                if type_ == 'BACKTICK':
                    self.output_terminal_tokens_stack.append(first_token)
                    next_token = self.pop_next_token()
                    if next_token.type == 'CONTROL_SEQUENCE':
                        next_token_name = next_token.value
                        next_terminal_token = TerminalToken(type_='UNEXPANDED_ONE_CHAR_CONTROL_SEQUENCE',
                                                            value=next_token_name)
                        self.output_terminal_tokens_stack.append(next_terminal_token)
                    else:
                        import pdb; pdb.set_trace()
            # Just some semantic bullshit, stick it on the output stack
            # for the interpreter to deal with.
            else:
                self.output_terminal_tokens_stack.append(first_token)
