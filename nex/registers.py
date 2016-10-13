from .common import Token
from .typer import register_tokens, short_hand_def_to_token_map


def is_register_type(type_):
    return type_ in register_tokens.values()


def register_token_type_to_register_type(type_):
    assert type_ in short_hand_def_to_token_map.values()
    return type_[:type_.find('_DEF_TOKEN')]


def get_initial_registers():
    register_sizes = [256 for _ in range(5)]
    return Registers(*register_sizes)


get_local_registers = get_initial_registers


class Registers(object):

    def __init__(self, nr_counts, nr_dimens,
                 nr_skips, nr_mu_skips, nr_token_lists):
        init_register = lambda n: {i: None for i in range(n)}
        cmd_register_map = {
            'count': init_register(nr_counts),
            'dimen': init_register(nr_dimens),
            'skip': init_register(nr_skips),
            'muskip': init_register(nr_mu_skips),
            'toks': init_register(nr_token_lists),
        }
        self.register_map = {register_tokens[c]: r for
                             c, r in cmd_register_map.items()}

    def _get_register_map(self, type_):
        return self.register_map[type_]

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
