class Library(object):

    def __init__(self):
        self.env = None
        self.extensions = []
        self.filters = {}
        self.globals = {}
        self.tests = {}
        self.attrs = {}

    def set_env(self, env):
        self.env = env

    def filter(self, func):
        self.filters[func.__name__] = func

        if self.env:
            self.env.filters[func.__name__] = func

    def attr(self, name, value):
        self.attrs[name] = value
        if self.env:
            setattr(self.env, name, value)

    def extension(self, extension):
        self.extensions.append(extension)
        if self.env:
            self.env.add_extension(extension)
