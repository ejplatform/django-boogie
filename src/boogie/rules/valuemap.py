from .value import value


class ValueMap(dict):
    def compute(self, name, *args, **kwargs):
        return name in self and self[name].test(*args, **kwargs)

    def value_exists(self, name):
        return name in self

    def add_value(self, name, pred):
        if name in self:
            raise KeyError('A rule with name `%s` already exists' % name)
        self[name] = pred

    def remove_value(self, name):
        del self[name]

    def __setitem__(self, name, pred):
        fn = value(pred)
        super().__setitem__(name, fn)


# Shared rule set
default_value_map = ValueMap()


def add_value(name, pred):
    default_value_map.add_value(name, pred)


def remove_value(name):
    default_value_map.remove_value(name)


def value_exists(name):
    return default_value_map.value_exists(name)


def compute(name, *args, **kwargs):
    return default_value_map.compute(name, *args, **kwargs)
