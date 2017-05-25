from enum import Enum
from functools import lru_cache

from .utils import sum_infinities
from .feedback import printable_ascii_codes, drep, truncate_list, dimrep


class LineState(Enum):
    naturally_good = 1
    should_stretch = 2
    should_shrink = 3


class GlueRatio(Enum):
    no_stretchability = 2
    no_shrinkability = 3


@lru_cache(512)
def glue_set_ratio(natural_length, desired_length, stretch, shrink):
    excess_length = natural_length - desired_length
    if excess_length == 0:
        line_state = LineState.naturally_good
    elif excess_length > 0:
        line_state = LineState.should_shrink
    else:
        line_state = LineState.should_stretch

    # If x = w, all glue gets its natural length.
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
            glue_ratio = -excess_length / relevant_stretch_dimen
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
            glue_ratio = excess_length / relevant_shrink_dimen
            # However, r is set to 1.0 in the case i=0 and x - w > z_0,
            # because the maximum shrinkability must not be exceeded.
            if glue_order == 0:
                glue_ratio = min(glue_ratio, 1.0)
    return line_state, glue_ratio, glue_order


class ListElement:

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__,
                               self.__dict__.__repr__())


# All modes.


#     Boxes.


def contsrep(contents, n=9):
    """Get a nice representation of the contents of a box."""
    cs_rep = []
    for c in contents:
        if isinstance(c, Character) and c.code in printable_ascii_codes:
            c_str = chr(c.code)
            if cs_rep and isinstance(cs_rep[-1], str):
                cs_rep[-1] += c_str
            else:
                cs_rep.append(c_str)
        else:
            cs_rep.append(c)
    return truncate_list(cs_rep, n=n)


class AbstractBox(ListElement):

    discardable = False

    def __init__(self, contents, to=None, spread=None, set_glue=True,
                 offset=0):
        self.to = to
        self.spread = spread
        if to is not None and spread is not None:
            raise Exception('Cannot specify both to and spread')
        self.contents = list(contents)
        self.set_glue = set_glue
        if set_glue:
            self.scale_and_set()
        self.offset = offset

    def __repr__(self):
        a = [contsrep(self.contents)]
        if self.to is not None:
            a.append(f'to {dimrep(self.to)}')
        elif self.spread is not None:
            a.append(f'spread {dimrep(self.to)}')
        return drep(self, a)

    @property
    def un_set_glues(self):
        return [e for e in self.contents
                if isinstance(e, Glue) and not e.is_set]

    @property
    def stretch(self):
        return sum_infinities(g.stretch for g in self.un_set_glues)

    @property
    def shrink(self):
        return sum_infinities(g.shrink for g in self.un_set_glues)

    @property
    def desired_length(self):
        if self.to is not None:
            return self.to
        w = self.natural_length
        if self.spread is not None:
            w += self.spread
        return w

    def append(self, *args, **kwargs):
        self.contents.append(*args, **kwargs)

    def extend(self, *args, **kwargs):
        self.contents.extend(*args, **kwargs)

    def copy(self, *args, **kwargs):
        # If glue is set, need to tell the constructor that set_glue should be
        # True, but that the glue is already set.
        if self.set_glue:
            raise NotImplementedError('Can only copy un-set boxes at the '
                                      'moment, because that is all that is '
                                      'needed')
        return self.__class__(contents=self.contents[:],
                              to=self.to, spread=self.spread, set_glue=False)

    def glue_set_ratio(self):
        return glue_set_ratio(self.natural_length, self.desired_length,
                              tuple(self.stretch), tuple(self.shrink))

    def scale_and_set(self):
        line_state, glue_ratio, glue_set_order = self.glue_set_ratio()

        # Note I've quoted this from the TeXbook, talking about setting glue in
        # an H Box. But it later says that this all applies to V Boxes, so I've
        # changed 'width' to 'length'.

        # Every glob of glue in the list being boxed is modified. Suppose the
        # glue has natural length u, stretchability y, and shrinkability z,
        # where y is a jth order infinity and z is a kth order infinity.
        for i, item in enumerate(self.contents):
            if (not isinstance(item, Glue)) or item.is_set:
                continue
            g = item
            if line_state == LineState.naturally_good:
                glue_diff = 0
            elif line_state == LineState.should_stretch:
                glue_order, glue_factor = extract_dimen(g.stretch)
                if glue_ratio == GlueRatio.no_stretchability:
                    glue_diff = 0
                # [Each] glue takes the new length u + ry if j=i;
                # it keeps its natural length u if j != i.
                elif glue_order == glue_set_order:
                    glue_diff = glue_ratio * glue_factor
                else:
                    glue_diff = 0
            elif line_state == LineState.should_shrink:
                glue_order, glue_factor = extract_dimen(g.shrink)
                if glue_ratio == GlueRatio.no_shrinkability:
                    glue_diff = 0
                # [Each] glue takes the new length u-rz if k = i; it
                # keeps its natural length u if k != i.
                elif glue_order == glue_set_order:
                    glue_diff = -glue_ratio * glue_factor
                else:
                    glue_diff = 0
            else:
                raise ValueError(f'Unknown line state: {line_state}')
            # Notice that stretching or shrinking occurs only when the glue
            # has the highest order of infinity that doesn't cancel out.
            self.contents[i].set(int(round(g.natural_length + glue_diff)))
        self.set_glue = True


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
    def natural_length(self):
        # The natural width, x, of the box contents is determined by adding up
        # the widths of the boxes and kerns inside, together with the natural
        # widths of all the glue inside.
        w = 0
        for c in self.contents:
            if isinstance(c, Glue):
                w += c.natural_length
            elif isinstance(c, Kern):
                w += c.length
            else:
                w += c.width
        return w

    @property
    def widths(self):
        return [e.length if isinstance(e, (Glue, Kern)) else e.width
                for e in self.contents]

    @property
    def heights(self):
        return [0 if isinstance(e, (Glue, Kern)) else e.height
                for e in self.contents]

    @property
    def depths(self):
        return [0 if isinstance(e, (Glue, Kern)) else e.depth
                for e in self.contents]

    @property
    def width(self):
        if not self.set_glue:
            raise AttributeError('HBox is not set yet, does not have a width')
        return self.desired_length

    # TODO: I'm not sure the height and depth definitions are correct.
    @property
    def height(self):
        return max(self.heights, default=0)

    @property
    def depth(self):
        return max(self.depths, default=0)

    def badness(self):
        line_state, glue_ratio, glue_order = self.glue_set_ratio()
        if glue_order > 0:
            b = 0
        elif glue_ratio in (GlueRatio.no_stretchability,
                            GlueRatio.no_shrinkability):
            b = 10000
        elif glue_ratio == 1.0:
            line_state, glue_ratio, glue_set_order = self.glue_set_ratio()
            b = 10000
        else:
            b = int(round(100 * glue_ratio ** 3))
        return min(b, 10000)


