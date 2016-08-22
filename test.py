from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander
from parser import parser, lex_wrapper


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
#         except EndOfFile:
#             break
#         print(tt)


def test_parser():
    file_name = 'p.tex'
    result = parser.parse(file_name, lexer=lex_wrapper)
    for term_tok in result:
        print(term_tok)


if __name__ == '__main__':
    test_parser()
# # result = parser.parse(chars, lexer=lexer, debug=logger)
# result = parser.parse(chars, lexer=lexer)
# print()
# print('Parsed:')
# for s in result:
#     print(s)
# import pdb; pdb.set_trace()
