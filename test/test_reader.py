from ..reader import Reader


test_file_name = 'test.tex'


def test_init():
    r = Reader(test_file_name)
    assert r.i == -1
