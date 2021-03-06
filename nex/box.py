import math
from enum import Enum
from functools import lru_cache

from .feedback import printable_ascii_codes, drep, truncate_list, dimrep
from .utils import InfiniteDimension, sum_infinities, LogicError


class LineState(Enum):
    naturally_good = 1
    should_stretch = 2
    should_shrink = 3


class GlueRatio(Enum):
    no_stretchability = 2
    no_shrinkability = 3


class BreakPoint(Enum):
    """The types of places where line or page breaks may happen.
    Used to decide how to assign penalties to breaks.
    """
    glue = 1
    kern = 2
    math_off = 3
    penalty = 4
    discretionary_break = 5
    not_a_break_point = 6


def extract_dimen(d):
    if isinstance(d, int):
        order = 0
        factor = d
    elif isinstance(d, InfiniteDimension):
        order = d.nr_fils
        factor = d.factor
    else:
        raise LogicError(f"Unknown dimen type: '{d}'")
    return order, factor


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

    # "If x < w, TeX attempts to stretch the contents of the box; the
    # glue order is the highest subscript i such that y_i is nonzero, and
    # the glue ratio is r = (w - x) / y_i. (If y_0 = y_1 = y_2 = y_3 = 0,
    # there's no stretchability; both i and r are set to zero.)"
    elif line_state == LineState.should_stretch:
        stretch = stretch
        stretch = [d for d in stretch if d > 0]
        if not stretch:
            glue_order = 0
            # I actually don't obey the rules in this case, because it results
            # in a weird situation where lines with no stretchability, such as
            # single words, are assigned zero badness.
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
        if not shrink:
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


def get_penalty(pre_break_conts, break_item):
    # Will assume if breaking at end of paragraph, so no break item, penalty is
    # zero. Not actually sure this is a real case, because \hfil is always
    # inserted right?
    if break_item is None:
        return 0
    # "Each potential breakpoint has an associated 'penalty,' which
    # represents the 'aesthetic cost' of breaking at that place."
    # "In cases (a), (b), (c), the penalty is zero".
    if isinstance(break_item, (Glue, Kern, MathOff)):
        return 0
    # "In case (d) an explicit penalty has been specified"
    elif isinstance(break_item, Penalty):
        return break_item.size
    # "In case (e) the penalty is the current value of \hyphenpenalty if
    # the pre-break text is nonempty, or the current value of
    # \exhyphenpenalty if the pre-break text is empty."
    elif isinstance(break_item, DiscretionaryBreak):
        raise NotImplementedError
    else:
        raise ValueError(f"Item is not a break-point: {break_item}")


def is_break_point(h_list, i):
    """These rules apply to both horizontal and vertical lists, but cases
    (d) and (e) should never happen.
    """
    item = h_list[i]
    # a) at glue, provided that this glue is immediately preceded by a non-
    #    discardable item, and that it is not part of a math formula (i.e.,
    #    not between math-on and math-off).
    #    A break 'at glue' occurs at the left edge of the glue space.
    # TODO: Add math conditions.
    if (isinstance(item, Glue)
            # Check a previous item exists, and it is not discardable.
            and ((i - 1) >= 0) and (not h_list[i - 1].discardable)):
                return True
    # b) at a kern, provided that this kern is immediately followed by
    # glue, and that it is not part of a math formula.
    # TODO: Add math conditions.
    elif (isinstance(item, Kern)
            # Check a following item exists, and it is glue.
            and ((i + 1) <= (len(h_list) - 1))
            and isinstance(h_list[i + 1], Glue)):
                return True
    # c) at a math-off that is immediately followed by glue.
    elif (isinstance(item, MathOff)
            # Check a following item exists, and it is glue.
            and ((i + 1) <= (len(h_list) - 1))
            and isinstance(h_list[i + 1], Glue)):
                return True
    # d) at a penalty (which might have been inserted automatically in a
    # formula).
    elif isinstance(item, Penalty):
        return True
    # e) at a discretionary break.
    elif isinstance(item, DiscretionaryBreak):
        return True
    else:
        return False


