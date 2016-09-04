def increasing_window(a):
    for i_max in range(len(a) + 1):
        yield a[:i_max]


def post_mortem(lex_wrapper, parser):
    ban = lex_wrapper.b
    lex = lex_wrapper.lex
    tl = ban._secret_terminal_list
    rtl = tl[-100:]
    # for t in rtl:
    #     print(t)
    ss = parser.sym_stack
    sts = parser.state_stack
    la = parser.look_ahead
    las = parser.look_ahead_stack
    import pdb; pdb.set_trace()
