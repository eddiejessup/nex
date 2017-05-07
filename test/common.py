import os
from enum import Enum

dir_path = os.path.dirname(os.path.realpath(__file__))
test_file_dir_path = os.path.join(dir_path, 'test_files')
test_file_name = os.path.join(test_file_dir_path, 'test.tex')
test_not_here_file_name = os.path.join(test_file_dir_path, 'not_here.tex')

test_chars = list('abc\n')
test_2_chars = list('def\n')


class DummyInstructions(Enum):
    test = 'TEST'
