from typer import register_tokens


reverse_token_map = {
    'COUNT_DEF_TOKEN': 'COUNT',
    'DIMEN_DEF_TOKEN': 'DIMEN',
    'SKIP_DEF_TOKEN': 'SKIP',
    'MU_SKIP_DEF_TOKEN': 'MU_SKIP',
}


def is_register_type(type_):
    return type_ in register_tokens.values()


def register_token_type_to_register_type(type_):
    return reverse_token_map[type_]


def get_initial_registers():
    count = {i: None for i in range(256)}
    dimen = {i: None for i in range(256)}
    skip = {i: None for i in range(256)}
    mu_skip = {i: None for i in range(256)}
    registers = Registers(count, dimen, skip, mu_skip)
    return registers


def get_local_registers():
    registers = Registers(count={}, dimen={}, skip={}, mu_skip={})
    return registers


class Registers(object):

    def __init__(self, count, dimen, skip, mu_skip):
        cmd_register_map = {
            'count': count,
            'dimen': dimen,
            'skip': skip,
            'muskip': mu_skip,
        }

        self.register_map = {register_tokens[c]: r for
                             c, r in cmd_register_map.items()}

    def get_register(self, type_):
        return self.register_map[type_]

    def get_register_value(self, type_, i):
        register = self.get_register(type_)
        return register[i]

    def set_register_value(self, type_, i, value):
        register = self.get_register(type_)
        register[i] = value

    def advance_register_value(self, type_, i, value):
        register = self.get_register(type_)
        register[i] += value
