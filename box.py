class SettingSetGlue(Exception):
    pass


class GlueNotSet(Exception):
    pass


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
    def natural_widths(self):
        return [e.natural_width for e in self.contents]

    @property
    def natural_heights(self):
        return [e.natural_height for e in self.contents]

    @property
    def widths(self):
        return [e.width for e in self.contents]

    @property
    def heights(self):
        return [e.height for e in self.contents]

    @property
    def glues(self):
        return [e for e in self.contents if isinstance(e, Glue)]


class HBox(AbstractBox):

    @property
    def natural_width(self):
        # The natural width, x, of the box contents is determined by adding up
        # the widths of the boxes and kerns inside, together with the natural
        # widths of all the glue inside.
        return sum(self.natural_widths)

    @property
    def width(self):
        return sum(self.widths)

    @property
    def natural_height(self):
        return max(self.natural_heights)

    @property
    def height(self):
        return max(self.heights)

    @property
    def stretch(self):
        return sum(g.stretch for g in self.glues)

    @property
    def shrink(self):
        return sum(g.shrink for g in self.glues)

    def badness(self, desired_width):
        b = int(round(100 * self.glue_set_ratio(desired_width) ** 3))
        return min(b, 10000)

    def glue_set_ratio(self, desired_width):
        # The total amount of glue stretchability and shrinkability
        # in the box is computed; let's say that there's a total of
        #     y_0 + y_1 fil + y_2 fill + y_3 filll
        # available for stretching and
        #     z_0 + z_1 fil + z_2 fill + z_3 filll
        # available for  shrinking.
        excess_width = self.natural_width - desired_width

        # If x = w, all glue gets its natural width.
        if excess_width == 0:
            return 0.0, None

        # Otherwise the glue will be modified, by computing a 'glue set ratio',
        # r and a 'glue set order', i, in the following way:

        stretching = excess_width < 0

        # If x < w, TeX attempts to stretch the contents of the box; the
        # glue order is the highest subscript i such that y_i is nonzero, and
        # the glue ratio is r = (w - x) / y_i. (If y_0 = y_1 = y_2 = y_3 = 0,
        # there's no stretchability; both i and r are set to zero.)
        if stretching:
            if self.stretch > 0:
                glue_ratio = -excess_width / self.stretch
            else:
                glue_ratio = 0.0

        # If x > w, the glue order is the highest subscript i such that z_i
        # != 0, and the glue ratio is normally r = (x - w) / z_i. However, r is
        # set to 1.0 in the case i=0 and x - w > z_0, because the maximum
        # shrinkability must not be exceeded.
        else:
            if self.stretch > 0:
                glue_ratio = excess_width / self.shrink
                glue_ratio = min(glue_ratio, 1.0)
            else:
                glue_ratio = 0.0
        return glue_ratio, stretching

    def scale_and_set(self, desired_width):
        glue_ratio, stretching = self.glue_set_ratio(desired_width)

        # (c) Finally, every glob of glue in the horizontal list being boxed is
        # modified. Suppose the glue has natural width u, stretchability y, and
        # shrinkability z, where y is a jth order infinity and z is a kth order
        # infinity.
        for g in self.glues:
            if glue_ratio == 0.0:
                g.set(g.natural_dimen)
                continue
            elif stretching:
                # [Each] glue takes the new width u + ry if j=i;
                # it keeps its natural width u if j != i.
                f = g.stretch
            else:
                # [Each] glue takes the new width u-rz if k = i; it
                # keeps its natural width u if k != i.
                f = -g.shrink
            # Notice that stretching or shrinnking occurs only when the glue
            # has the highest order of infinity that doesn't cancel out.
            g.set(int(round(g.natural_width + glue_ratio * f)))


class VBox(AbstractBox):

    @property
    def natural_width(self):
        return max(self.natural_widths)

    @property
    def natural_height(self):
        return sum(self.natural_heights)

    @property
    def width(self):
        return max(self.widths)

    @property
    def height(self):
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

    natural_width = width = natural_height = height = 0


class Glue(ListElement):
    discardable = True

    def __init__(self, dimen, stretch=0, shrink=0):
        if isinstance(dimen, float):
            import pdb; pdb.set_trace()
        self.natural_dimen = dimen
        self.stretch = stretch
        self.shrink = shrink
        self.set_dimen = None

    @property
    def natural_width(self):
        return self.natural_dimen
    natural_height = natural_width

    def set(self, dimen):
        if self.set_dimen is not None:
            raise SettingSetGlue
        self.set_dimen = dimen

    @property
    def dimen(self):
        if self.set_dimen is None:
            raise GlueNotSet
        return self.set_dimen
    height = width = dimen


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
    def width(self):
        return self.font.width(self.code)
    natural_width = width

    @property
    def height(self):
        return self.font.height(self.code)
    natural_height = height


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

    natural_width = width = natural_height = height = 0


class FontSelection(ListElement):
    discardable = False

    def __init__(self, font_nr):
        self.font_nr = font_nr

    natural_width = width = natural_height = height = 0
