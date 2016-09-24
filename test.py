import logging

from dvi_api.dvi_document import DVIDocument

from banisher import LexWrapper
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
    # file_name = 'test.tex'
    file_name = 'plain.tex'
    lex_wrapper = LexWrapper(file_name)

    b = lex_wrapper.b
    st = lex_wrapper.state
    command_grabber = CommandGrabber(b, parser=parser)
    box = execute_commands(command_grabber, state=st, reader=lex_wrapper.r)
    print(box)

    magnification = st.get_parameter_value('mag')
    doc = DVIDocument(magnification)
    write_box_to_doc(doc, box)
    doc.write('oot.dvi')

if __name__ == '__main__':
    test_parser()
