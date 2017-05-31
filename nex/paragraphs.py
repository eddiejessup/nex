from collections import namedtuple

from . import box


HListRoute = namedtuple('HListRoute', ('sequence', 'demerit'))


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
    if (isinstance(item, box.Glue)
            # Check a previous item exists, and it is not discardable.
            and ((i - 1) >= 0) and (not h_list[i - 1].discardable)):
                return True
    # b) at a kern, provided that this kern is immediately followed by
    # glue, and that it is not part of a math formula.
    # TODO: Add math conditions.
    elif (isinstance(item, box.Kern)
            # Check a following item exists, and it is glue.
            and ((i + 1) <= (len(h_list) - 1))
            and isinstance(h_list[i + 1], box.Glue)):
                return True
    # c) at a math-off that is immediately followed by glue.
    elif (isinstance(item, box.MathOff)
            # Check a following item exists, and it is glue.
            and ((i + 1) <= (len(h_list) - 1))
            and isinstance(h_list[i + 1], box.Glue)):
                return True
    # d) at a penalty (which might have been inserted automatically in a
    # formula).
    elif isinstance(item, box.Penalty):
        return True
    # e) at a discretionary break.
    elif isinstance(item, box.DiscretionaryBreak):
        return True
    else:
        return False


def break_at(h_list, i):
    break_item = h_list[i]
    # If the break item is glue, it is not included in the got h_list;
    # otherwise, it is. This is why the break item is returned separately.
    if isinstance(break_item, box.Glue):
        h_list_got = h_list[: i]
    else:
        h_list_got = h_list[: i+1]
    # If the break item is the last item in the list, no h_list after.
    if i == len(h_list) - 1:
        h_list_after = []
    # Otherwise, discard tokens until seeing something.
    else:
        for j in range(i + 1, len(h_list)):
            item_after = h_list[j]
            # Discard items until we see something not discardable, or a break-
            # point.
            if (not item_after.discardable) or is_break_point(h_list, j):
                break
        h_list_after = h_list[j:]
    return h_list_got, h_list_after, break_item


def get_best_route(h_list, demerit_func):
    if not h_list:
        return HListRoute(sequence=[], demerit=0)

    child_routes = []
    for i in range(len(h_list)):
        if is_break_point(h_list, i):
            h_list_got, h_list_after, break_item = break_at(h_list, i)
            got_demerit = demerit_func(h_list_got, break_item)
            if got_demerit is not None:
                best_current_child_route = get_best_route(h_list_after,
                                                          demerit_func)
                if best_current_child_route is not None:
                    rt = HListRoute(sequence=[h_list_got] + best_current_child_route.sequence,
                                    demerit=got_demerit + best_current_child_route.demerit)
                    child_routes.append(rt)

    # One option is not to break at all.
    no_break_demerit = demerit_func(h_list, break_item=None)
    if no_break_demerit is not None:
        child_routes.append(HListRoute(sequence=[h_list],
                                       demerit=no_break_demerit))

    if child_routes:
        return min(child_routes, key=lambda t: t.demerit)
    else:
        return None


def get_demerit(h_list, h_size, tolerance, line_penalty, break_item):
    h_box = box.HBox(h_list, to=h_size, set_glue=False)
    if h_box.considerable_as_line(tolerance, break_item):
        return h_box.demerit(break_item, line_penalty)
    else:
        return None


def get_best_h_lists(h_list, h_size, tolerance, line_penalty):
    def demerit(h_list, break_item):
        return get_demerit(h_list, h_size, tolerance, line_penalty, break_item)
    best_route = get_best_route(h_list,
                                demerit_func=demerit)
    return best_route.sequence
