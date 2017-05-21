from nex.state import GlobalState
from nex import nex

from common import test_runnable_file_name, test_file_dir_path


def test_make_input_chain():
    state = GlobalState.from_defaults()
    nex.make_input_chain(test_runnable_file_name, state)


def test_run_file():
    nex.run_file(test_runnable_file_name,
                 font_search_paths=[test_file_dir_path])
