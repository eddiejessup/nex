import string


printable_ascii_codes = list(map(ord, string.printable))


def truncate_list(ts, n=9):
    """Truncate the elements of a list, keeping elements at each end, and
    replacing the omitted middle with a single character, an ellipsis ('…').
    Note that this is not '...', but the unicode character for an ellipsis
    proper. After all, we *are* making a typesetting program."""
    k = 2 * n
    lim = (k - 1) // 2
    if len(ts) > k:
        return list(ts[:lim]) + ['…'] + list(ts[-lim:])
    else:
        return ts


def strep(s):
    """Format a string for display as a line context."""
    return (s
            .replace(' ', '␣')
            .replace('\n', '⏎ ')
            .replace('\t', '⇥')
            )


def csep(args):
    """Get string representations of a sequence of items. Intended for use in
    __repr__ and such."""
    sargs = []
    for arg in args:
        if arg is None or arg == '':
            continue
        if isinstance(arg, str):
            sarg = arg
        else:
            sarg = repr(arg)
        sargs.append(sarg)
    return ', '.join(sargs)


def clsn(obj):
    """Short-hand to get class name. Intended for use in __repr__ and such."""
    return obj.__class__.__name__


def drep(obj, a):
    """Helper for formatting typical __repr__ return values."""
    return f'{clsn(obj)}({csep(a)})'
