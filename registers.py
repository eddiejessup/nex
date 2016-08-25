class Registers(object):

    def __init__(self):
        self.count = {i: None for i in range(256)}


registers = Registers()