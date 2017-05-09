#!/usr/bin/env python3

import logging
import argparse
import os.path as opath
import sys

from nex.utils import ensure_extension, get_default_font_paths
from nex.box_writer import write_to_dvi_file
from nex.nex import run_file

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('input')
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
    elif args.debug:
        logging.basicConfig(level=logging.DEBUG)

    font_search_paths = default_font_search_paths[:]
    if args.fonts:
        font_search_paths += args.fonts
    in_dir_path = opath.dirname(args.input)
    font_search_paths += [in_dir_path, opath.join(in_dir_path, 'fonts')]

    if args.stdout:
        dvi_path = sys.stdout.buffer
    elif args.output:
        dvi_path = ensure_extension(args.output, 'dvi')
    elif args.test:
        pass
    else:
        dvi_path = opath.splitext(opath.basename(args.input))[0]
        dvi_path = ensure_extension(dvi_path, 'dvi')

    print(f'Reading from {args.input}')
    if args.test:
        print('Not writing output in test mode')
    else:
        print(f'Writing DVI to {dvi_path}')
    state = run_file(args.input, font_search_paths)
    if not args.test:
        write_to_dvi_file(state, dvi_path, args.pdf)
