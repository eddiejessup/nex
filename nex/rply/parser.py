from .errors import ParsingError


class Token(object):
    """
    Represents a syntactically relevant piece of text.

    :param type_: A string describing the kind of text represented.
    :param value: The actual text represented.
    """
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return "Token(%r, %r)" % (self.type, self.value)


class LRParser(object):
    def __init__(self, lr_table, error_handler):
        self.lr_table = lr_table
        self.error_handler = error_handler

    def parse(self, tokenizer, state=None):
        lookahead = None
        lookaheadstack = []

        statestack = [0]
        symstack = [Token("$end", "$end")]

        current_state = 0
        while True:
            if self.lr_table.default_reductions[current_state]:
                t = self.lr_table.default_reductions[current_state]
                current_state = self._reduce_production(
                    t, symstack, statestack, state
                )
                continue

            if lookahead is None:
                if lookaheadstack:
                    lookahead = lookaheadstack.pop()
                else:
                    try:
                        # Get the next token.
                        lookahead = next(tokenizer)
                    except StopIteration:
                        lookahead = None

                if lookahead is None:
                    # Check if the only possible action from here is to end.
                    could_only_end = len(self.lr_table.lr_action[current_state]) == 1
                    lookahead = Token("$end", "$end")

            # Check if the next token is a valid next step, given our current
            # state.
            if lookahead.type in self.lr_table.lr_action[current_state]:
                # Get the next action.
                t = self.lr_table.lr_action[current_state][lookahead.type]
                # Shift.
                if t > 0:
                    statestack.append(t)
                    current_state = t
                    symstack.append(lookahead)
                    lookahead = None
                    continue
                # Reduce.
                elif t < 0:
                    current_state = self._reduce_production(
                        t, symstack, statestack, state
                    )
                    continue
                # t == 0 means (maybe among other things), we got the 'end'
                # token. We are done, so we should return the token we made.
                else:
                    # This is the output token.
                    n = symstack[-1]
                    # Annotate the output token with whether or not the only
                    # next step when we got to the end, was in fact to end.
                    n._could_only_end = could_only_end
                    return n
            else:
                self.sym_stack = symstack
                self.state_stack = statestack
                self.look_ahead = lookahead
                self.look_ahead_stack = lookaheadstack
                # TODO: actual error handling here
                if self.error_handler is not None:
                    if state is None:
                        self.error_handler(lookahead)
                    else:
                        self.error_handler(state, lookahead)
                    raise AssertionError("For now, error_handler must raise.")
                else:
                    raise ParsingError(None, lookahead.getsourcepos())

    def _reduce_production(self, t, symstack, statestack, state):
        # reduce a symbol on the stack and emit a production
        p = self.lr_table.grammar.productions[-t]
        pname = p.name
        plen = len(p)
        start = len(symstack) + (-plen - 1)
        assert start >= 0
        targ = symstack[start + 1:]
        start = len(symstack) + (-plen)
        assert start >= 0
        del symstack[start:]
        del statestack[start:]
        if state is None:
            value = p.func(targ)
        else:
            value = p.func(state, targ)
        symstack.append(value)
        current_state = self.lr_table.lr_goto[statestack[-1]][pname]
        statestack.append(current_state)
        return current_state
