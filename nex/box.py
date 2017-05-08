from enum import Enum
from functools import lru_cache

from .pydvi.TeXUnit import sp2pt

from .utils import sum_infinities


class LineState(Enum):
    naturally_good = 1
    should_stretch = 2
    should_shrink = 3


class GlueRatio(Enum):
    no_stretchability = 2
    no_shrinkability = 3


class LayoutList:
    pass


class ListElement:

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.__dict__.__repr__())


@lru_cache(512)
def glue_set_ratio(natural_width, desired_width, stretch, shrink):
    excess_width = natural_width - desired_width
    if excess_width == 0:
        line_state = LineState.naturally_good
    elif excess_width > 0:
        line_state = LineState.should_shrink
    else:
        line_state = LineState.should_stretch

    # If x = w, all glue gets its natural width.
    if line_state == LineState.naturally_good:
        glue_ratio = 0.0
        # Not stated, but assuming this value does not matter.
        glue_order = 0

    # Otherwise the glue will be modified, by computing a 'glue set ratio',
    # r and a 'glue set order', i, in the following way:

    # Let's say that there's a total of
    #     y_0 + y_1 fil + y_2 fill + y_3 filll
    # available for stretching and
    #     z_0 + z_1 fil + z_2 fill + z_3 filll
    # available for  shrinking.

    # If x < w, TeX attempts to stretch the contents of the box; the
    # glue order is the highest subscript i such that y_i is nonzero, and
    # the glue ratio is r = (w - x) / y_i. (If y_0 = y_1 = y_2 = y_3 = 0,
    # there's no stretchability; both i and r are set to zero.)
    elif line_state == LineState.should_stretch:
        stretch = stretch
        stretch = [d for d in stretch if d > 0]
        if len(stretch) == 0:
            glue_order = 0
            glue_ratio = GlueRatio.no_stretchability
        else:
            glue_order = len(stretch) - 1
            relevant_stretch_dimen = stretch[-1]
            glue_ratio = -excess_width / relevant_stretch_dimen
    # If x > w, the glue order is the highest subscript i such that z_i
    # != 0, and the glue ratio is normally r = (x - w) / z_i. (see below
    # for exception at 'However...')
    elif line_state == LineState.should_shrink:
        shrink = shrink
        shrink = [d for d in shrink if d > 0]
        # I assume that the rule when stretch_i = 0 also applies for
        # shrink_i = 0, though I can't see it stated anywhere.
        if len(shrink) == 0:
            glue_order = 0
            glue_ratio = GlueRatio.no_shrinkability
        else:
            glue_order = len(shrink) - 1
            relevant_shrink_dimen = shrink[-1]
            glue_ratio = excess_width / relevant_shrink_dimen
            # However, r is set to 1.0 in the case i=0 and x - w > z_0,
            # because the maximum shrinkability must not be exceeded.
            if glue_order == 0:
                glue_ratio = min(glue_ratio, 1.0)
    return line_state, glue_ratio, glue_order


# All modes.


#     Boxes.


class AbstractBox(ListElement):

    discardable = False

    def __init__(self, contents, to=None, spread=None, set_glue=True):
        self.to = to
        self.spread = spread
        if to is not None and spread is not None:
            raise Exception('Cannot specify both to and spread')
        self.contents = list(contents)
        self.set_glue = set_glue
        if set_glue:
            self.scale_and_set()

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self.contents)

    @property
    def widths(self):
        return [e.width for e in self.contents]

    @property
    def heights(self):
        return [e.height for e in self.contents]

    @property
    def un_set_glues(self):
        return [e for e in self.contents if isinstance(e, UnSetGlue)]


def extract_dimen(d):
    if isinstance(d, int):
        order = 0
        factor = d
    else:
        order = d.value['number_of_fils']
        factor = d.value['factor']
    return order, factor


