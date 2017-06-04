import pytest

from nex.fonts import GlobalFontState


def test_skew_char():
    gfs = GlobalFontState()
    gfs.set_skew_char(0, 65)
    with pytest.raises(KeyError):
        gfs.set_skew_char(1, 65)


def test_hyphen_char():
    gfs = GlobalFontState()
    gfs.set_hyphen_char(0, 65)
    with pytest.raises(KeyError):
        gfs.set_hyphen_char(1, 65)
