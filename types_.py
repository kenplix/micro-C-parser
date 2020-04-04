from utilities import *

memory = map(lambda x: x, range(0, 1000))


def type_crop(from_type, to_type, number):
    if issubclass(from_type, Integer) and issubclass(to_type, Floating):
        return float(number)
    elif issubclass(from_type, Floating) and issubclass(to_type, Integer):
        return int(number)
    else:
        return number


def crop(from_type, to_type, number):
    bias = from_type.size - to_type.size
    integer_part = int(number)
    float_part = number - integer_part
    sign = '-' if list(str(number))[0] == '-' else '+'
    prefix = 3 if sign == '-' else 2
    binary = bin(integer_part)[prefix:]
    fill = from_type.size * 8 - len(binary)
    binary = ('0' * fill) + binary
    integer_part = int(sign + binary[bias * 8:], 2)
    return type_crop(from_type, to_type, integer_part + float_part)


def in_range(cls, number):
    return True if cls.min <= number <= cls.max else False


def determine_type(number):
    """Automatically determines the type of number"""
    find_all_sub(Integer) if isinstance(number, int) else find_all_sub(Floating)
    for cls in subclasses:
        if in_range(cls, number):
            return cls


class Object:

    def __init__(self, name, virtual_mode):
        if not virtual_mode:
            self.id = next(memory)

        self.name = name
        self._value = None

    @cached_property
    def allowed_inheritors(self):
        from grammar import MUL, VARIABLE
        return MUL, VARIABLE


class Type(type):

    def __call__(cls, *args, **kwargs):
        if cls in (Type, Numeric, Integer, Floating):
            raise TypeError(f'base class {cls} may not be instantiated, use only data types')
        return super().__call__(*args, **kwargs)


class Numeric(Object, metaclass=Type):

    def __init__(self, name, pointer, reference, virtual_mode, type_of_numbers):
        super(Numeric, self).__init__(name, virtual_mode)
        self._pointer = pointer
        self.reference = reference
        self.type_of_numbers = type_of_numbers

    @property
    def pointer(self):
        return self._pointer

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if isinstance(val, ARRAY):
            if not isinstance(self._value, ARRAY) and self._value is not None:
                raise TypeError
            self._value = val
        else:
            if isinstance(self._value, ARRAY) and self._value is not None:
                raise TypeError
            if in_range(self.__class__, val):
                self._value = self.type_of_numbers(val)
            else:
                self._value = crop(from_type=determine_type(val), to_type=self.__class__, number=val)

    def __repr__(self):
        return f'id:{self.id}, type:{self.__class__.__name__}, ' \
               f'*{self.pointer}, reference:{self.reference}, ' \
               f'name:{self.name}, value:{self.value}'


class Integer(Numeric):
    pass


class CHAR(Integer):

    size = 1
    min = -128
    max = 127

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(Integer, self).__init__(name, pointer, reference, virtual_mode, type_of_numbers=int)


class SHORT(CHAR):

    size = 2
    min = -32768
    max = 32767

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(Integer, self).__init__(name, pointer, reference, virtual_mode, type_of_numbers=int)


class INT(SHORT):

    size = 4
    min = -2147483648
    max = 2147483647

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(Integer, self).__init__(name, pointer, reference, virtual_mode, type_of_numbers=int)


class LONG(INT):

    size = 4
    min = -2147483648
    max = 2147483647

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(Integer, self).__init__(name, pointer, reference, virtual_mode, type_of_numbers=int)


class Floating(Numeric):
    pass


class FLOAT(Floating):

    size = 4
    min = -3.4e+38
    max = 3.4e+38

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(Floating, self).__init__(name, pointer, reference, virtual_mode, type_of_numbers=float)


class DOUBLE(FLOAT):

    size = 8
    min = -1.7e+308
    max = 1.7e+308

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(Floating, self).__init__(name, pointer, reference, virtual_mode, type_of_numbers=float)


class STRING(Object, metaclass=Type):

    def __init__(self, name=None, pointer=False, reference=None, virtual_mode=False):
        super(STRING, self).__init__(name, virtual_mode)
        self._pointer = pointer
        self.reference = reference

    @property
    def pointer(self):
        return self._pointer

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if isinstance(val, str):
            self._value = val
        else:
            raise TypeError(f'The value <{val}> is not string')


class Memory(list):

    def __init__(self):
        list.__init__([])
        self.last_viewed = None

    def get_by_id(self, id_, throw=False):
        for variable in self:
            if isinstance(variable.value, ARRAY):
                if variable.id <= id_ <= variable.id + variable.value.length - 1:
                    return variable
            else:
                if id == variable.id:
                    self.last_viewed = variable
                    return variable
        if throw:
            raise Exception(f'Variable with id <{id}> not declared')

    def get_by_name(self, name: str, throw=False):
        for variable in self:
            if name == variable.name:
                self.last_viewed = variable
                return variable
        if throw:
            raise Exception(f'Variable name <{name}> not declared')


class NonNegative:

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError('Cannot be negative')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class ARRAY(list):
    length = NonNegative()

    def __init__(self, length):
        list.__init__([])
        self.length = length
        self.alloc_memory(length)

    def alloc_memory(self, length):
        if self.__class__ is not Controller:
            for _ in range(length - 1):
                next(memory)


class Controller(ARRAY):

    def __init__(self, variable):
        super(Controller, self).__init__(variable.value.length)
        self.variable = variable
        self.counter = 0

    def __repr__(self):
        return f'{self.variable.value}'

    def _check_type_compatibility(self, variable):
        if self.variable.pointer != variable.pointer:
            raise TypeError(f'different types of pointers')
        if isinstance(variable.value, ARRAY):
            raise TypeError('array inside array')

        crop_func = type_crop if variable.size <= self.variable.__class__.size else crop
        return crop_func(from_type=variable.__class__,
                         to_type=self.variable.__class__,
                         number=variable.value)

    def _add_number(self, number):
        variable = determine_type(number)(virtual_mode=True)
        variable.value = number
        return self._check_type_compatibility(variable=variable)

    def _data_checker(self, data):
        if isinstance(data, int) or isinstance(data, float):
            return self._add_number(data)
        else:
            return self._check_type_compatibility(variable=data)

    def setitem(self, data, position):
        self.variable.value[position] = self._data_checker(data)

    def append(self, data):
        self.counter += 1
        if self.counter > self.length:
            raise IndexError(f'list index out of range - {self.length}')

        self.variable.value.append(self._data_checker(data))