class HBox(AbstractBox):

    @property
    def natural_width(self):
        # The natural width, x, of the box contents is determined by adding up
        # the widths of the boxes and kerns inside, together with the natural
        # widths of all the glue inside.
        return sum([e.natural_width for e in self.contents])

    @property
    def width(self):
        if not self.set_glue:
            raise Exception('HBox is not set yet, does not have a width')
        return self.desired_width

    @property
    def height(self):
        return max(self.heights)

    @property
    def stretch(self):
        return sum_infinities(g.stretch for g in self.un_set_glues)

    @property
    def shrink(self):
        return sum_infinities(g.shrink for g in self.un_set_glues)

    @property
    def desired_width(self):
        if self.to is not None:
            return self.to
        w = self.natural_width
        if self.spread is not None:
            w += self.spread
        return w

    def badness(self):
        line_state, glue_ratio, glue_order = self.glue_set_ratio()
        if glue_order > 0:
            b = 0
        elif glue_ratio in (GlueRatio.no_stretchability,
                            GlueRatio.no_shrinkability):
            b = 10000
        else:
            b = int(round(100 * glue_ratio ** 3))
            if glue_ratio == 1.0:
                b = 10000
        return min(b, 10000)

    def glue_set_ratio(self):
        return glue_set_ratio(self.natural_width, self.desired_width,
                              tuple(self.stretch), tuple(self.shrink))

    def scale_and_set(self):
        line_state, glue_ratio, glue_set_order = self.glue_set_ratio()

        # Every glob of glue in the horizontal list being boxed is
        # modified. Suppose the glue has natural width u, stretchability y, and
        # shrinkability z, where y is a jth order infinity and z is a kth order
        # infinity.
        for i, item in enumerate(self.contents):
            if not isinstance(item, UnSetGlue):
                continue
            g = item
            if line_state == LineState.naturally_good:
                glue_diff = 0
            elif line_state == LineState.should_stretch:
                glue_order, glue_factor = extract_dimen(g.stretch)
                if glue_ratio == GlueRatio.no_stretchability:
                    glue_diff = 0
                # [Each] glue takes the new width u + ry if j=i;
                # it keeps its natural width u if j != i.
                elif glue_order == glue_set_order:
                    glue_diff = glue_ratio * glue_factor
                else:
                    glue_diff = 0
            else:
                glue_order, glue_factor = extract_dimen(g.shrink)
                if glue_ratio == GlueRatio.no_shrinkability:
                    glue_diff = 0
                # [Each] glue takes the new width u-rz if k = i; it
                # keeps its natural width u if k != i.
                elif glue_order == glue_set_order:
                    glue_diff = -glue_ratio * glue_factor
                else:
                    glue_diff = 0
            # Notice that stretching or shrinking occurs only when the glue
            # has the highest order of infinity that doesn't cancel out.
            self.contents[i] = g.set(int(round(g.natural_width + glue_diff)))
        self.set_glue = True


class VBox(AbstractBox):

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


#     /Boxes.
#     Miscellanea.

class WhatsIt(ListElement):
    discardable = False

    width = height = 0


def repr_dimen(d):
    if isinstance(d, int):
        return '{:.1f}pt'.format(sp2pt(d))
    else:
        return d


class UnSetGlue(ListElement):
    discardable = True

    def __init__(self, dimen, stretch=None, shrink=None):
        self.natural_dimen = dimen
        self.stretch = stretch
        self.shrink = shrink

    def __repr__(self):
        return 'G({} +{} -{})'.format(*[repr_dimen(d)
                                        for d in (self.natural_dimen,
                                                  self.stretch,
                                                  self.shrink)])

    @property
    def natural_width(self):
        return self.natural_dimen
    natural_height = natural_width

    def set(self, dimen):
        return SetGlue(dimen)


class SetGlue(ListElement):
    discardable = True

    def __init__(self, dimen):
        self.dimen = dimen

    def __repr__(self):
        return '|G|({})'.format(repr_dimen(self.dimen))

    @property
    def width(self):
        return self.dimen
    height = width


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

    def __repr__(self):
        return self.char
        # return '{}({})'.format(self.__class__.__name__, self.char)

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

    width = height = 0


class FontSelection(ListElement):
    discardable = False

    def __init__(self, font_nr):
        self.font_nr = font_nr

    width = height = 0
