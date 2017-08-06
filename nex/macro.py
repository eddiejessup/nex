from .constants.instructions import Instructions
from .tokens import InstructionToken
from .utils import LogicError, UserError


def parse_parameter_text(tokens):
    """
    From the raw parameter text of a macro, extract the parameters, their types
    (delimited or un-delimited), and the delimiting tokens.
    """
    param_nr = 1
    i = 0
    parameters = []
    while i < len(tokens):
        t = tokens[i]

        # We should only see a non-parameter here if there is text
        # preceding the parameters proper. Other non-parameter tokens should be
        # gobbled up down below.
        # "Tokens that precede the first parameter token in the parameter
        # text of a definition are required to follow the control sequence; in
        # effect, they become part of the control sequence name."
        if t.instruction != Instructions.parameter:
            if param_nr != 1:
                raise LogicError(f'Found non-parameter token where only '
                                 f'parameter tokens are expected: {t}')
            parameters.append(t)
            i += 1
            continue

        # Go forward to get the parameter number,
        # and check it is numbered correctly.
        i += 1
        t_next = tokens[i]
        labelled_param_char = t_next.value['char']
        try:
            labelled_param_nr = int(labelled_param_char)
        except ValueError:
            raise UserError(f'Got parameter number {param_nr}, but it is '
                            f'labelled as non-integer "{labelled_param_char}"')
        else:
            if labelled_param_nr != param_nr:
                raise UserError(f'Got parameter number {param_nr}, but it is '
                                f'labelled as parameter number '
                                f'{labelled_param_nr}')

        # "How does TeX determine where an argument stops, you ask. Answer:
        # There are two cases.
        # An undelimited parameter is followed immediately in the parameter
        # text by a parameter token, or it occurs at the very end of the
        # parameter text; [...]
        # A delimited parameter is followed in the parameter text by
        # one or more non-parameter tokens [...]"
        delim_tokens = []
        # Go forward to inspect following token.
        i += 1
        if i < len(tokens):
            # If there are more tokens, go forward in the token list collecting
            # delimiter tokens.
            while i < len(tokens):
                d_t = tokens[i]
                if d_t.instruction == Instructions.parameter:
                    break
                else:
                    delim_tokens.append(d_t)
                i += 1
        instruction = (Instructions.delimited_param if delim_tokens
                       else Instructions.undelimited_param)
        param = InstructionToken(
            instruction,
            value={'param_nr': param_nr, 'delim_tokens': delim_tokens},
            # Parents are parameter character, parameter number, and delimiter
            # tokens.
            parents=[t, t_next] + delim_tokens,
        )
        param_nr += 1
        parameters.append(param)
    return parameters


def parse_replacement_text(tokens):
    """
    From the raw replacement text of a macro, extract the use of parameter
    arguments and translate them into parameter call tokens.
    """
    i = 0
    tokens_processed = []
    while i < len(tokens):
        t = tokens[i]
        # If token represents a potential parameter call.
        if t.instruction == Instructions.parameter:
            # [...] each "#" must be followed by a digit that appeared after
            # "#" in the parameter text, or else the "#" should be followed by
            # another "#".
            # Inspect the next token to see which of the two cases applies.
            i += 1
            t_next = tokens[i]
            if t_next.instruction == Instructions.parameter:
                # TODO: I don't know if the cat-code of this should be changed.
                # Look in TeX: The Program to see what it does.
                t_processed = t_next
            else:
                param_nr_char = t_next.value['char']
                try:
                    param_nr = int(param_nr_char)
                except ValueError:
                    raise UserError(f'Parameter indicator followed by '
                                    f'non-integer "{param_nr_char}"')
                t_processed = InstructionToken(
                    Instructions.param_number,
                    value=param_nr,
                    parents=[t, t_next],
                )
        else:
            t_processed = t
        tokens_processed.append(t_processed)
        i += 1
    return tokens_processed


def substitute_params_with_args(replace_text, arguments):
    """
    Combine a macro's parsed replacement text with the arguments of a call to
    it, to produce a finished text after substituting the parameters with the
    arguments.
    """
    finished_text = []
    for i, t in enumerate(replace_text):
        if t.instruction == Instructions.param_number:
            param_nr = t.value
            argument_i = param_nr - 1
            argument_tokens = arguments[argument_i]
            finished_text.extend(argument_tokens)
        else:
            finished_text.append(t)
    return finished_text
