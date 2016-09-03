from typer import register_tokens


class Registers(object):

    def __init__(self):
        self.count = {i: None for i in range(256)}
        self.dimen = {i: None for i in range(256)}
        self.skip = {i: None for i in range(256)}
        self.mu_skip = {i: None for i in range(256)}
        cmd_register_map = {
            'count': self.count,
            'dimen': self.dimen,
            'skip': self.skip,
            'muskip': self.mu_skip,
        }
        self.reverse_token_map = {
            'COUNT_DEF_TOKEN': 'COUNT',
            'DIMEN_DEF_TOKEN': 'DIMEN',
            'SKIP_DEF_TOKEN': 'SKIP',
            'MU_SKIP_DEF_TOKEN': 'MU_SKIP',
        }

        self.register_map = {register_tokens[c]: r for
                             c, r in cmd_register_map.items()}

    def get_register(self, type_):
        return self.register_map[type_]

    def register_token_to_register_type(self, type_):
        return self.reverse_token_map[type_]

    def is_register_type(self, type_):
        return type_ in self.register_map
