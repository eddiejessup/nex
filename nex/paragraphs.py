from collections import namedtuple

from . import box


HListRoute = namedtuple('HListRoute', ('sequence', 'demerit'))


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
            if (not item_after.discardable) or box.is_break_point(h_list, j):
                break
        h_list_after = h_list[j:]
    return h_list_got, h_list_after, break_item


def get_best_route(h_list, h_size, tolerance, line_penalty):
    if not h_list:
        return HListRoute(sequence=[], demerit=0)

    child_routes = []
    for i in range(len(h_list)):
        if box.is_break_point(h_list, i):
            h_list_got, h_list_after, break_item = break_at(h_list, i)
            h_box = box.HBox(h_list, to=h_size, set_glue=False)
            if h_box.considerable_as_line(tolerance, break_item):
                got_demerit = h_box.demerit(break_item, line_penalty)
                best_current_child_route = get_best_route(h_list_after,
                                                          h_size, tolerance, line_penalty)
                if best_current_child_route is not None:
                    rt = HListRoute(sequence=[h_list_got] + best_current_child_route.sequence,
                                    demerit=got_demerit + best_current_child_route.demerit)
                    child_routes.append(rt)

    # One option is not to break at all.
    no_break_h_box = box.HBox(h_list, to=h_size, set_glue=False)
    no_break_demerit = no_break_h_box.demerit(break_item=None,
                                              line_penalty=line_penalty)
    child_routes.append(HListRoute(sequence=[h_list],
                                   demerit=no_break_demerit))

    if child_routes:
        return min(child_routes, key=lambda t: t.demerit)
    else:
        return None


def get_best_h_lists(h_list, h_size, tolerance, line_penalty):
    best_route = get_best_route(h_list, h_size, tolerance, line_penalty)
    if best_route is None:
        raise Exception('Could not break lines')
    else:
        return best_route.sequence
