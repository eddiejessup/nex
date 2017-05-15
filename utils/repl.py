from nex.state import GlobalState
from nex.reader import Reader
from nex.lexer import Lexer
from nex.instructioner import Instructioner
from nex.banisher import Banisher
from nex.parsing.command_parser import command_parser
from nex.parsing.utils import ChunkGrabber
from nex.box_writer import write_to_dvi_file
from nex.utils import TidyEnd


reader = Reader()
state = GlobalState.from_defaults(font_search_paths=['/Users/ejm/projects/nex/fonts'])
font_id = state.define_new_font(file_name='cmr10', at_clause=None)
state.select_font(is_global=True, font_id=font_id)

lexer = Lexer(reader, get_cat_code_func=state.codes.get_cat_code)
instructioner = Instructioner(lexer)
banisher = Banisher(instructioner, state, reader)
command_grabber = ChunkGrabber(banisher, command_parser)

reader.insert_file('/Users/ejm/projects/nex/tex/plain.tex')
state.execute_command_tokens(command_grabber, banisher, reader)

while True:
    s = input('In: ')
    reader.insert_string(s + '\n')
    try:
        state.execute_commands(command_grabber, banisher, reader)
    except TidyEnd:
        break
# out_path = sys.stdout.buffer
write_to_dvi_file(state, 'repl.dvi', write_pdf=True)
