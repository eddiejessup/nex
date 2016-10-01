import logging

from dampf.dvi_document import DVIDocument

from state import GlobalState
from reader import Reader
from lexer import Lexer
from banisher import Banisher
from executor import execute_commands, write_box_to_doc, CommandGrabber
from parser import parser


ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(ch)

# def test_reader():
#     file_name = 'p.tex'
#     r = Reader(file_name)
#     while True:
#         try:
#             c = r.next_char
#         except EndOfFile:
#             break
#         print(c)


# def test_lexer():
#     file_name = 'p.tex'
#     r = Reader(file_name)
#     lex = Lexer(r)
#     while True:
#         try:
#             lt = lex.next_token
#         except EndOfFile:
#             break
#         print(lt)


# def test_typer():
#     file_name = 'p.tex'
#     r = Reader(file_name)
#     lex = Lexer(r)
#     ty = Typer(lex)
#     while True:
#         try:
#             tt = ty.next_token
#         except EndOfFile:
#             break
#         print(tt)

# def test_banisher():
#     file_name = 'p.tex'
#     r = Reader(file_name)
#     lex = Lexer(r)
#     e = Expander()
#     b = Banisher(lex, e)
#     while True:
#         try:
#             tt = b.next_token
#         except EndOfFile:m
#             break
#         print(tt)


def test_parser():
    file_name = 'test.tex'
    # file_name = 'plain.tex'

    state = GlobalState()
    reader = Reader(file_name)
    lexer = Lexer(reader, state)
    banisher = Banisher(lexer, state=state, reader=reader)

    command_grabber = CommandGrabber(banisher, parser=parser)
    execute_commands(command_grabber, state=state, banisher=banisher,
                     reader=reader)

    magnification = state.get_parameter_value('mag')
    doc = DVIDocument(magnification)
    total_layout_list = state.pop_mode()
    write_box_to_doc(doc, total_layout_list)
    doc.write('oot.dvi')

if __name__ == '__main__':
    test_parser()
