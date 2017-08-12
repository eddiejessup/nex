import numpy as np


def get_new_grid_row(x_max):
    return [' ' for i in range(x_max)]


def pad_and_join(s, p, vs):
    return f'{s}{p}' + f'{p}{s}{p}'.join(vs) + f'{p}{s}'


class DAGLog:
    GRID_NODE_SYMBOL = '•'

    GRID_COL_SEP_CHAR = ''
    GRID_COL_SEP_PAD = ''
    GRID_ROW_SEP_CHAR = ''
    GRID_NAME_SEP_STR = '    '
    # GRID_COL_SEP_CHAR = '|'
    # GRID_COL_SEP_PAD = ' '
    # GRID_ROW_SEP_CHAR = '-'
    # GRID_NAME_SEP_STR = '    '

    def __init__(self, x_max, y_max):
        self.grid = np.empty([x_max, y_max], dtype=str)
        self.grid[...] = ' '
        self.names = ['' for _ in range(y_max)]

    def to_str(self):
        row_strs = []
        cc = self.GRID_COL_SEP_CHAR
        for grid_row, name in zip(self.grid, self.names):
            grid_str = pad_and_join(s=cc, p=self.GRID_COL_SEP_PAD, vs=grid_row)
            row_str = self.GRID_NAME_SEP_STR.join([grid_str, name])
            row_strs.append(row_str)
        if self.GRID_ROW_SEP_CHAR:
            sr = (self.GRID_ROW_SEP_CHAR * len(grid_str))
            dat_str = pad_and_join(s=sr, p='\n', vs=row_strs)
        else:
            dat_str = '\n'.join(row_strs)
        return dat_str

    def write(self, childs):
        parents = get_parents(childs)
        self._write(x=0, y=0, name='Target', childs=childs,
                    parents=parents, to_do={})

    def _write(self, x, y, name, childs, parents, to_do):
        # Set this node's symbol,
        self.grid[y, x] = self.GRID_NODE_SYMBOL
        # and description.
        self.names[y] = name
        first = True
        xfrom, yfrom = x, y
        if childs is not None:
            for child_name, child_childs in childs.items():

                child_parents = parents[child_name]
                if child_parents is None:
                    print('Ignoring node with parent')
                elif len(child_parents) == 1:
                    pass
                elif len(child_parents) == 0:
                    raise ValueError('Child node apparently has no parents')
                else:
                    i_this_parent = child_parents.index(name)
                    # If this is not the last parent node.
                    if i_this_parent < len(child_parents) - 1:
                        # Add a task to connect this parent node to the child,
                        # when the child gets drawn.
                        to_do.setdefault(child_name, []).append((x, y))
                        # And delay drawing the child until then.
                        continue
                    # If this is the last parent node.
                    else:
                        for xtask, ytask in to_do.pop(child_name):
                            print(xtask, ytask)

                # Start at current column (x), but after that, move right each
                # time.
                if first:
                    y += 1

                    self.grid[y, x] = '┃'

                    y += 1
                    first = False
                else:
                    y += 1
                    x += 1

                    for xcur in range(xfrom + 1, x + 1):
                        cexist = self.grid[yfrom, xcur]
                        turning = xcur == x
                        if turning:
                            c = '┓'
                        else:
                            if cexist == '┓':
                                c = '┳'
                            else:
                                c = '━'
                        self.grid[yfrom, xcur] = c

                    for ycur in range(yfrom + 1, y):
                        self.grid[ycur, x] = '┃'

                x, y = self._write(x, y, child_name, child_childs,
                                   parents=parents, to_do=to_do)
        return x, y


v = {
    'a': {
        'b': {'m': None},
        'c': {'m': None},
    },
    'd': None,
    'e': {
        'f': None,
        'g': None,
    },
}
# v = {
#     'a': {
#         'b': None,
#         'c': None,
#     },
#     'd': None,
#     'e': {
#         'f': None,
#         'g': None,
#     },
# }


def walk_dict(d):
    for k, v in d.items():
        if v is None:
            continue
        try:
            childs = v.keys()
        except AttributeError:
            raise ValueError(f"Could not get keys of item value: '{v}'")
        for child in childs:
            yield k, child
        yield from walk_dict(v)


def get_parents(v):
    # Add the top-level nodes with target as their parent.
    ps = {k: None for k in v}
    for pname, cname in walk_dict(v):
        ps.setdefault(cname, []).append(pname)
    return ps


x_max = 20
y_max = 20


log = DAGLog(x_max=x_max, y_max=y_max)
log.write(childs=v)
print(log.to_str())
