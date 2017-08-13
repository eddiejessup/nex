import numpy as np


# A few handy functions for navigating nested dictionaries. Especially useful
# for Pythons >= 3.6, where the `.keys()` method returns an object that can't
# be indexed.

def nk(d):
    return len(d.keys())


def k(d, n):
    return list(d.keys())[n]


def v(d, n):
    return d[k(d, n)]


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
        ps_cur = ps.setdefault(cname, [])
        if pname not in ps_cur:
            ps_cur.append(pname)
    return ps


class DAGLog:
    GRID_NODE_SYMBOL = '◔'
    GRID_EMPTY_SYMBOL = ' '
    NAME_EMPTY_STRING = ''

    def __init__(self):
        self.grid = self._get_grid_chunk(x=1, y=1)
        self.names = []

    def set_grid(self, x, y, v):
        self._extend_log_right(x)
        self._extend_log_down(y)
        self.grid[y, x] = v

    def set_name(self, y, v):
        self._extend_log_down(y)
        self.names[y] = v

    def get_grid(self, x, y):
        try:
            return self.grid[y, x]
        except IndexError:
            return self.GRID_EMPTY_SYMBOL

    def write(self, childs, target_node='Target'):
        parents = get_parents(childs)
        self._write(x=0, y=0, node=target_node, childs=childs,
                    parents=parents, to_do={})

    def to_str(self, nr_pads=1):
        row_strs = []
        for grid_row, name in zip(self.grid, self.names):
            grid_str = ''.join(self._pad_row(grid_row, nr_pads=nr_pads))
            row_str = (' ' * nr_pads).join([grid_str, name])
            row_strs.append(row_str)
        dat_str = '\n'.join(row_strs)
        return dat_str

    def _get_grid_chunk(self, x, y):
        return np.full((y, x), self.GRID_EMPTY_SYMBOL, dtype=str)

    def _extend_log_down(self, y):
        extra_y_grid = y - (self.grid.shape[0] - 1)
        if extra_y_grid > 0:
            extra_grid = self._get_grid_chunk(x=self.grid.shape[1],
                                              y=extra_y_grid)
            self.grid = np.append(self.grid, extra_grid, axis=0)
        extra_y_names = y - (len(self.names) - 1)
        self.names += [self.NAME_EMPTY_STRING for _ in range(extra_y_names)]

    def _extend_log_right(self, x):
        extra_x_grid = x - (self.grid.shape[1] - 1)
        if extra_x_grid > 0:
            extra_grid = self._get_grid_chunk(x=extra_x_grid,
                                              y=self.grid.shape[0])
            self.grid = np.append(self.grid, extra_grid, axis=1)

    def _pipe_horizontally(self, x, y):
        ccur = self.get_grid(x=x, y=y)
        if ccur in ('┓', '┳'):
            c = '┳'
        elif ccur in (' ', '━'):
            c = '━'
        else:
            raise NotImplementedError(ccur)
        self.set_grid(y=y, x=x, v=c)

    def _pipe_vertically(self, x, y):
        ccur = self.get_grid(y=y, x=x)
        if ccur in (' ', '┃'):
            c = '┃'
        else:
            raise NotImplementedError(ccur)
        self.set_grid(y=y, x=x, v=c)

    def _pipe_west_with_south(self, x, y):
        ccur = self.get_grid(y=y, x=x)
        if ccur in (' ', '┓'):
            c = '┓'
        else:
            raise NotImplementedError(ccur)
        self.set_grid(y=y, x=x, v=c)

    def _pipe_north_with_east(self, x, y):
        ccur = self.get_grid(y=y, x=x)
        if ccur in (' ', '┗'):
            c = '┗'
        elif ccur in ('┻', '━'):
            c = '┻'
        else:
            raise NotImplementedError(ccur)
        self.set_grid(y=y, x=x, v=c)

    def _tunnel_horizontally(self, xs, xe, y):
        for x in range(xs + 1, xe):
            self._pipe_horizontally(x=x, y=y)

    def _tunnel_vertically(self, ys, ye, x):
        for y in range(ys + 1, ye):
            self._pipe_vertically(x=x, y=y)

    def _tunnel_east_then_south(self, xs, xe, ys, ye):
        self._tunnel_horizontally(xs=xs, xe=xe, y=ys)
        self._pipe_west_with_south(x=xe, y=ys)
        self._tunnel_vertically(ys=ys, ye=ye, x=xe)

    def _tunnel_south_then_east(self, xs, xe, ys, ye):
        self._tunnel_vertically(ys=ys, ye=ye, x=xs)
        self._pipe_north_with_east(x=xs, y=ye)
        self._tunnel_horizontally(xs=xs, xe=xe, y=ye)

    def _write(self, x, y, node, childs, parents, to_do):
        # Set this node's symbol and description.
        self.set_grid(y=y, x=x, v=self.GRID_NODE_SYMBOL)
        self.set_name(y=y, v=str(node)[:90])
        first = True
        xfrom, yfrom = x, y
        if childs is not None:
            for child_node, child_childs in childs.items():

                extra_tasks = []
                child_parents = parents[child_node]
                if child_parents is None:
                    pass
                elif len(child_parents) == 1:
                    pass
                elif len(child_parents) == 0:
                    raise ValueError('Child node apparently has no parents')
                else:
                    i_this_parent = child_parents.index(node)
                    # If this is not the last parent node.
                    if i_this_parent < len(child_parents) - 1:
                        # Add a task to connect this parent node to the child,
                        # when the child gets drawn.
                        to_do.setdefault(child_node, []).append((x, y))
                        # And delay drawing the child until then.
                        continue
                    # If this is the last parent node.
                    else:
                        extra_tasks = to_do.pop(child_node)

                # Start at current column (x), but after that, move right each
                # time.
                if first:
                    y += 1
                    self._pipe_vertically(x=x, y=y)
                    y += 1
                    first = False
                else:
                    y += 1
                    x += 1
                    self._tunnel_east_then_south(xs=xfrom, xe=x,
                                                 ys=yfrom, ye=y)

                # Connect up extra nodes to this child.
                for xtask_from, ytask_from in extra_tasks:
                    self._tunnel_south_then_east(xs=xtask_from, xe=x,
                                                 ys=ytask_from, ye=y)

                x, y = self._write(x, y, child_node, child_childs,
                                   parents=parents, to_do=to_do)
        return x, y

    def _pad_row(self, row, nr_pads):
        common_pads = (self.GRID_NODE_SYMBOL, '┳', '┻', '━')
        w_pads = common_pads + ('┗',)
        e_pads = common_pads + ('┓',)
        yield row[0]
        for w, e in zip(row[:-1], row[1:]):
            if w in w_pads and e in e_pads:
                fill_symbol = '━'
            else:
                fill_symbol = self.GRID_EMPTY_SYMBOL
            for _ in range(nr_pads):
                yield fill_symbol
            yield e


if __name__ == '__main__':

    root = {'Root': None}
    v = {
        'a': {
            'b': {'m': root},
            'c': {'m': root},
        },
        'd': root,
        'e': {
            'f': root,
            'g': root,
        },
    }

    root = {
        'root': None,
    }
    vt = {
        'a': {
           'b': root,
        },
        # 'c': root,
        'd': {
           'b': root,
        },
    }
    # macro_newins = {
    #     'macro_newinsert': {
    #         'newinsert_cw': {
    #             'newinsert_lex': buf,
    #         }
    #     }
    # }
    # vt = {
    #     'footins_def': {
    #         'chardef_instr': {
    #             'chardef_cw': macro_newins,
    #         },
    #         'footins_cw': {
    #             'footins_lex': buf,
    #         },
    #         'optional_equals': {
    #             'equals_instr': macro_newins,
    #         },
    #         'number': {
    #             'signs': None,
    #             'size': {
    #                 'count': {
    #                     'count_def_tok_instr': {
    #                         'macro_alloc_nr': {
    #                             'alloc_nr_cw': macro_newins,
    #                         }
    #                     }
    #                 }
    #             },
    #         },
    #     }
    # }

    log = DAGLog()
    log.write(childs=vt)
    print(log.to_str(2))
