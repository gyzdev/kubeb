class BaseGenerator(object):
    def __init__(self, data: dict):
        self.data = data

    def execute(self):
        raise NotImplementedError
