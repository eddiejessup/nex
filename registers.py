class Registers(object):

    def __init__(self):
        self.count = {i: None for i in range(256)}
        self.dimen = {i: None for i in range(256)}
        self.skip = {i: None for i in range(256)}
        self.mu_skip = {i: None for i in range(256)}


registers = Registers()