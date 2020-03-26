from utilities import *

memory = map(lambda x: str(x), range(0, 1000))


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


# метод для автоматического определения типа числа
def determine_type(number):
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
        self.type_of_numbers = type_of_numbers  # float or int
        # self.__class__ - type

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


# todo: у строк тоже есть указатели и это массив символов
class STRING(Object, metaclass=Type):

    def __init__(self, name=None, virtual_mode=False):
        super(STRING, self).__init__(name, virtual_mode)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if isinstance(val, str):
            self._value = val
        else:
            raise TypeError(f'значение {val} не является строчным')


class Memory(list):

    def __init__(self):
        list.__init__([])
        self.last_viewed = None

    def get(self, attr, val):
        for variable in self:
            if val == variable.__dict__[attr]:
                self.last_viewed = variable
                return variable

    #  todo : написать нормальный гетер параметров (выше потестить)
    def get(self, name: str):
        for variable in self:
            if name == variable.name or (name.isdigit() and name == variable.id):
                self.last_viewed = variable
                return variable


class NonNegative:

    def __get__(self, instance, owner):
        return instance.__dict__[self.name]

    def __set__(self, instance, value):
        if value < 0:
            raise ValueError('Cannot be negative.')
        instance.__dict__[self.name] = value

    def __set_name__(self, owner, name):
        self.name = name


class ARRAY(list):
    length = NonNegative()

    def __init__(self, length):
        list.__init__([])
        self.length = length
        # выделение памти на массив
        for _ in range(length - 2):
            print(next(memory))


class Controller(ARRAY):
    def __init__(self, variable):
        super(Controller, self).__init__(variable.value.length)
        self.variable = variable
        self.counter = 0

    def __repr__(self):
        return f'{self.variable.value}'

    def _check_type_compatibility(self, variable):
        # print(f'get type - {variable.__class__}, array type - {self.variable.__class__}')
        if self.variable.pointer != variable.pointer:
            raise TypeError(f'different types of pointers')
        if isinstance(variable.value, ARRAY):
            raise TypeError('array inside array')

        crop_func = type_crop if variable.size <= self.variable.__class__.size else crop
        self.variable.value.append(crop_func(from_type=variable.__class__,
                                             to_type=self.variable.__class__,
                                             number=variable.value))

    def _add_number(self, number):
        variable = determine_type(number)()
        variable.value = number
        self._check_type_compatibility(variable=variable)

    def append(self, data):
        self.counter += 1
        if self.counter > self.length:
            raise IndexError(f'list index out of range - {self.variable.value.length}')

        if isinstance(data, int) or isinstance(data, float):
            self._add_number(data)
        else:
            self._check_type_compatibility(variable=data)


if __name__ == '__main__':
    # print(isinstance(CHAR('qwewq'), Integer))
    t = Type('kek', (), {})
    # num = Numeric('lol', False, False, False, int)
    # n = Integer(False, False, False, False, False)
    # w = CHAR()
    # print('lol')

    # '''test = CHAR('TEST')
    #   test.set_value(False, False, DataStorage(length=3))'''

    a = CHAR('a', False)
    # print(a)
    mem = Memory()
    mem.append(a)
    print(mem)
    # print(mem.get('b'))
    print()
    b = INT('b')
    print(b)
    c = FLOAT('c')
    print(c)
    c.value = 12345
    print(c)
    d = INT('d')
    print(d)
    s = CHAR('s', False)
    print(s)
    # s.value = 333333.57
    print(s)

    st = ARRAY()
    print('jhebfjhebker   ', st)
    s.value = st
    # st.add(c)
    # s.set_value(s.pointer, s.reference, st)
    array = Controller(s)
    print(array)
    array.append(123)
    print(array)
    lol_var = INT('lol')
    print(crop(LONG, LONG, 355))
    print(s.__class__.__name__)
