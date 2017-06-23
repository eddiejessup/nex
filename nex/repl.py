import argparse

from .state import GlobalState
from .parsing.command_parser import command_parser
from .box_writer import write_to_dvi_file
from .utils import TidyEnd
from .run_utils import make_input_chain
from .parsing.utils import chunk_iter


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-f', '--fonts', nargs='*')
    parser.add_argument('-fmt', '--format')

    args = parser.parse_args()

    # TODO: Augment font search paths with sensible defaults, like nex.
    state = GlobalState.from_defaults(font_search_paths=args.fonts)

    # Set up input chain.
    banisher, reader = make_input_chain(state)
    command_grabber = chunk_iter(banisher, command_parser)

    # Execute format file.
    reader.insert_file(args.format)
    state.execute_command_tokens(command_grabber, banisher, reader)

    while True:
        s = input('In: ')
        reader.insert_string(s + '\n')

        try:
            state.execute_command_tokens(command_grabber, banisher, reader)
        except TidyEnd:
            break
    # out_path = sys.stdout.buffer
    write_to_dvi_file(state, 'repl.dvi', write_pdf=True)
