import logging

from banisher import LexWrapper
from reader import EndOfFile
from parser import parser, CommandGrabber


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
    file_name = 'p.tex'
    lex_wrapper = LexWrapper(file_name)

    b = lex_wrapper.b
    grabber = CommandGrabber(b, lex_wrapper, parser=parser)
    commands = list(grabber.get_commands_until_end())

    # for command in commands:
    #     print(command)
    #     print()

    # result = parser.parse(lex_wrapper, state=lex_wrapper)
    # # result = parser.parse(file_name, lexer=lex_wrapper, debug=logger)
    # for term_tok in result:
    #     print(term_tok)
    # post_mortem(lex_wrapper, parser)

if __name__ == '__main__':
    test_parser()
