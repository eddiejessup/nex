import logging

from utils import post_mortem
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander
from parser import parser, LexWrapper

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

    result = parser.parse(lex_wrapper, state=lex_wrapper)
    # result = parser.parse(file_name, lexer=lex_wrapper, debug=logger)
    # post_mortem(lex_wrapper, parser)
    for term_tok in result:
        print(term_tok)

if __name__ == '__main__':
    test_parser()
