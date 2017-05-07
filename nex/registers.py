from .instructions import Instructions, register_instructions


short_hand_reg_def_token_type_to_reg_type = {
    Instructions.count_def_token.value: Instructions.count.value,
    Instructions.dimen_def_token.value: Instructions.dimen.value,
    Instructions.skip_def_token.value: Instructions.skip.value,
    Instructions.mu_skip_def_token.value: Instructions.mu_skip.value,
    Instructions.toks_def_token.value: Instructions.toks.value,
}


register_sizes = [256 for _ in range(5)]


def is_register_type(type_):
    try:
        i = Instructions(type_)
    except ValueError:
        return False
    return i in register_instructions


def get_initial_registers():
    return Registers(*register_sizes)


def get_local_registers(enclosing_scope):
    return get_initial_registers()


def check_type(type_, value):
    # TODO: Make type checking more strict, and do in more places.
    if type_ in (Instructions.count.value,
                 Instructions.dimen.value,
                 Instructions.integer_parameter.value,
                 Instructions.dimen_parameter.value):
        expected_type = int
    elif type_ in (Instructions.skip.value,
                   Instructions.mu_skip.value,
                   Instructions.glue_parameter.value,
                   Instructions.mu_glue_parameter.value):
        expected_type = dict
    elif type_ in (Instructions.toks.value,
                   Instructions.token_parameter.value):
        expected_type = list
    if not isinstance(value, expected_type):
        raise TypeError('Value has wrong type')


class Registers:

    def __init__(self, nr_counts, nr_dimens,
                 nr_skips, nr_mu_skips, nr_token_lists):
        init_register = lambda n: {i: None for i in range(n)}
        self.register_map = {
            Instructions.count.value: init_register(nr_counts),
            Instructions.dimen.value: init_register(nr_dimens),
            Instructions.skip.value: init_register(nr_skips),
            Instructions.mu_skip.value: init_register(nr_mu_skips),
            Instructions.toks.value: init_register(nr_token_lists),
        }

    def get(self, type_, i):
        register = self.register_map[type_]
        try:
            r = register[i]
        except KeyError:
            raise ValueError('No register number {} of type {}'
                             .format(i, type_))
        if r is None:
            raise ValueError('No value in register number {} of type {}'
                             .format(i, type_))
        return r

    def set(self, type_, i, value):
        check_type(type_, value)
        register = self.register_map[type_]
        if i not in register:
            raise ValueError('No register number {} of type {}'
                             .format(i, type_))
        register[i] = value
