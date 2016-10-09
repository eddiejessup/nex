from .box import HBox, UnSetGlue


def grab_word(h_list):
    chars = []
    # Loop making a word.
    while True:
        chars.append(h_list.popleft())
        if isinstance(chars[-1], UnSetGlue):
            break_glue = chars.pop()
            break
    return chars, break_glue


def h_list_to_h_box_tree(h_list, w):
    tree = {}
    h_box = HBox(contents=[], to=w, set_glue=False)
    conts = h_box.contents
    while h_list:
        chars, break_glue = grab_word(h_list)
        conts.extend(chars)
        if h_box.badness() < 1000:
            key = (tuple(h_box.contents[:]), len(conts), h_box.badness())
            tree[key] = h_list_to_h_box_tree(h_list.copy(), w)
        # If we are not breaking, put the break glue on the list.
        conts.append(break_glue)
    key = (tuple(h_box.contents[:]), len(conts), h_box.badness())
    tree[key] = None
    return tree


def pp(tree, l=1):
    # print(l)
    for k, v in tree.items():
        tabs = ''.join('\t' for _ in range(l))
        print(tabs, ' ', k[0][-10:])
        if v is None:
            print(tabs, '\t', 'end')
        else:
            pp(v, l=l+1)


def get_best_route(node, tree, w):
    route_options = []
    for child_node, child_tree in tree.items():
        if child_tree is None:
            child_best_route = [child_node]
        else:
            child_best_route = get_best_route(child_node, child_tree, w)
        route_options.append(child_best_route)
    best_route = min(route_options, key=lambda x: x[0][2])
    # Have the best option, now need to add the sub-route's badness
    # to this node,
    node = list(node)
    node[2] += best_route[0][2]
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
    h_box_tree = h_list_to_h_box_tree(h_list, h_size)
    root_node = [None, None, 0]
    best_route = get_best_route(root_node, h_box_tree, h_size)
    # Ignore root node.
    contents = best_route[1:]
    h_boxes = [HBox(contents=c[0], to=h_size, set_glue=True)
               for c in contents]
    return h_boxes
