#!/usr/bin/env python

import logging
l = logging.getLogger("claripy.expression")

import operator
from .storable import Storable

class A(object):
    '''
    An A(ST) tracks a tree of calls (including operations) on arguments.
    '''

    def __init__(self, op, args):
        self._op = op
        self._args = args

    def eval(self, backends, save, model=None):
        args = [ ]
        for a in self._args:
            if isinstance(a, E):
                args.append(a.eval(backends=backends, save=save, model=model))
            elif isinstance(a, A):
                args.append(a.eval(backends, save, model=model))
            else:
                args.append(a)

        for b in backends:
            l.debug("trying evaluation with %s", b)
            try:
                return b.call(self._op, args, model=model)
            except BackendError:
                l.debug("... failed")
                continue

        raise Exception("eval failed with available backends")

    def __repr__(self):
        if '__' in self._op:
            return "%s.%s%s" % (self._args[0], self._op, self._args[1:])
        else:
            return "%s%s" % (self._op, self._args)

class E(Storable):
    '''
    A base class to wrap Z3 objects.
    '''
    __slots__ = [ 'variables', 'symbolic', '_uuid', '_obj', '_ast', '_stored' ]

    def __init__(self, claripy, variables=None, symbolic=None, uuid=None, obj=None, ast=None, stored=False):
        Storable.__init__(self, claripy, uuid=uuid)
        have_uuid = uuid is not None
        have_data = not (variables is None or symbolic is None or (obj is None and ast is None))

        if have_uuid and not have_data:
            self._load()
        elif have_data:
            self.variables = variables
            self.symbolic = symbolic

            self._uuid = uuid
            self._obj = obj
            self._ast = ast
            self._stored = stored
        else:
            raise ValueError("invalid arguments passed to E()")

    def _load(self):
        e = self._claripy.dl.load_expression(self._uuid)
        self.variables = e.variables
        self.symbolic = e.symbolic

        self._uuid = e._uuid
        self._obj = e._obj
        self._ast = e._ast
        self._stored = e._stored

    def __nonzero__(self):
        raise Exception('testing Expressions for truthiness does not do what you want, as these expressions can be symbolic')

    @property
    def is_abstract(self):
        return self._obj is None

    @property
    def is_actual(self):
        return self._obj is not None

    def __repr__(self):
        name = "E"
        if self.symbolic:
            name += "S"

        if self._obj is not None:
            return name + "(%s)" % self._obj
        elif self._ast is not None:
            return name + "(%s)" % self._ast
        elif self._uuid is not None:
            return name + "(uuid=%s)" % self._uuid

    def _do_op(self, op_name, args):
        if all([ type(a) in {int, long, float, str, bool} for a in (self._obj,)+args ]) and hasattr(operator, op_name):
            return getattr(operator, op_name)(*((self._obj,)+args))

        for b in self._claripy.expression_backends:
            try:
                e = b.call(op_name, (self,)+args)
                #if self._ast is None:
                #   e._ast = A(op_name, (self,)+args)
                return e
            except BackendError:
                continue

        raise Exception("no backend can handle operation %s" % op_name)

    def eval(self, backends=None, save=False, model=None):
        if type(self._obj) in { int, long, str }:
            return self._obj

        if self._obj is not None and backends is None:
            l.debug("eval() called with an existing obj %r", self._obj)
            return self._obj
        elif self._obj is not None and backends is not None:
            for b in backends:
                try:
                    r = b.convert(self._obj, model=model)
                    if save: self._obj = r
                    return r
                except BackendError:
                    pass
            raise Exception("no backend can convert obj %r" % self._obj)
        elif isinstance(self._ast, A):
            r = self._ast.eval(backends if backends is not None else self._claripy.expression_backends, save=save, model=model)
            if save or backends is None:
                if isinstance(r, E):
                    self._obj = r._obj
                    self.variables = r.variables
                    self.symbolic = r.symbolic
                else:
                    self._obj = r
                return r
            else:
                return r._obj if isinstance(r, E) else r
        else:
            if self._ast is None:
                raise Exception("AST is None in abstract E!")

            r = self._ast
            if save or backends is None:
                self._obj = r
            return r

    def abstract(self, backends=None):
        if self._ast is not None:
            l.debug("abstract() called with an existing ast")
            return self._ast

        for b in backends if backends is not None else self._claripy.expression_backends:
            l.debug("trying abstraction with %s", b)
            try:
                r = b.abstract(self)
                if isinstance(r, E):
                    self._ast = r._ast
                    self.variables = r.variables
                    self.symbolic = r.symbolic
                else:
                    self._ast = r

                l.debug("... success!")
                return self._ast
            except BackendError:
                l.debug("... BackendError!")
                continue

        raise Exception("abstraction failed with available backends")

    def split(self, split_on, backends=None):
        self.abstract(backends=backends)
        if not isinstance(self._ast, A):
            return [ self ]

        if self._ast._op in split_on:
            l.debug("Trying to split: %r", self._ast)
            if all(isinstance(a, E) for a in self._ast._args):
                return self._ast._args[:]
            else:
                raise Exception('wtf')
        else:
            l.debug("no split for you")
            return [ self ]

    #
    # Storing and loading of expressions
    #

    def store(self):
        self._claripy.dl.store_expression(self)

    def __getstate__(self):
        if self._uuid is not None:
            l.debug("uuid pickle on %s", self)
            return self._uuid
        l.debug("full pickle on %s", self)

        if self._ast is None:
            self.abstract()
        return self._uuid, self._ast, self.variables, self.symbolic

    def __setstate__(self, s):
        if type(s) is str:
            self.__init__([ ], uuid=s)
            return

        uuid, ast, variables, symbolic = s
        self.__init__([ ], variables=variables, symbolic=symbolic, ast=ast, uuid=uuid)

    #
    # BV operations
    #

    def __len__(self):
        return self._claripy.size(self)._obj
    size = __len__

    def __iter__(self):
        raise Exception("Please don't iterate over Expressions!")

    def simplify(self):
        for b in self._claripy.expression_backends:
            try:
                return b.simplify_expr(self)
            except BackendError:
                pass

        raise Exception("unable to simplify")

    def chop(self, bits=1):
        s = len(self)
        if s % bits != 0:
            raise ValueError("expression length (%d) should be a multiple of 'bits' (%d)" % (len(self), bits))
        elif s == bits:
            return [ self ]
        else:
            return list(reversed([ self[(n+1)*bits - 1:n*bits] for n in range(0, s / bits) ]))

    def reversed(self, chunk_bits=8):
        '''
        Reverses the expression.
        '''
        s = self.chop(bits=chunk_bits)
        if len(s) == 1:
            return s[0]
        else:
            return self._claripy.Concat(*reversed(s))

    def __getitem__(self, rng):
        if type(rng) is slice:
            return self._claripy.Extract(int(rng.start), int(rng.stop), self)
        else:
            return self._claripy.Extract(int(rng), int(rng), self)

    def zero_extend(self, n):
        return self._claripy.ZeroExt(n, self)

    def sign_extend(self, n):
        return self._claripy.SignExt(n, self)

