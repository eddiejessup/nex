import logging
import os

from nex.dampf.dvi_document import DVIDocument

from nex.state import GlobalState
from nex.reader import Reader
from nex.lexer import Lexer
from nex.banisher import Banisher
from nex.executor import execute_commands, write_box_to_doc, CommandGrabber
from nex.parser import parser


dir_path = os.path.dirname(os.path.realpath(__file__))


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)


def run_file(in_path):
    state = GlobalState()
    reader = Reader(in_path)
    lexer = Lexer(reader, state)
    banisher = Banisher(lexer, state=state, reader=reader)

    command_grabber = CommandGrabber(banisher, parser=parser)
    execute_commands(command_grabber, state=state, banisher=banisher,
                     reader=reader)
    return state


def write_to_file(state, out_path):
    magnification = state.get_parameter_value('mag')
    doc = DVIDocument(magnification)
    total_layout_list = state.pop_mode()
    write_box_to_doc(doc, total_layout_list)
    doc.write(out_path)


if __name__ == '__main__':
    # in_path = os.path.join(dir_path, 'test.tex')
    in_path = os.path.join(dir_path, 'plain.tex')
    state = run_file(in_path)
    out_path = in_path[:-4] + '.dvi'
    write_to_file(state, out_path)
