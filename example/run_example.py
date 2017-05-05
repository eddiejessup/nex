import logging
import os

from nex.state import GlobalState
from nex.reader import Reader
from nex.lexer import Lexer
from nex.instructioner import Instructioner
from nex.banisher import Banisher
from nex.executor import execute_commands
from nex.box_writer import write_to_file
from nex.parsing.command_parser import command_parser
from nex.parsing.utils import ChunkGrabber

dir_path = os.path.dirname(os.path.realpath(__file__))


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


def run_file(in_path, font_search_paths):
    state = GlobalState(font_search_paths)
    reader = Reader()
    reader.insert_file(in_path)
    lexer = Lexer(reader, get_cat_code_func=state.get_cat_code)
    instructioner = Instructioner(lexer)
    banisher = Banisher(instructions=instructioner, state=state, reader=reader)

    command_grabber = ChunkGrabber(banisher, parser=command_parser)
    execute_commands(command_grabber, state=state, banisher=banisher,
                     reader=reader)
    return state


if __name__ == '__main__':
    in_path = os.path.join(dir_path, 'test.tex')
    # in_path = os.path.join(dir_path, 'plain.tex')
    font_search_paths = [os.path.join(dir_path, 'fonts')]
    state = run_file(in_path, font_search_paths)
    out_path = in_path[:-4] + '.dvi'
    write_to_file(state, out_path)