#
# Wrap stuff
#
operations = {
    # arithmetic
    '__add__', '__radd__',
    '__div__', '__rdiv__',
    '__truediv__', '__rtruediv__',
    '__floordiv__', '__rfloordiv__',
    '__mul__', '__rmul__',
    '__sub__', '__rsub__',
    '__pow__', '__rpow__',
    '__mod__', '__rmod__',
    '__divmod__', '__rdivmod__',

    # comparisons
    '__eq__',
    '__ne__',
    '__ge__', '__le__',
    '__gt__', '__lt__',

    # bitwise
    '__neg__',
    '__pos__',
    '__abs__',
    '__invert__',
    '__or__', '__ror__',
    '__and__', '__rand__',
    '__xor__', '__rxor__',
    '__lshift__', '__rlshift__',
    '__rshift__', '__rrshift__',
}

opposites = {
    '__add__': '__radd__', '__radd__': '__add__',
    '__div__': '__rdiv__', '__rdiv__': '__div__',
    '__truediv__': '__rtruediv__', '__rtruediv__': '__truediv__',
    '__floordiv__': '__rfloordiv__', '__rfloordiv__': '__floordiv__',
    '__mul__': '__rmul__', '__rmul__': '__mul__',
    '__sub__': '__rsub__', '__rsub__': '__sub__',
    '__pow__': '__rpow__', '__rpow__': '__pow__',
    '__mod__': '__rmod__', '__rmod__': '__mod__',
    '__divmod__': '__rdivmod__', '__rdivmod__': '__divmod__',

    '__eq__': '__eq__',
    '__ne__': '__ne__',
    '__ge__': '__le__', '__le__': '__ge__',
    '__gt__': '__lt__', '__lt__': '__gt__',

    #'__neg__':
    #'__pos__':
    #'__abs__':
    #'__invert__':
    '__or__': '__ror__', '__ror__': '__or__',
    '__and__': '__rand__', '__rand__': '__and__',
    '__xor__': '__rxor__', '__rxor__': '__xor__',
    '__lshift__': '__rlshift__', '__rlshift__': '__lshift__',
    '__rshift__': '__rrshift__', '__rrshift__': '__rshift__',
}

def wrap_operator(cls, op_name):
    def wrapper(self, *args):
        return self._do_op(op_name, args)
    wrapper.__name__ = op_name

    setattr(cls, op_name, wrapper)

def make_methods(cls):
    for name in operations:
        wrap_operator(cls, name)
make_methods(E)

from .backends.backend import BackendError
