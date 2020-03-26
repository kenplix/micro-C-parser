import operator


class Calculator:

    MATH_OPERATORS = {'+': operator.add,
                      '-': operator.sub,
                      '*': operator.mul,
                      '/': operator.truediv}

    LOGICAL_OPERATORS = {'==': operator.eq,
                         '!=': operator.ne,
                         '<': operator.lt,
                         '>': operator.gt,
                         '<=': operator.le,
                         '=>': operator.ge,
                         '&&': operator.and_,
                         '||': operator.or_,
                         '^': operator.xor}

    def __init__(self):
        self.token_storage = []

    @staticmethod
    def check_brackets_conditions(nomenclature):
        op_br_count, cl_br_count = nomenclature.count('('), nomenclature.count(')')
        nomenclature.insert(0, '(')
        nomenclature.append(')')

        # fill with zeros for correct parsing of signed expressions
        i = 0
        while i < len(nomenclature):
            if i + 1 < len(nomenclature) and nomenclature[i] == '(' and nomenclature[i + 1] in ('-', '+'):
                nomenclature.insert(i + 1, '0')
                i += 2
            else:
                i += 1

        def find_couples():
            # index brackets
            brackets_storage = []
            for index, bracket in enumerate(nomenclature):
                if bracket in ('(', ')'):
                    brackets_storage.append((index, bracket))

            pairs_of_brackets = []

            while len(brackets_storage) > 2:
                for index in range(len(brackets_storage)):
                    if index + 1 < len(brackets_storage) and \
                            brackets_storage[index][1] == '(' and brackets_storage[index + 1][1] == ')':
                        opening_index = brackets_storage[index][0]
                        closing_index = brackets_storage[index + 1][0]
                        pairs_of_brackets.append((opening_index, closing_index))
                        del brackets_storage[index], brackets_storage[index]
                        break
            else:
                pairs_of_brackets.append((brackets_storage[0][0], brackets_storage[1][0]))

            return pairs_of_brackets

        if op_br_count == cl_br_count:
            return find_couples()
        elif op_br_count > cl_br_count:
            raise SyntaxError(f'you have more opening brackets than closing brackets')
        else:
            raise SyntaxError(f'you have more closing brackets than opening brackets')

    @staticmethod
    def determine_type(number: str):
        return float(number) if '.' in number else int(number)

    def _execute(self, expression, operators=('*', '/', '+', '-', '<', '>', '<=', '>=', '&&', '||', '^')):
        def calculate(first, operator, second):
            if operator in self.MATH_OPERATORS:
                return str(self.MATH_OPERATORS[operator](self.determine_type(first), self.determine_type(second)))
            elif operator in self.LOGICAL_OPERATORS:
                res = str(self.LOGICAL_OPERATORS[operator](self.determine_type(first), self.determine_type(second)))
                if res == 'True':
                    return '1'
                elif res == 'False':
                    return '0'
                else:
                    return res
            else:
                raise SyntaxError(f'unknown operator - {operator}')

        for operator in operators:
            if operator in expression:
                index = 0
                while index + 2 < len(expression):
                    if expression[index] not in operators\
                            and expression[index + 2] not in operators \
                            and expression[index + 1] in operators:

                        pairs = calculate(*expression[index:index + 3])
                        del expression[index:index + 3]
                        expression.insert(index, pairs)
                    else:
                        index += 2

    def _part_of_the_calculations(self, expression):
        index = 0
        while index + 1 < len(expression):
            if expression[index] == '-' and expression[index + 1] == '+':
                del expression[index:index + 2]
                expression.insert(index, '-')
            elif expression[index] == '+' and expression[index + 1] == '-':
                del expression[index:index + 2]
                expression.insert(index, '-')
            elif expression[index] == '-' and expression[index + 1] == '-':
                del expression[index:index + 2]
                expression.insert(index, '+')
            elif expression[index] == '+' and expression[index + 1] == '+':
                del expression[index:index + 2]
                expression.insert(index, '+')
            else:
                index += 1

        self._execute(expression)
        return expression[0]

    # вложение скобок

    @staticmethod
    def _build_hierarchy(pairs_of_brackets):
        hierarchy = {}
        for i, j in pairs_of_brackets.copy():
            hierarchy[f'{i}-{j}'] = []
            index = 0
            while index < len(pairs_of_brackets):
                if pairs_of_brackets[index][0] > i and pairs_of_brackets[index][1] < j:
                    hierarchy[f'{i}-{j}'].append((pairs_of_brackets[index][0], pairs_of_brackets[index][1]))
                    del pairs_of_brackets[index]
                else:
                    index += 1
        return hierarchy

    @staticmethod
    def spliter(key, delimiter=None):
        return map(lambda x: int(x), key.split(delimiter))

    # первичные вычисления
    def _primary_calculations(self, hierarchy):
        calculated_hierarchy = {}
        for key, value in hierarchy.copy().items():
            start, end = self.spliter(key, '-')
            if not value:
                hierarchy.pop(key)
                calculated_hierarchy[key] = self._part_of_the_calculations(self.token_storage[start + 1:end])
        return calculated_hierarchy

    @staticmethod
    def find_range(all, part):
        temp = [zip((i, all[all.index(i) + 1]), part) for i in all if all.index(i) + 1 < len(all)]

        start = None
        for i in temp:
            j = list(i)
            if len(set(j[0])) == 1 and len(set(j[1])) == 1:
                start = temp.index(i)
                break

        if start:
            end = start + len(part) - 1
            return start, end

    def _other_calculations(self, hierarchy, calculated_hierarchy):
        last_result = None

        if not hierarchy.items():
            return self.determine_type(next(iter(calculated_hierarchy.values())))

        for index, item in enumerate(hierarchy.items()):
            key, value = item
            start, end = self.spliter(key, '-')
            dynamic_part = self.token_storage[start + 1:end]

            for calculated_key, calculated_value in calculated_hierarchy.copy().items():
                calculated_start, calculated_end = self.spliter(calculated_key, '-')

                if (calculated_start, calculated_end) in value:
                    calculated_part = self.token_storage[calculated_start:calculated_end + 1]
                    start_, end_ = self.find_range(dynamic_part, calculated_part)  # was part
                    for index in range(start_, end_ + 1):
                        dynamic_part[index] = '' if index != end_ else calculated_value

            dynamic_part = [i for i in dynamic_part if i != '']
            calculated_hierarchy[key] = self._part_of_the_calculations(dynamic_part)
            last_result = calculated_hierarchy[key]

        return self.determine_type(last_result)

    def find_value(self):
        br_pairs = self.check_brackets_conditions(self.token_storage)
        hierarchy = self._build_hierarchy(br_pairs)
        primary_calculated_hierarchy = self._primary_calculations(hierarchy)
        return self._other_calculations(hierarchy, primary_calculated_hierarchy)

if __name__ == '__main__':
    test = Calculator()
    test.token_storage = ['4','-','5']
    print(test.find_value())