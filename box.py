class LayoutList(object):
    pass


class ListElement(object):

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.__dict__.__repr__())


# All modes.


#     Boxes.


class HBox(ListElement):
    discardable = False

    def __init__(self, specification, contents):
        self.specification = specification
        self.contents = contents


class VBox(ListElement):
    discardable = False
    pass


class Rule(ListElement):
    discardable = False

    def __init__(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth


#     /Boxes.
#     Miscellanea.

class WhatsIt(ListElement):
    discardable = False
    pass


class Glue(ListElement):
    discardable = True

    def __init__(self, dimen, stretch=None, shrink=None):
        self.dimen = dimen
        self.stretch = stretch
        self.shrink = shrink


class Leaders(ListElement):
    discardable = True
    pass


class Kern(ListElement):
    discardable = True
    pass


class Penalty(ListElement):
    discardable = True
    pass


#     /Miscellanea.
#     Vertical material.


class Mark(ListElement):
    discardable = False
    pass


class Insertion(ListElement):
    discardable = False
    pass


#     /Vertical material.


# Horizontal mode only.


#     Boxes.

class Character(ListElement):
    discardable = False

    def __init__(self, char):
        self.char = char

    @property
    def code(self):
        return ord(self.char)


class Ligature(ListElement):
    discardable = False
    pass


#     /Boxes.
#     Miscellanea.


class DiscretionaryBreak(ListElement):
    discardable = False
    pass


class MathOn(ListElement):
    discardable = True
    pass


class MathOff(ListElement):
    discardable = True
    pass


#     /Miscellanea.
#     Vertical material.


class VAdjust(ListElement):
    discardable = False
    pass


#     /Vertical material.

# Fake items for font things.


class FontDefinition(ListElement):
    discardable = False

    def __init__(self, font_nr, font_name, file_name, at_clause=None):
        self.font_nr = font_nr
        self.font_name = font_name
        self.file_name = file_name
        self.at_clause = at_clause


class FontSelection(ListElement):
    discardable = False

    def __init__(self, font_nr):
        self.font_nr = font_nr
