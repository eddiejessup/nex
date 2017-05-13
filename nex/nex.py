from .utils import TidyEnd
from .state import GlobalState
from .reader import Reader
from .lexer import Lexer
from .instructioner import Instructioner
from .banisher import Banisher
from .parsing.parsing import command_parser
from .parsing.utils import safe_chunk_grabber


def run_file(in_path, font_search_paths):
    reader = Reader()
    reader.insert_file(in_path)
    state = GlobalState.from_defaults(font_search_paths)
    lexer = Lexer(reader, get_cat_code_func=state.codes.get_cat_code)
    instructioner = Instructioner(lexer)
    banisher = Banisher(
        instructions=instructioner, state=state, reader=reader,
    )
    with safe_chunk_grabber(banisher, command_parser) as command_grabber:
        try:
            state.execute_commands(command_grabber, banisher, reader)
        except TidyEnd:
            return state
    return state
