from collections import namedtuple

from .box import HBox, UnSetGlue
from .feedback import truncate_list


HListKey = namedtuple('HListKey', ('contents', 'badness'))


def grab_word(h_list):
    chars = []
    # Loop making a word.
    while True:
        chars.append(h_list.popleft())
        if isinstance(chars[-1], UnSetGlue):
            break_glue = chars.pop()
            break
    return chars, break_glue


def h_list_to_box_tree(remaining, w):
    tree = {}
    seen_box = HBox(contents=[], to=w, set_glue=False)
    seen_conts = seen_box.contents
    while remaining:
        grab_chars, grab_break_glue = grab_word(remaining)
        seen_conts.extend(grab_chars)
        seen_badness = seen_box.badness()
        if seen_badness < 1000:
            key = HListKey(contents=tuple(seen_conts[:]),
                           badness=seen_badness)
            tree[key] = h_list_to_box_tree(remaining.copy(), w)
        # If we are not breaking, put the break glue on the list.
        seen_conts.append(grab_break_glue)
    # Add possibility to never break this h-list.
    key = HListKey(contents=tuple(seen_conts[:]), badness=seen_box.badness())
    tree[key] = None
    return tree


def pp(tree, l=1):
    tabs = '\t' * l
    if tree is None:
        print(f'B: ----- ', tabs, 'end')
        return
    for k, v in tree.items():
        cnt = truncate_list(k.contents, 5)
        print(f'B: {k.badness} ', tabs, cnt)
        pp(v, l=l+1)


def get_best_route(node, tree, w):
    route_options = []
    for child_node, child_tree in tree.items():
        if child_tree is None:
            child_best_route = [child_node]
        else:
            child_best_route = get_best_route(child_node, child_tree, w)
        route_options.append(child_best_route)
    best_route = min(route_options, key=lambda x: x[0].badness)
    # Have the best option, now need to add the sub-route's badness
    # to this node,
    node = HListKey(contents=node.contents,
                    badness=node.badness + best_route[0].badness)
    # and add it to the front of the route.
    best_route = [node] + best_route
    return best_route


def get_all_routes(node, tree, w):
    routes = []
    for child_node, child_tree in tree.items():
        if child_tree is None:
            routes.append([child_node])
        else:
            routes.extend(get_all_routes(child_node, child_tree, w))
    routes = [[node] + r for r in routes]
    return routes


def h_list_to_best_h_boxes(h_list, h_size):
    box_tree = h_list_to_box_tree(h_list, h_size)
    root_node = HListKey(contents=None, badness=0)
    best_route = get_best_route(root_node, box_tree, h_size)
    # Ignore root node.
    contents = best_route[1:]
    h_boxes = [HBox(contents=c[0], to=h_size, set_glue=True)
               for c in contents]
    return h_boxes