class ListElement:

    def __repr__(self):
        return f'{self.__class__.__name__}({self.__dict__.__repr__()})'


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
        a = []
        a.append(f'naturally {dimrep(self.natural_length)}')
        a.append(f'minimally {dimrep(self.min_length)}')
        if self.to is not None:
            a.append(f'to {dimrep(self.to)}')
        elif self.spread is not None:
            a.append(f'spread {dimrep(self.to)}')
        a.append(contsrep(self.contents))
        cls_name = self.__class__.__name__
        if self.set_glue:
            cls_name = f'|{cls_name}|'
        return drep(cls_name, a)

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
    def natural_length(self):
        # The natural width, x, of the box contents is determined by adding up
        # the widths of the boxes and kerns inside, together with the natural
        # widths of all the glue inside.
        # I'm assuming this also applies to VBoxes, but adding heights instead
        # of widths. Might not be true, considering depths exist.
        w = 0
        for item in self.contents:
            if isinstance(item, Glue):
                w += item.natural_length
            elif isinstance(item, Kern):
                w += item.length
            else:
                w += self.get_length(item)
        return w

    @property
    def min_length(self):
        """
        Non-Knuthian concept, used to decide if a box is over-full: the length
        even if all glue is maximally shrunk.
        """
        w = 0
        for item in self.contents:
            if isinstance(item, Glue):
                w += item.min_length
            elif isinstance(item, Kern):
                w += item.length
            else:
                w += self.get_length(item)
        return w

    @property
    def is_over_full(self):
        return self.min_length > self.desired_length

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
        # I undo the disobeyance I did in the glue set ratio logic, to align
        # with the TeXbook from now on.
        if glue_ratio in (GlueRatio.no_shrinkability,
                          GlueRatio.no_stretchability):
            glue_ratio = 0.0

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
                # [Each] glue takes the new length u + ry if j=i;
                # it keeps its natural length u if j != i.
                if glue_order == glue_set_order:
                    glue_diff = glue_ratio * glue_factor
                else:
                    glue_diff = 0
            elif line_state == LineState.should_shrink:
                glue_order, glue_factor = extract_dimen(g.shrink)
                # [Each] glue takes the new length u-rz if k = i; it
                # keeps its natural length u if k != i.
                if glue_order == glue_set_order:
                    glue_diff = -glue_ratio * glue_factor
                else:
                    glue_diff = 0
            else:
                raise ValueError(f'Unknown line state: {line_state}')
            # Notice that stretching or shrinking occurs only when the glue
            # has the highest order of infinity that doesn't cancel out.
            self.contents[i].set(round(g.natural_length + glue_diff))
        self.set_glue = True

    def badness(self):
        """
        Compute how bad this box would look if placed on a line. This is
        high if the line is much shorter or longer than the page width.
        """
        # Page 97 of TeXbook.
        # "The badness of a line is an integer that is approximately 100 times
        # the cube of the ratio by which the glue inside the line must stretch
        # or shrink to make an hbox of the required size. For example, if the
        # line has a total shrinkability of 10 points, and if the glue is being
        # compressed by a total of 9 points, the badness is computed to be 73
        # (since 100 * (9/10)^3 = 72.9); similarly, a line that stretches by
        # twice its total stretchability has a badness of 800. But if the
        # badness obtained by this method turns out to be more than 10000, the
        # value 10000 is used. (See the discussion of glue set ratio and glue
        # set order in Chapter 12; if i != 0, there is infinite stretchability
        # or shrinkability, so the badness is zero, otherwise the badness is
        # approximately min(100r^3, 10000).) Overfull boxes are considered to
        # be infinitely bad; they are avoided whenever possible."
        # Page 111 of TeXbook.
        # "Vertical badness is computed by the same rules as horizontal
        # badness; it is an integer between 0 and 10000, inclusive, except when
        # the box is overfull, when it is infinity."
        if self.is_over_full:
            return math.inf
        line_state, glue_ratio, glue_order = self.glue_set_ratio()
        if glue_order > 0:
            return 0
        # I can't find this stated anywhere, but it seems intuitively correct:
        # a single word on a line has no flexibility, but it is probably bad.
        elif glue_ratio in (GlueRatio.no_stretchability,
                            GlueRatio.no_shrinkability):
            return 10000
        else:
            return min(round(100 * glue_ratio ** 3), 10000)


class HBox(AbstractBox):

    def get_length(self, item):
        if isinstance(item, (Glue, Kern)):
            return item.length
        else:
            return item.width

    @property
    def widths(self):
        return [self.get_length(e) for e in self.contents]

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

    def demerit(self, break_item, line_penalty):
        ten_k = 10000
        el = line_penalty
        b = self.badness()
        p = get_penalty(self.contents, break_item)
        d = (el + b)**2
        if 0 <= p < ten_k:
            d += p**2
        elif -ten_k < p < 0:
            d -= p**2
        elif p <= -ten_k:
            pass
        else:
            raise LogicError('Undefined condition state when computing '
                             'demerit')
        return d

    def considerable_as_line(self, tolerance, break_item):
        return (get_penalty(self.contents, break_item) < 10000
                and (self.badness() <= tolerance))


class VBox(AbstractBox):

    def get_length(self, item):
        if isinstance(item, (Glue, Kern)):
            return item.length
        else:
            return item.height

    @property
    def widths(self):
        return [0 if isinstance(e, (Glue, Kern)) else e.width
                for e in self.contents]

    @property
    def heights(self):
        return [self.get_length(e) for e in self.contents]

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

    # TODO: This is wrong. Correct rules are in TeXbook page 80.
    @property
    def depth(self):
        if self.contents:
            # This is an approximation of the rules, not an attempt at
            # correctness.
            if not isinstance(self.contents[-1], AbstractBox):
                return 0
            else:
                return self.contents[-1].depth
        else:
            return 0

    def page_break_cost_and_penalty(self, break_item, insert_penalties):
        # Page 111 of TeXbook.
        ten_k = 10000
        b = self.badness()
        p = get_penalty(self.contents, break_item)
        q = insert_penalties
        if b < math.inf and p <= -ten_k and q < ten_k:
            c = p
        elif b < ten_k and -ten_k < p < ten_k and q < ten_k:
            c = b + p + q
        elif b >= ten_k and -ten_k < p < ten_k and q < ten_k:
            # Not ten_k, I checked!
            hundred_k = 100000
            c = hundred_k
        elif (b == math.inf or q >= ten_k) and p < ten_k:
            c = math.inf
        else:
            raise LogicError('TeX implies we should not get here')
        return c, p


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
            return f'|G|({dimrep(self.set_dimen)})'

    @property
    def is_set(self):
        return self.set_dimen is not None

    @property
    def min_length(self):
        if isinstance(self.shrink, InfiniteDimension):
            return 0
        else:
            return self.natural_length - self.shrink

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
        return f'K({dimrep(self.length)})'


class Leaders(ListElement):
    discardable = True
    pass


class Penalty(ListElement):
    discardable = True

    def __init__(self, size):
        self.size = size

    def __repr__(self):
        return f'P({self.size})'

    width = height = depth = 0


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
