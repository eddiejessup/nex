import logging
import os

from nex.state import GlobalState
from nex.reader import Reader
from nex.lexer import Lexer
from nex.instructioner import Instructioner
from nex.banisher import Banisher
from nex.box_writer import write_to_file
from nex.parsing.command_parser import command_parser
from nex.parsing.utils import safe_chunk_grabber

dir_path = os.path.dirname(os.path.realpath(__file__))


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


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
        state.execute_commands(command_grabber, banisher, reader)
    return state


if __name__ == '__main__':
    in_path = os.path.join(dir_path, 'test.tex')
    # in_path = os.path.join(dir_path, 'plain.tex')
    font_search_paths = [os.path.join(dir_path, 'fonts')]
    state = run_file(in_path, font_search_paths)
    out_path = in_path[:-4] + '.dvi'
    write_to_file(state, out_path)
