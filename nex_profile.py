import cProfile as prof
import os.path as opath

from nex.nex import run_file
from nex.utils import get_default_font_paths
from nex.box_writer import write_to_dvi_file


dir_path = opath.dirname(opath.realpath(__file__))


font_search_paths = get_default_font_paths() + [
    dir_path,
    opath.join(dir_path, 'fonts'),
]


def t():
    state = run_file("tex/test.tex", font_search_paths)
    write_to_dvi_file(state, 'prof_out.dvi', write_pdf=True)

prof.run('t()', 'prof_stats')
