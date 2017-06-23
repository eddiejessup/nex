import logging
import argparse
import os.path as opath
import sys

from .utils import ensure_extension, get_default_font_paths
from .run_utils import run_and_write
from .reader import logger as read_logger
from .lexer import logger as lex_logger
from .router import logger as instr_logger
from .banisher import logger as banish_logger
from .parsing.utils import logger as chunk_logger
from .state import logger as state_logger

dir_path = opath.dirname(opath.realpath(__file__))


default_font_search_paths = get_default_font_paths() + [
    dir_path,
    opath.join(dir_path, 'fonts'),
]


def log_level(v):
    short_map = {
        'D': 'DEBUG',
        'I': 'INFO',
        'W': 'WARNING',
        'E': 'ERROR',
        'C': 'CRITICAL',
    }
    v = v.upper()
    if v in short_map:
        v = short_map[v]
    if v not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        raise argparse.ArgumentTypeError('Invalid log level')
    return v


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('inputs', nargs='*')
    parser.add_argument('--pdf', action='store_true')
    parser.add_argument('-f', '--fonts', nargs='*')

    out_group = parser.add_mutually_exclusive_group()
    out_group.add_argument('-o', '--output')
    out_group.add_argument('-t', '--test', action='store_true')
    out_group.add_argument('-s', '--stdout', action='store_true')

    log_group = parser.add_mutually_exclusive_group()
    log_group.add_argument('-l', '--log', dest='log_level',
                           type=log_level,
                           help='Set the logging level')
    log_group.add_argument('-v', '--verbose', action='store_true')
    log_group.add_argument('-d', '--debug', action='store_true')

    args = parser.parse_args()

    if args.log_level:
        logging.basicConfig(level=getattr(logging, args.log_level))
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)
        read_logger.setLevel(logging.WARNING)
        lex_logger.setLevel(logging.WARNING)
        instr_logger.setLevel(logging.WARNING)
        banish_logger.setLevel(logging.WARNING)
        chunk_logger.setLevel(logging.WARNING)
        state_logger.setLevel(logging.INFO)
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG)
        read_logger.setLevel(logging.WARNING)
        lex_logger.setLevel(logging.WARNING)
        instr_logger.setLevel(logging.INFO)
        banish_logger.setLevel(logging.INFO)
        chunk_logger.setLevel(logging.DEBUG)
        state_logger.setLevel(logging.INFO)

    font_search_paths = default_font_search_paths[:]
    if args.fonts:
        font_search_paths += args.fonts
    for input_path in args.inputs:
        in_dir_path = opath.dirname(input_path)
        font_search_paths += [in_dir_path, opath.join(in_dir_path, 'fonts')]

    if args.test:
        dvi_path = None
    elif args.stdout:
        dvi_path = sys.stdout.buffer
    elif args.output:
        dvi_path = ensure_extension(args.output, 'dvi')
    elif args.inputs:
        dvi_path = opath.splitext(opath.basename(args.inputs[-1]))[0]
        dvi_path = ensure_extension(dvi_path, 'dvi')
    else:
        dvi_path = 'nexput.dvi'

    if args.test:
        print('Not writing output in test mode')
    else:
        print(f'Writing DVI to {dvi_path}')

    run_and_write(font_search_paths, args.inputs, dvi_path, args.pdf)


if __name__ == '__main__':
    main()