class VBox(AbstractBox):

    @property
    def natural_length(self):
        w = 0
        for c in self.contents:
            if isinstance(c, Glue):
                w += c.natural_length
            else:
                w += c.height
        return w

    @property
    def widths(self):
        return [0 if isinstance(e, (Glue, Kern)) else e.width
                for e in self.contents]

    @property
    def heights(self):
        return [e.length if isinstance(e, (Glue, Kern)) else e.height
                for e in self.contents]

    @property
    def depths(self):
        return [0 if isinstance(e, (Glue, Kern)) else e.width
                for e in self.contents]

    @property
    def width(self):
        return max(self.widths)

    @property
    def height(self):
        if not self.set_glue:
            raise AttributeError('VBox is not set yet, does not have a height')
        return self.desired_length

    # TODO: This is almost certainly wrong.
    @property
    def depth(self):
        return self.contents[-1].depth


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

    width = height = depth = 0


class Glue(ListElement):
    discardable = True

    def __init__(self, dimen, stretch=0, shrink=0):
        self.natural_length = dimen
        self.stretch = stretch
        self.shrink = shrink

        self.set_dimen = None

    def __repr__(self):
        if self.set_dimen is None:
            return 'G({} +{} -{})'.format(dimrep(self.natural_length),
                                          dimrep(self.stretch),
                                          dimrep(self.shrink))
        else:
            return '|G|({})'.format(dimrep(self.set_dimen))

    @property
    def is_set(self):
        return self.set_dimen is not None

    def set_naturally(self):
        self.set_dimen = self.natural_length

    def set(self, dimen):
        self.set_dimen = dimen

    def unset(self):
        self.set_dimen = None

    @property
    def length(self):
        if self.set_dimen is not None:
            return self.set_dimen
        else:
            raise AttributeError('Glue is not set, so has no length')


class Kern(ListElement):
    discardable = True

    def __init__(self, dimen):
        self.length = dimen

    def __repr__(self):
        return 'K({})'.format(dimrep(self.length))


class Leaders(ListElement):
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

    def __init__(self, code, width, height, depth):
        self.code = code
        self.width = width
        self.height = height
        self.depth = depth

    def __repr__(self):
        if self.code in printable_ascii_codes:
            return f"'{chr(self.code)}'"
        else:
            return f"C({self.code})"


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

    width = height = depth = 0

    def __repr__(self):
        return f'FD({self.font_nr}: {self.font_name})'


class FontSelection(ListElement):
    discardable = False

    def __init__(self, font_nr):
        self.font_nr = font_nr

    def __repr__(self):
        return f'F({self.font_nr})'

    width = height = depth = 0
