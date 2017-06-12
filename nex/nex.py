from .state import GlobalState, TidyEnd
from .reader import Reader
from .lexer import Lexer
from .router import Instructioner
from .banisher import Banisher
from .parsing.parsing import command_parser
from .parsing.utils import chunk_iter
from .box_writer import write_to_dvi_file


def make_input_chain(in_path, state):
    reader = Reader()
    reader.insert_file(in_path)
    lexer = Lexer(reader, get_cat_code_func=state.codes.get_cat_code)
    instructioner = Instructioner(
        lexer=lexer,
        resolve_cs_func=state.router.lookup_control_sequence
    )
    banisher = Banisher(
        instructions=instructioner,
        state=state,
        reader=reader,
    )
    return banisher, reader


def run_file(in_path, font_search_paths):
    state = GlobalState.from_defaults(font_search_paths)
    banisher, reader = make_input_chain(in_path, state)

    command_grabber = chunk_iter(banisher, command_parser)
    try:
        state.execute_command_tokens(command_grabber, banisher, reader)
    except TidyEnd:
        return state
    return state


def run_and_write(tex_path, dvi_path, font_search_paths, convert_to_pdf=False):
    state = run_file(tex_path, font_search_paths)
    if dvi_path is not None:
        write_to_dvi_file(state, dvi_path, convert_to_pdf)
