__all__ = ['VirtualCharacter']

from ..Tools.Stream import ByteStream


class VirtualCharacter(object):

    def __init__(self, char_code, width, dvi):

        self.char_code = char_code
        self.width = width
        self._dvi = dvi
        self._subroutine = None

    def __repr__(self):

        return "Virtual Character {}".format(self.char_code)

    @property
    def subroutine(self):

        if self._subroutine is None:
            # Fixme: circular import ?
            from ..Dvi.DviParser import DviSubroutineParser
            parser = DviSubroutineParser(ByteStream(self._dvi))
            self._subroutine = parser.parse()
        return self._subroutine
