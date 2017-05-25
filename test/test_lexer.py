from nex.constants.codes import CatCode
from nex.accessors import Codes
from nex.lexer import Lexer


class DummyCatCodeGetter:

    def __init__(self):
        self.char_to_cat = Codes.default_initial_cat_codes()

    def get(self, char):
        return self.char_to_cat[char]


def lex_string_to_tokens(s):
    cat_code_getter = DummyCatCodeGetter()
    lex = Lexer.from_string(s, get_cat_code_func=cat_code_getter.get)
    return list(lex.advance_to_end())


def test_trioing():
    """Check trioing (escaping characters to obtain exotic character codes)."""
    test_input = 'abc^^I^^K^^>'

    # The code numbers we should return if all is well.
    correct_code_nrs = [ord('a'), ord('b'), ord('c'),
                        ord('\t'), ord('K') - 64, ord('>') + 64]

    # Check with various characters, including the usual '^'.
    for trio_char in ['^', '1', '@']:
        cat_code_getter = DummyCatCodeGetter()
        # Set our chosen trioing character to have superscript CatCode, so we
        # can use it for trioing (this is a necessary condition to trigger it).
        cat_code_getter.char_to_cat[trio_char] = CatCode.superscript
        # Input the test string, substituted with the chosen trioing character.
        lex = Lexer.from_string(test_input.replace('^', trio_char),
                                cat_code_getter.get)

        tokens = list(lex.advance_to_end())

        # Check correct number of tokens were returned
        assert len(tokens) == 6
        # Check the correct code numbers were returned.
        assert [ord(t.value['char']) for t in tokens] == correct_code_nrs
        # Check the correct character positions and lengths are returned.
        assert [t.char_nr for t in tokens] == [0, 1, 2, 3, 6, 9]
        assert [t.char_len for t in tokens] == [1, 1, 1, 3, 3, 3]


def test_comments():
    """Check comment characters."""
    tokens = lex_string_to_tokens(r'hello% say hello')
    assert [t.value['char'] for t in tokens] == list('hello')


def test_skipping_blanks():
    """Check multiple spaces are ignored."""
    toks_single = lex_string_to_tokens(r'hello m')
    toks_triple = lex_string_to_tokens(r'hello   m')
    # Check same char-cat pairs are returned.
    assert ([t.value['char'] for t in toks_single] ==
            [t.value['char'] for t in toks_triple])
    assert ([t.value['cat'] for t in toks_single] ==
            [t.value['cat'] for t in toks_triple])
    # Check same character lengths are returned.
    assert ([t.char_len for t in toks_single] ==
            [t.char_len for t in toks_triple])
    # Check same character positions are returned, except last token.
    assert ([t.char_nr for t in toks_single[:-1]] ==
            [t.char_nr for t in toks_triple[:-1]])
    # For last tokens, check the spaces are considered correctly when assigning
    # their positions.
    assert toks_single[-1].char_nr == 6
    assert toks_triple[-1].char_nr == 8


def test_control_sequence():
    """Check multiple spaces are ignored."""
    tokens = lex_string_to_tokens(r'a\howdy\world')
    assert len(tokens) == 3

    assert tokens[0].value['char'] == 'a'
    assert tokens[0].char_nr == 0
    assert tokens[0].char_len == 1

    assert tokens[1].value == 'howdy'
    assert tokens[1].char_nr == 1
    assert tokens[1].char_len == 6

    assert tokens[2].value == 'world'
    assert tokens[2].char_nr == 7
    assert tokens[2].char_len == 6

    # Check control sequences starting with a non-letter, make single-letter
    # control sequences.
    tokens_single = lex_string_to_tokens(r'\@a')
    assert tokens_single[0].value == '@' and len(tokens_single) == 2


def test_control_sequence_spacing():
    """Check multiple spaces are ignored."""
    tokens_close = lex_string_to_tokens(r'\howdy\world')
    tokens_spaced = lex_string_to_tokens(r'\howdy \world')
    tokens_super_spaced = lex_string_to_tokens(r'\howdy  \world')
    assert len(tokens_close) == len(tokens_spaced) == len(tokens_super_spaced)


def test_new_lines():
    """Check what happens when entering new-lines."""
    # Note that I'm not even sure what the specification says *should* happen
    # here.
    # Check entering once in the middle of a line makes a space.
    tokens = lex_string_to_tokens('a\n')
    assert len(tokens) == 2 and tokens[1].value['char'] == ' '
    # Check entering a new-line at a line beginning gives a \par.
    tokens = lex_string_to_tokens('a\n\n')
    assert (len(tokens) == 3 and tokens[1].value['char'] == ' ' and
            tokens[2].value == 'par')
    # Check entering a new-line when skipping spaces does nothing. Note that a
    # space *is* returned, but from the first space after the 'a'.
    tokens = lex_string_to_tokens('a  \n')
    assert len(tokens) == 2 and tokens[1].value['char'] == ' '


def test_tokenise():
    """Check what happens when entering non-lexical tokens."""
    s = '@${'
    tokens = lex_string_to_tokens(s)
    assert len(tokens) == 3
    # Tokens should just be wrapped as a lexical token, with the character
    # returned by the reader, and category assigned by the state.
    for c, t in zip(s, tokens):
        assert t.value['char'] == c
        assert t.value['cat'] == CatCode.other
