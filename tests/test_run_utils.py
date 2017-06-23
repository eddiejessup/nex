from nex.state import GlobalState
from nex import run_utils

from common import test_runnable_file_name, test_file_dir_path


def test_make_input_chain():
    state = GlobalState.from_defaults()
    run_utils.make_input_chain(state)


def test_run_file():
    run_utils.run_files(input_paths=[test_runnable_file_name],
                        font_search_paths=[test_file_dir_path])
