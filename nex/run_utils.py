from .reader import Reader
from .lexer import Lexer
from .router import Instructioner
from .banisher import Banisher
from .state import GlobalState, TidyEnd
from .parsing.parsing import command_parser
from .parsing.utils import chunk_iter
from .box_writer import write_to_dvi_file


def make_input_chain(state):
    reader = Reader()
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


def run_state(state, input_paths):
    banisher, reader = make_input_chain(state)

    command_grabber = chunk_iter(banisher, command_parser)
    for input_path in input_paths:
        reader.insert_file(input_path)
        state.execute_command_tokens(command_grabber, banisher, reader)

    while True:
        s = input('In: ')
        reader.insert_string(s + '\n')
        command_grabber = chunk_iter(banisher, command_parser)
        state.execute_command_tokens(command_grabber, banisher, reader)


def run_files(font_search_paths, input_paths):
    state = GlobalState.from_defaults(font_search_paths)
    try:
        run_state(state, input_paths)
    except TidyEnd:
        return state
    raise Exception('Left run_state without TidyEnd occurring.')


def run_and_write(font_search_paths, input_paths, dvi_path, write_pdf):
    state = run_files(font_search_paths, input_paths)
    write_to_dvi_file(state, dvi_path, write_pdf=write_pdf)
