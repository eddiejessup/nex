class LayoutList(object):
    pass


class ListElement(object):

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.__dict__.__repr__())


# All modes.


#     Boxes.


class AbstractBox(ListElement):

    discardable = False

    def __init__(self, specification, contents):
        self.specification = specification
        self.contents = contents

    @property
    def widths(self):
        return [e.natural_width for e in self.contents]

    @property
    def heights(self):
        return [e.natural_height for e in self.contents]


class HBox(AbstractBox):

    @property
    def natural_width(self):
        return sum(self.widths)

    @property
    def natural_height(self):
        return max(self.heights)


class VBox(AbstractBox):

    @property
    def natural_width(self):
        return max(self.widths)

    @property
    def natural_height(self):
        return sum(self.heights)


class Rule(ListElement):
    discardable = False

    def __init__(self, width, height, depth):
        self.width = width
        self.height = height
        self.depth = depth

    @property
    def natural_width(self):
        return self.width

    @property
    def natural_height(self):
        return self.height


#     /Boxes.
#     Miscellanea.

class WhatsIt(ListElement):
    discardable = False

    @property
    def natural_width(self):
        return 0

    @property
    def natural_height(self):
        return 0


class Glue(ListElement):
    discardable = True

    def __init__(self, dimen, stretch=None, shrink=None):
        self.dimen = dimen
        self.stretch = stretch
        self.shrink = shrink

    @property
    def natural_width(self):
        if self.dimen is None:
            import pdb; pdb.set_trace()
        return self.dimen

    natural_height = natural_width


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

    def __init__(self, char, font):
        self.char = char
        self.font = font

    @property
    def code(self):
        return ord(self.char)

    @property
    def natural_width(self):
        return self.font.width(self.code)

    @property
    def natural_height(self):
        return self.font.height(self.code)


class Ligature(ListElement):
    discardable = False
    pass


#     /Boxes.
#     Miscellanea.


class DiscretionaryBreak(ListElement):
    discardable = False


class MathOn(ListElement):
    discardable = True


class MathOff(ListElement):
    discardable = True


#     /Miscellanea.
#     Vertical material.


class VAdjust(ListElement):
    discardable = False


#     /Vertical material.

# Fake items for font things.


class FontDefinition(ListElement):
    discardable = False

    def __init__(self, font_nr, font_name, file_name, at_clause=None):
        self.font_nr = font_nr
        self.font_name = font_name
        self.file_name = file_name
        self.at_clause = at_clause

    @property
    def natural_width(self):
        return 0

    @property
    def natural_height(self):
        return 0


class FontSelection(ListElement):
    discardable = False

    def __init__(self, font_nr):
        self.font_nr = font_nr

    @property
    def natural_width(self):
        return 0

    @property
    def natural_height(self):
        return 0
