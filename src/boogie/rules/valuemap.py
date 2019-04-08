from .value import value


class ValueMap(dict):
    def compute(self, name, *args, **kwargs):
        return name in self and self[name].compute(*args, **kwargs)

    def value_exists(self, name):
        return name in self

    def add_value(self, name, pred):
        if name in self:
            raise KeyError("A rule with name `%s` already exists" % name)
        self[name] = pred

    def remove_value(self, name):
        del self[name]

    def __setitem__(self, name, pred):
        fn = value(pred)
        super().__setitem__(name, fn)


# Shared rule set
default_value_map = ValueMap()
NOT_GIVEN = object()


def add_value(name, func):
    default_value_map.add_value(name, func)


def register_value(name, **kwargs):
    def decorator(func):
        vfunc = value(**kwargs)(func)
        default_value_map.add_value(name, vfunc)
        return vfunc

    return decorator


def remove_value(name):
    default_value_map.remove_value(name)


def value_exists(name):
    return default_value_map.value_exists(name)


def compute(name, *args, **kwargs):
    return default_value_map.compute(name, *args, **kwargs)


def get_value(name, default=NOT_GIVEN):
    try:
        return default_value_map[name]
    except KeyError:
        if default is NOT_GIVEN:
            raise ValueError("could not find value: %s" % name)
        return default
