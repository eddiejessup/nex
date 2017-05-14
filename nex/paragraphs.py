from collections import namedtuple

from .box import HBox, UnSetGlue
from .feedback import truncate_list


def grab_word(h_list):
    chars = []
    # Loop making a word.
    while True:
        chars.append(h_list.popleft())
        if isinstance(chars[-1], UnSetGlue):
            break_glue = chars.pop()
            break
    return chars, break_glue


Node = namedtuple('Node', ('contents', 'badness', 'children'))
NodeRoute = namedtuple('NodeRoute', ('sequence', 'badness'))


def h_list_to_box_tree(remaining, w):
    tree = []
    seen_box = HBox(contents=[], to=w, set_glue=False)
    seen_conts = seen_box.contents
    while remaining:
        grab_chars, grab_break_glue = grab_word(remaining)
        seen_conts.extend(grab_chars)
        seen_badness = seen_box.badness()
        if seen_badness < 1000:
            children = h_list_to_box_tree(remaining.copy(), w)
            tree.append(Node(contents=seen_conts[:], badness=seen_badness,
                             children=children))
        # If we are not breaking, put the break glue on the list.
        seen_conts.append(grab_break_glue)
    # Add possibility to never break this h-list.
    tree.append(Node(contents=seen_conts[:], badness=seen_box.badness(),
                     children=None))
    return tree


def pp(tree, l=1):
    tabs = '\t' * l
    if tree is None:
        print(f'B: ----- ', tabs, 'end')
        return
    for node in tree:
        cnt = truncate_list(node.contents, 5)
        print(f'B: {node.badness} ', tabs, cnt)
        pp(node.children, l=l+1)


def get_best_route(node):
    if node.children is None:
        return NodeRoute(sequence=[node],
                         badness=node.badness)
    child_routes = []
    for child_node in node.children:
        best_current_child_route = get_best_route(child_node)
        child_routes.append(best_current_child_route)
    best_child_route = min(child_routes, key=lambda t: t.badness)
    return NodeRoute(sequence=[node] + best_child_route.sequence,
                     badness=node.badness + best_child_route.badness)


# def get_all_routes(node, tree):
#     routes = []
#     for child_node, child_tree in tree.items():
#         if child_tree is None:
#             routes.append([child_node])
#         else:
#             routes.extend(get_all_routes(child_node, child_tree))
#     routes = [[node] + r for r in routes]
#     return routes


def h_list_to_best_h_boxes(h_list, h_size):
    box_tree = h_list_to_box_tree(h_list, h_size)
    root_node = Node(contents=None, badness=0, children=box_tree)
    best_route = get_best_route(root_node)
    # Ignore root node.
    best_sequence = best_route.sequence[1:]
    h_boxes = [HBox(contents=node.contents, to=h_size, set_glue=True)
               for node in best_sequence]
    return h_boxes
