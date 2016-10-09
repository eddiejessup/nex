from .typer import register_tokens, short_hand_def_to_token_map


def is_register_type(type_):
    return type_ in register_tokens.values()


def register_token_type_to_register_type(type_):
    assert type_ in short_hand_def_to_token_map.values()
    return type_[:type_.find('_DEF_TOKEN')]


def get_initial_registers():
    count = {i: None for i in range(256)}
    dimen = {i: None for i in range(256)}
    skip = {i: None for i in range(256)}
    mu_skip = {i: None for i in range(256)}
    tokens = {i: None for i in range(256)}
    registers = Registers(count, dimen, skip, mu_skip, tokens)
    return registers


def get_local_registers():
    registers = Registers(count={}, dimen={}, skip={}, mu_skip={}, tokens={})
    return registers


class Registers(object):

    def __init__(self, count, dimen, skip, mu_skip, tokens):
        cmd_register_map = {
            'count': count,
            'dimen': dimen,
            'skip': skip,
            'muskip': mu_skip,
            'toks': tokens,
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

    def get_advanced_register_value(self, type_, i, value):
        register = self.get_register(type_)
        result = register[i] + value
        return result
