import os

import pytest

from nex.codes import get_initial_char_cats
from nex.reader import Reader, EndOfFile
from nex.lexer import Lexer
from nex.typer import CatCode

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')
test_2_file_name = os.path.join(test_file_dir_path, 'test_2.tex')
test_not_here_file_name = os.path.join(test_file_dir_path, 'not_here.tex')


class DummyGlobalState:

    def __init__(self):
        self.char_to_cat = get_initial_char_cats()

    def get_cat_code(self, char):
        return self.char_to_cat[char]


def test_trioing():
    sample_s = 'abc^^I^^K^^>'

    # The code numbers we should return if all is well.
    correct_code_nrs = [ord('a'), ord('b'), ord('c'),
                        ord('\t'), ord('K') - 64, ord('>') + 64]

    # Check with various characters, including the usual '^'.
    for trio_char in ['^', '1', '@']:
        reader = Reader()
        reader.insert_string(sample_s.replace('^', trio_char))
        state = DummyGlobalState()
        # Set our chosen trioing character to have superscript CatCode, so we
        # can use it for trioing (this is a necessary condition to trigger it).
        state.char_to_cat[trio_char] = CatCode.superscript
        lex = Lexer(reader, state)

        # Lex the string into tokens.
        tokens = [lex.next_token for _ in range(6)]

        # Check the correct code numbers are returned.
        assert [ord(tok.value['char']) for tok in tokens] == correct_code_nrs
        # Check the correct character positions and lengths are returned.
        assert [tok.char_nr for tok in tokens] == [0, 1, 2, 3, 6, 9]
        assert [tok.char_len for tok in tokens] == [1, 1, 1, 3, 3, 3]

        # Check no more tokens will be lexed.
        with pytest.raises(EndOfFile):
            lex.next_token()
