arithmetic_operations = {
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
}

comparator_operations = {
    # comparisons
    '__eq__',
    '__ne__',
    '__ge__', '__le__',
    '__gt__', '__lt__',
}

bitwise_operations = {
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

operations = arithmetic_operations | comparator_operations | bitwise_operations

backend_comparator_operations = {
    'UGE', 'ULE', 'UGT', 'ULT',
}

backend_bitwise_operations = {
    'RotateLeft', 'RotateLeft', 'LShR',
}

backend_boolean_operations = {
    'And', 'Or', 'Not', 'If',
}

backend_bitmod_operations = {
    'Concat', 'Extract', 'SignExt', 'ZeroExt',
}

backend_creation_operations = {
    'BoolVal', 'BitVec', 'BitVecVal',
}

backend_operations = backend_comparator_operations | backend_bitwise_operations | backend_boolean_operations | backend_bitmod_operations | backend_creation_operations

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
