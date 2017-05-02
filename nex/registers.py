from .constants.primitive_control_sequences import (Instructions,
                                                    register_instructions)


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


get_local_registers = get_initial_registers


class Registers(object):

    def __init__(self, nr_counts, nr_dimens,
                 nr_skips, nr_mu_skips, nr_token_lists):
        init_register = lambda n: {i: None for i in range(n)}
        self.register_map = {
            Instructions.count: init_register(nr_counts),
            Instructions.dimen: init_register(nr_dimens),
            Instructions.skip: init_register(nr_skips),
            Instructions.mu_skip: init_register(nr_mu_skips),
            Instructions.toks: init_register(nr_token_lists),
        }

    def _get_register_map(self, type_):
        return self.register_map[Instructions(type_)]

    def get_register_value(self, type_, i):
        register = self._get_register_map(type_)
        try:
            r = register[i]
        except KeyError:
            raise ValueError('No register number {} of type {}'
                             .format(i, type_))
        if r is None:
            raise ValueError('No value in register number {} of type {}'
                             .format(i, type_))
        return r

    def set_register_value(self, type_, i, value):
        # TODO: Make type checking more strict, and do in more places.
        if type_ in ('COUNT', 'DIMEN'):
            expected_type = int
        elif type_ in ('SKIP', 'MU_SKIP'):
            expected_type = dict
        elif type_ == 'TOKS':
            expected_type = list
        if not isinstance(value, expected_type):
            raise TypeError('Setting register to wrong type')
        register = self._get_register_map(type_)
        if i not in register:
            raise ValueError('No register number {} of type {}'
                             .format(i, type_))
        register[i] = value
