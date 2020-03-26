subclasses = []

# метод для нахождения подклассов
# параметр _counter служит для обнуления результата поиска и является служебным
def find_all_sub(*cls, _counter: int = 0):

    if _counter == 0:
        subclasses.clear()

    for cls in cls:
        _counter += 1
        for sub in cls.__subclasses__():
            subclasses.append(sub)
            find_all_sub(sub, _counter=_counter)


class cached_property:

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        result = instance.__dict__[self.func.__name__] = self.func(instance)
        return result


class Checker:

    def __setattr__(self, key, value):
        if key != 'inheritor':
            raise AttributeError

        if value in self.allowed_inheritors:
            self.__dict__['inheritor'] = value
        else:
            raise SyntaxError(f'wrong child type <{value.__name__}> after parent <{self.__class__.__name__}>')
