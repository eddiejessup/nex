import logging

from parse import parser, lexer

logger = logging.getLogger(__name__)
logger.setLevel('DEBUG')


with open('p.tex', 'rb') as f:
    chars = [chr(b) for b in f.read()]

# result = parser.parse(chars, lexer=lexer, debug=logger)
result = parser.parse(chars, lexer=lexer)
print()
print('Parsed:')
for s in result:
    print(s)
import pdb; pdb.set_trace()
