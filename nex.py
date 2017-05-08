#!/usr/bin/env python3

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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('input')
    parser.add_argument('--pdf', action='store_true')
    parser.add_argument('-f', '--fonts', nargs='*')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--output')
    group.add_argument('-s', '--stdout', action='store_true')

    args = parser.parse_args()

    font_search_paths = default_font_search_paths[:]
    if args.fonts:
        font_search_paths += args.fonts
    in_dir_path = opath.dirname(args.input)
    font_search_paths += [in_dir_path, opath.join(in_dir_path, 'fonts')]

    if args.stdout:
        dvi_path = sys.stdout.buffer
    elif args.output:
        dvi_path = ensure_extension(args.output, 'dvi')
    else:
        dvi_path = opath.splitext(opath.basename(args.input))[0]
        dvi_path = ensure_extension(dvi_path, 'dvi')

    print(f'Reading from {args.input}')
    print(f'Writing DVI to {dvi_path}')
    state = run_file(args.input, font_search_paths)
    write_to_dvi_file(state, dvi_path, args.pdf)
