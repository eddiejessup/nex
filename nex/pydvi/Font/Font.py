""" This module provides a base class for font type managed by the font manager.
"""

__all__ = ['Font', 'font_types', 'sort_font_class']

import os

from ..Kpathsea import kpsewhich
from ..Tools.EnumFactory import EnumFactory
from ..Tools.Logging import print_card
from .TfmParser import TfmParser

# Fixme: we could use a metaclass to register the font classes

#: Font Type Enumerate
font_types = EnumFactory(
    'FontTypes', ('Pk', 'Vf', 'Type1', 'TrueType', 'OpenType'))


def sort_font_class(*args):
    """ Sort a list of :class:`Font` instance by font type enumerate. """
    return sorted(args, key=lambda v: v.font_type)


class FontNotFound(NameError):
    pass


class FontMetricNotFound(NameError):
    pass


class Font(object):

    """This class is a base class for font managed by the Font Manager.

    Class attributes to be defined in subclass:

      ``font_type``
        font type enumerate

      ``font_type_string``
        description of the font type

      ``extension``
        file extension

    To create a :class:`Font` instance use::

      font = Font(font_manager, font_id, name)

    where *font_manager* is a :class:`PyDvi.FontManager.FontManager` instance, *font_id* is the font
    id provided by the font manager and *name* is the font name, "cmr10" for example.

    """

    font_type = None
    font_type_string = None
    extension = None

    def __init__(self, font_manager, font_id, name):
        self.font_manager = font_manager
        self.id = font_id  # Fixme: ask the font_manager
        self.name, extension = os.path.splitext(name)
        # Fixme: extension = '' for pk
        # if extension != '.' + self.extension:
        #     raise NameError("Wrong file extension {} versus {}".format(extension, self.extension))

        self._find_font()
        self._find_tfm()

    def __repr__(self):

        return 'Font {}.{}'.format(self.name, self.extension)

    def _find_font(self, kpsewhich_options=None):
        """ Find the font file location in the system using Kpathsea. """
        basename = self.basename()
        self.filename = kpsewhich(basename, options=kpsewhich_options)
        if self.filename is None:
            raise FontNotFound("Font file %s not found" % (basename))

    def _find_tfm(self):
        """ Find the TFM file location in the system using Kpathsea and load it. """

        tfm_file = kpsewhich(self.name, file_format='tfm')
        if tfm_file is None:
            # raise FontMetricNotFound("TFM file was not found for font {}".format(self.name))
            self.tfm = None
        else:
            self.tfm = TfmParser.parse(self.name, tfm_file)

    def basename(self):
        """ Return the basename. """

        return self.name + '.' + self.extension

    @property
    def is_virtual(self):
        return self.font_type == font_types.Vf

    def print_header(self):

        string_format = """%s %s

 - font file: %s
 - tfm  file: %s
"""

        return string_format % (self.font_type_string,
                                self.name,
                                self.filename,
                                self.tfm.filename,
                                )

    def print_summary(self):

        print_card(self.print_header())
