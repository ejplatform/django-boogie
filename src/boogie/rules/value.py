import inspect
import operator as op
from functools import partial
from functools import update_wrapper

from rules.predicates import Context, NO_VALUE, Predicate, _context

from sidekick.core.operators import SYMBOLS


def binary(op, reverse=False, symbol=None):
    symbol = symbol or SYMBOLS[op]

    def binary_op(self, other):
        if isinstance(other, Value):
            fn = lambda *args: self._combine_binop(other, op, args)
            name = f"{self.name} {symbol} {other.name}"
            return Value(fn, name)
        else:
            transform = lambda x: op(x, other)
            fn = lambda *args: self._transform(transform, args)
            name = f"{self.name} {symbol} {repr(other)}"
            return Value(fn, name)

    if reverse:

        def rbinary_op(self, other):
            fn = lambda *args: self._transform(partial(op, other), args)
            name = f"{self.name} {symbol} {repr(other)}"
            return Value(fn, name)

        return rbinary_op

    return binary_op


def unary(op, symbol):
    symbol = symbol or SYMBOLS.get(op, op.__name__)

    def unary(self):
        fn = lambda *args: self._transform(op, args)
        name = f"{symbol} {self.name}"
        return Value(fn, name)

    return unary


class Value:
    def __init__(self, fn, name=None, bind=False):  # noqa: C901
        # fn can be a callable with any of the following signatures:
        #   - fn(obj=None, user=None)
        #   - fn(obj=None)
        #   - fn()
        if isinstance(fn, Value):
            fn, num_args, var_args, name = (
                fn.fn,
                fn.num_args,
                fn.var_args,
                name or fn.name,
            )
        elif isinstance(fn, partial):
            argspec = inspect.getfullargspec(fn.func)
            var_args = argspec.varargs is not None
            num_args = len(argspec.args) - len(fn.args)
            if inspect.ismethod(fn.func):
                num_args -= 1  # skip `self`
            name = fn.func.__name__
        elif inspect.ismethod(fn):
            argspec = inspect.getfullargspec(fn)
            var_args = argspec.varargs is not None
            num_args = len(argspec.args) - 1  # skip `self`
        elif inspect.isfunction(fn):
            argspec = inspect.getfullargspec(fn)
            var_args = argspec.varargs is not None
            num_args = len(argspec.args)
        elif callable(fn):
            callfn = getattr(fn, "__call__")
            argspec = inspect.getfullargspec(callfn)
            var_args = argspec.varargs is not None
            num_args = len(argspec.args) - 1  # skip `self`
            name = name or type(fn).__name__
        else:
            raise TypeError("Incompatible value function.")
        if bind:
            num_args -= 1
        if num_args > 2:
            raise TypeError("Value function must receive at most 2 arguments")
        self.fn = fn
        self.num_args = num_args
        self.var_args = var_args
        self.name = name or fn.__name__
        self.bind = bind

    def __repr__(self):
        type_name = type(self).__name__
        return "<%s:%s object at %s>" % (type_name, self, hex(id(self)))

    # Value is not a subclass of Predicate, but shares many functionality
    # We simply copy the common methods here.
    __str__ = Predicate.__str__
    __call__ = Predicate.__call__
    context = Predicate.context
    skip = Predicate.skip

    # Binary operators
    __add__ = binary(op.add)
    __radd__ = binary(op.add, reverse=True)
    __sub__ = binary(op.sub)
    __rsub__ = binary(op.sub, reverse=True)
    __mul__ = binary(op.mul)
    __rmul__ = binary(op.mul, reverse=True)
    __truediv__ = binary(op.truediv)
    __rtruediv__ = binary(op.truediv, reverse=True)

    def compute(self, obj=NO_VALUE, user=NO_VALUE):
        """
        The canonical method to invoke values.
        """
        args = tuple(arg for arg in (obj, user) if arg is not NO_VALUE)
        _context.stack.append(Context(args))
        try:
            return self._apply(*args)
        finally:
            _context.stack.pop()

    def _apply(self, *args):
        # Internal method that is used to invoke the predicate with the
        # proper number of positional arguments, inside the current
        # invocation context.
        if self.var_args:
            callargs = args
        elif self.num_args > len(args):
            callargs = args + (None,) * (self.num_args - len(args))
        else:
            callargs = args[: self.num_args]
        if self.bind:
            callargs = (self,) + callargs
        return self.fn(*callargs)

    def _transform(self, func, args):
        result = self._apply(*args)
        return func(result)

    def _combine_binop(self, other, op, args):
        left = self._apply(*args)
        right = other._apply(*args)
        return op(left, right)


def value(fn=None, name=None, **options):
    """
    Decorator that constructs a ``Value`` instance from any function::

    >>> @value
    ... def status_display(question):
    ...     if question.status == question.OPEN:
    ...         return 'Receiving submissions'
    ...     else:
    ...         return 'Closed'
    """
    if not name and not callable(fn):
        name = fn
        fn = None

    def inner(fn):
        if isinstance(fn, Value):
            return fn
        p = Value(fn, name, **options)
        update_wrapper(p, fn)
        return p

    if fn:
        return inner(fn)
    else:
        return inner
