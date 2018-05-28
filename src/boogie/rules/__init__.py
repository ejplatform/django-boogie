from rules import *
from rules.rulesets import default_rules as DEFAULT_RULES

from .proxy import proxy, proxy_seq
from .value import value
from .valuemap import ValueMap, compute, add_value, value_exists, remove_value, register_value


def register_rule(name, **kwargs):
    def decorator(func):
        pred = predicate(**kwargs)(func)
        add_rule(name, pred)
        return pred

    return decorator


def register_perm(name, **kwargs):
    def decorator(func):
        pred = predicate(**kwargs)(func)
        add_perm(name, pred)
        return pred

    return decorator


def get_rule(name):
    try:
        return DEFAULT_RULES[name]
    except KeyError:
        raise ValueError('rule does not exist: %r' % name)
