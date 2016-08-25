def increasing_window(a):
    for i_max in range(len(a) + 1):
        yield a[:i_max]
