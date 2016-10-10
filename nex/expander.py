from .common import InternalToken

undelim_macro_param_type = 'UNDELIMITED_PARAM'
delim_macro_param_type = 'DELIMITED_PARAM'
macro_param_types = (undelim_macro_param_type, delim_macro_param_type)


def parse_parameter_text(tokens):
    p_nr = 1
    i = 0
    parameters = []
    while i < len(tokens):
        t = tokens[i]

        # The only time we should see a non-parameter, is if there is text
        # preceding the parameters proper. Anything else should be
        # gobbled down below. Ooh-err.
        # "
        # Tokens that precede the first parameter token in the parameter
        # text of a definition are required to follow the control sequence; in
        # effect, they become part of the control sequence name.
        # "
        if t.type != 'PARAMETER':
            assert p_nr == 1
            parameters.append(t)
            i += 1
            continue

        # Go forward to get the parameter number,
        # and check it is numbered correctly.
        i += 1
        t_next = tokens[i]
        if int(t_next.value['char']) != p_nr:
            raise ValueError

        # "
        # How does TeX determine where an argument stops, you ask. Answer:
        # There are two cases.
        # An undelimited parameter is followed immediately in the parameter
        # text by a parameter token, or it occurs at the very end of the
        # parameter text; [...]
        # A delimited parameter is followed in the parameter text by
        # one or more non-parameter tokens [...]
        # "
        delim_tokens = []
        i += 1
        if i < len(tokens):
            # If there are more tokens, go forward in the token list collecting
            # delimiter tokens.
            while i < len(tokens):
                d_t = tokens[i]
                if d_t.type == 'PARAMETER':
                    break
                else:
                    delim_tokens.append(d_t)
                i += 1
        type_ = (delim_macro_param_type if delim_tokens
                 else undelim_macro_param_type)
        param = InternalToken(type_=type_, value={'param_nr': p_nr,
                                                  'delim_tokens': delim_tokens})
        p_nr += 1
        parameters.append(param)
    return parameters


def parse_replacement_text(tokens):
    i = 0
    tokens_processed = []
    while i < len(tokens):
        t = tokens[i]
        if t.type == 'PARAMETER':
            i += 1
            t_next = tokens[i]
            # [...] each # must be followed by a digit that appeared after # in
            # the parameter text, or else the # should be followed by another
            # #.
            if t_next.type == 'PARAMETER':
                # TODO: I don't know if the cat-code of this should be changed.
                # Look in TeX: The Program to see what it does.
                tokens_processed.append(t_next)
            else:
                p_nr = int(t_next.value['char'])
                t = InternalToken(type_='PARAM_NUMBER', value=p_nr)
        tokens_processed.append(t)
        i += 1
    return tokens_processed


def substitute_params_with_args(replace_text, arguments):
    finished_text = []
    for i, t in enumerate(replace_text):
        if t.type == 'PARAM_NUMBER':
            param_nr = t.value
            argument_i = param_nr - 1
            argument_tokens = arguments[argument_i]
            finished_text.extend(argument_tokens)
        else:
            finished_text.append(t)
    return finished_text


def expand_macro_to_token_list(macro_token, arguments):
    def_token = macro_token.value['definition']
    def_text_token = def_token.value['text']
    replace_text = def_text_token.value['replacement_text']
    finished_text = substitute_params_with_args(replace_text, arguments)
    return finished_text
