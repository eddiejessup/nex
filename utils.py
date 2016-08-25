def increasing_window(a):
    for i_max in range(len(a) + 1):
        yield a[:i_max]


def post_mortem(lex_wrapper):
    ban = lex_wrapper.b
    exp = lex_wrapper.e
    lex = lex_wrapper.lex
    tl = ban._secret_terminal_list
    rtl = tl[-100:]
    for t in rtl:
        print(t)
    import pdb; pdb.set_trace()
