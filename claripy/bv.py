import functools

def compare_bits(f):
    @functools.wraps(f)
    def compare_guard(self, o):
        if self.bits != o.bits:
            raise TypeError("bitvectors are differently-sized (%d and %d)" % (self.bits, o.bits))
        return f(self, o)

    return compare_guard

def normalize_types(f):
    @functools.wraps(f)
    def normalizer(self, o):
        if hasattr(o, '__module__') and o.__module__ == 'z3':
            o = BVV(o.as_long(), o.size())
        if type(o) in (int, long):
            o = BVV(o, self.bits)
        if type(self) in (int, long):
            self = BVV(self, self.bits)
        return f(self, o)

    return normalizer

class BVV(object):
    def __init__(self, value, bits):
        self.bits = bits
        self._value = 0
        self.mod = 2**bits
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = v % self.mod

    @property
    def signed(self):
        return self._value if self._value < self.mod/2 else self._value % (self.mod/2) - (self.mod/2)

    @signed.setter
    def signed(self, v):
        self._value = v % -self.mod

    #
    # Arithmetic stuff
    #

    @normalize_types
    @compare_bits
    def __add__(self, o):
        return BVV(self.value + o.value, self.bits)

    @normalize_types
    @compare_bits
    def __sub__(self, o):
        return BVV(self.value - o.value, self.bits)

    @normalize_types
    @compare_bits
    def __mul__(self, o):
        return BVV(self.value * o.value, self.bits)

    @normalize_types
    @compare_bits
    def __mod__(self, o):
        return BVV(self.value % o.value, self.bits)

    @normalize_types
    @compare_bits
    def __div__(self, o):
        return BVV(self.value / o.value, self.bits)

    #
    # Reverse arithmetic stuff
    #

    @normalize_types
    @compare_bits
    def __radd__(self, o):
        return BVV(self.value + o.value, self.bits)

    @normalize_types
    @compare_bits
    def __rsub__(self, o):
        return BVV(o.value - self.value, self.bits)

    @normalize_types
    @compare_bits
    def __rmul__(self, o):
        return BVV(self.value * o.value, self.bits)

    @normalize_types
    @compare_bits
    def __rmod__(self, o):
        return BVV(o.value % self.value, self.bits)

    @normalize_types
    @compare_bits
    def __rdiv__(self, o):
        return BVV(o.value / self.value, self.bits)

    #
    # Bit operations
    #

    @normalize_types
    @compare_bits
    def __and__(self, o):
        return BVV(self.value & o.value, self.bits)

    @normalize_types
    @compare_bits
    def __or__(self, o):
        return BVV(self.value | o.value, self.bits)

    @normalize_types
    @compare_bits
    def __xor__(self, o):
        return BVV(self.value ^ o.value, self.bits)

    @normalize_types
    @compare_bits
    def __lshift__(self, o):
        return BVV(self.value << o.signed, self.bits)

    @normalize_types
    @compare_bits
    def __rshift__(self, o):
        return BVV(self.signed >> o.signed, self.bits)

    def __invert__(self):
        return BVV(self.value ^ self.mod-1, self.bits)

    #
    # Reverse bit operations
    #

    @normalize_types
    @compare_bits
    def __rand__(self, o):
        return BVV(self.value & o.value, self.bits)

    @normalize_types
    @compare_bits
    def __ror__(self, o):
        return BVV(self.value | o.value, self.bits)

    @normalize_types
    @compare_bits
    def __rxor__(self, o):
        return BVV(self.value ^ o.value, self.bits)

    @normalize_types
    @compare_bits
    def __rlshift__(self, o):
        return BVV(o.value << self.signed, self.bits)

    @normalize_types
    @compare_bits
    def __rrshift__(self, o):
        return BVV(o.signed >> self.signed, self.bits)

    #
    # Boolean stuff
    #

    @normalize_types
    @compare_bits
    def __eq__(self, o):
        return self.value == o.value

    @normalize_types
    @compare_bits
    def __ne__(self, o):
        return self.value != o.value

    @normalize_types
    @compare_bits
    def __lt__(self, o):
        return self.signed < o.signed

    @normalize_types
    @compare_bits
    def __gt__(self, o):
        return self.signed > o.signed

    @normalize_types
    @compare_bits
    def __le__(self, o):
        return self.signed <= o.signed

    @normalize_types
    @compare_bits
    def __ge__(self, o):
        return self.signed >= o.signed

    #
    # Conversions
    #

    def size(self):
        return self.bits

    def __repr__(self):
        return 'BVV(%d, %d)' % (self.value, self.bits)

#
# External stuff
#

def BitVecVal(value, bits):
    return BVV(value, bits)

def ZeroExt(num, o):
    return BVV(o.value, o.bits + num)

def SignExt(num, o):
    return BVV(o.signed, o.bits + num)

def Extract(f, t, o):
    return BVV((o.value >> t) & (2**(f+1) - 1), f-t+1)

def Concat(*args):
    total_bits = 0
    total_value = 0

    for o in args:
        total_value = (total_value << o.bits) | o.value
        total_bits += o.bits
    return BVV(total_value, total_bits)

def RotateRight(self, bits):
    raise NotImplementedError()

def RotateLeft(self, bits):
    raise NotImplementedError()

@normalize_types
@compare_bits
def ULT(self, o):
    return self.value < o.value

@normalize_types
@compare_bits
def UGT(self, o):
    return self.value > o.value

@normalize_types
@compare_bits
def ULE(self, o):
    return self.value <= o.value

@normalize_types
@compare_bits
def UGE(self, o):
    return self.value >= o.value

#
# Pure boolean stuff
#

def BoolVal(b):
    return b

def And(*args):
    return all(args)

def Or(*args):
    return all(args)

def Not(b):
    return not b

def If(c, t, f):
    if c:
        return t
    else:
        return f

@normalize_types
@compare_bits
def LShR(a, b):
    return BVV(a.value >> b.signed, a.bits)


def test():
    a = BVV(1, 8)
    b = BVV(2, 8)
    assert a | b == 3
    assert a & b == 0
    assert a / b == 0
    assert b * b == 4
    assert a.signed == a.value
    assert a + 8 == 9

    c = BVV(128, 8)
    assert c.signed == -128
    print "YAY"

    d = BVV(255, 8)
    assert Extract(1, 0, d) == 3
    assert SignExt(8, d).value == 2**16-1
    assert ZeroExt(8, d).size() == 16
    assert ZeroExt(8, d).value == 255

    e = BVV(0b1010, 4)
    f = BVV(0b11, 2)
    assert Concat(e, e, e, e) == 0b1010101010101010
    assert Concat(e,f,f) == 0b10101111

    print "OK"

if __name__ == '__main__':
    test()