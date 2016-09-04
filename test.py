from collections import deque
import logging

from utils import post_mortem
from parse_utils import LexWrapper
from reader import Reader, EndOfFile
from lexer import Lexer
from banisher import Banisher
from expander import Expander
from parser import parser
from condition_parser import condition_parser, ExpectedParsingError


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


class CommandGrabber(object):

    def __init__(self, banisher, lex_wrapper):
        self.banisher = banisher
        self.lex_wrapper = lex_wrapper

        self.condition_buffer_stack = deque()

    def get_command(self):
        condition_parse_stack = deque()
        have_parsed = False
        while True:
            # While populating this, maybe we will see an if_type in the
            # condition. Haven't tested, but it seems like this should
            # recurse correctly.
            t = self.banisher.pop_or_fill_and_pop(self.condition_buffer_stack)
            condition_parse_stack.append(t)
            try:
                outcome = parser.parse(iter(condition_parse_stack),
                                       state=self.lex_wrapper)
            except (ExpectedParsingError, StopIteration):
                if have_parsed:
                    break
            else:
                have_parsed = True
        self.condition_buffer_stack.appendleft(condition_parse_stack.pop())
        return outcome


def test_parser():
    file_name = 'p.tex'
    lex_wrapper = LexWrapper(file_name)

    b = lex_wrapper.b
    grabber = CommandGrabber(b, lex_wrapper)

    commands = []
    while True:
        try:
            command = grabber.get_command()
        except EndOfFile:
            break
        else:
            commands.append(command)

    import pdb; pdb.set_trace()


    # result = parser.parse(lex_wrapper, state=lex_wrapper)
    # # result = parser.parse(file_name, lexer=lex_wrapper, debug=logger)
    # for term_tok in result:
    #     print(term_tok)
    # post_mortem(lex_wrapper, parser)

if __name__ == '__main__':
    test_parser()
