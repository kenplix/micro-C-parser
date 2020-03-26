from lexer import *
from expression_handler.calculator import Calculator

ID = 'id'
NAME = 'name'

ANNOUNCEMENT = 'announcement'
INITIALIZE = 'initialize'
GETITEM = 'getitem'
REFERENCE = 'reference'


class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.memory = types_.Memory()

    def is_WS_before(self, token, /):
        ch = self.lexer.ch
        if self.lexer.token is token:
            if ch == ' ':
                raise SyntaxError(f'WS before {token}')
            return False
        else:
            raise SyntaxError(f'Ожидается другой токен {token} получен {self.lexer.token}')

    # arr[<expression>] = {<expression>, <expression>, ..., <expression>}
    def parse_array(self, name, pointer=False, *, mode):

        def define_action(dimension):
            if isinstance(dimension, int):

                if self.lexer.token is RSBR:

                    if mode == ANNOUNCEMENT:
                        self.lexer.next_token()
                        return types_.ARRAY(length=value)

                    elif mode == GETITEM:
                        variable = self.memory.get(NAME, val=name)
                        return variable.value[dimension]

                    elif mode == REFERENCE:
                        start = self.memory.get(NAME, val=name).id
                        return start + dimension
                else:
                    raise SyntaxError(
                        f'unexpected token - {self.lexer.token.__name__}, should be <]>')
            else:
                raise SyntaxError('define_action type must be <INTEGER> and not <FRACTIONAL>')

        if pointer:
            raise SyntaxError('not implemented feature')

        self.lexer.next_token()
        value = self.calculate_expression(stop_tokens=(RSBR,))  # in [...]
        return define_action(value)

    #todo: есть массив нулевой длинны, создавать его заново когда длинна известна
    def array_init(self, controller: types_.Controller):
        temp_array = []
        if self.lexer.token is LBRC:
            self.lexer.next_token()
            while True:
                temp_array.append(self.calculate_expression(stop_tokens=(COMMA, RBRC)))
                if self.lexer.token is RBRC:
                    break
                self.lexer.next_token()

            if controller.length == 0:
                array = types_.ARRAY(length=len(temp_array))
                variable = controller.variable
                variable.value = array
                controller = types_.Controller(variable)

            elif controller.length >= len(temp_array):
                zeros = [0 for _ in range(controller.length - len(temp_array))]
                temp_array.extend(zeros)
            else:
                raise SyntaxError('controller.length < len(temp_array)')

            list(map(lambda element: controller.append(element), temp_array))
            # step to semicolon
            self.lexer.next_token()
        else:
            raise SyntaxError(f'expected token <{{> received {self.lexer.token}')

    def pointer_init(self):
        self.lexer.next_token()

        if self.lexer.token is REFERENCE:
            pass

    def skip_to(self, token):
        while self.lexer.token != token:
            self.lexer.next_token()
            if self.lexer.token is EOF:
                raise Exception(f'token not found <{token}>')

    def parse_expression(self, stop_tokens: tuple):
        expression = Calculator()
        ch = None
        star_flag = None

        while True:
            if self.lexer.token is VARIABLE:
                name = self.lexer.name

                if (variable := self.memory.get(NAME, val=name)) is not None:
                    # when parse element is array element
                    if isinstance(variable.value, types_.ARRAY):
                        self.lexer.next_token()
                        if not self.is_WS_before(LSBR):
                            expression.token_storage.append(str(self.parse_array(name, mode='getitem')))
                    # when parse element is variable
                    else:
                        variable = self.memory.get(NAME, val=name)

                        if variable.value is not None:
                            if variable.pointer:
                                if star_flag and ch != ' ':
                                    expression.token_storage.pop()
                                else:
                                    raise SyntaxError('error in pointer construction')

                            expression.token_storage.append(str(variable.value))
                        else:
                            raise SyntaxError(f'variable - <{name}> not defined')
                else:
                    raise Exception(f'variable name - <{name}> not declared')

            elif self.lexer.token is CONSTANT:
                expression.token_storage.append(str(self.lexer.value))

            elif self.lexer.token is LBR:
                expression.token_storage.append('(')

            elif self.lexer.token is RBR:
                expression.token_storage.append(')')

            elif self.lexer.token.__base__ is OPERATOR:
                expression.token_storage.append(self.lexer.token.operator)
                if self.lexer.token is MUL:
                    star_flag = True
                    ch = self.lexer.ch

            elif self.lexer.token is QUESTION_MARK:
                stop_tokens = (QUESTION_MARK,)

            elif self.lexer.token.__base__ is LOGIC:
                expression.token_storage.append(self.lexer.token.operator)

            elif self.lexer.token in stop_tokens:
                break

            else:
                raise SyntaxError(
                    f'unacceptable token - <{self.lexer.token}> in expression expected token {stop_tokens}')

            self.lexer.next_token()

        return expression, stop_tokens

    def calculate_expression(self, stop_tokens=(SEMICOLON,)):
        expression, stop_tokens = self.parse_expression(stop_tokens)

        if QUESTION_MARK in stop_tokens:
            if expression.find_value():
                expression, *_ = self.parse_expression(stop_tokens=(COLON,))
                self.skip_to(token=SEMICOLON)
            else:
                self.skip_to(token=COLON)
                expression, *_ = self.parse_expression(stop_tokens=(SEMICOLON,))

        if RSBR in stop_tokens and not expression.token_storage:
            return 0 # for init unk length array

        return expression.find_value()

    def initialize(self, variable):

        if isinstance(variable.value, types_.ARRAY):
            self.array_init(types_.Controller(variable))
        elif variable.pointer:
            variable.value = self.pointer_init()
        else:
            variable.value = self.calculate_expression()

    def construction(self, name, pointer, mode):
        if self.memory.get(NAME, val=name) is None:
            self.lexer.next_token()
            self.variable = self.type_(name, pointer)

            if self.lexer.token in (COMMA, SEMICOLON, ASSIGNMENT):
                self.memory.append(self.variable)

            elif not self.is_WS_before(LSBR):
                array_res = self.parse_array(name, pointer, mode=mode)
                self.variable.value = array_res
                self.memory.append(self.variable)
        else:
            self.variable = self.memory.last_viewed
            if mode == ANNOUNCEMENT:
                raise SyntaxError(
                    f'redefinition of <{name}> : '
                    f'(new) <{self.type_.__class__.__name__}> *{pointer} '
                    f'(old) <{self.variable.__class__.__name__}> *{self.variable.pointer}')

    def classification(self, mode):
        self.lexer.next_token()

        if self.lexer.token is MUL:
            self.lexer.next_token()
            if not self.is_WS_before(VARIABLE):
                self.construction(name=self.lexer.name, pointer=True, mode=mode)

        elif self.lexer.token is VARIABLE:
            self.construction(name=self.lexer.name, pointer=False, mode=mode)


    def determination(self, mode):
        self.type_ = self.lexer.token
        self.classification(mode)
        # type var = expr;
        if self.lexer.token is ASSIGNMENT:
            self.lexer.next_token()
            self.initialize(self.variable)
        else:
            # type var1, *var2, var3[expr], ...;
            if mode == ANNOUNCEMENT:
                while self.lexer.token is not SEMICOLON:
                    if self.lexer.token is COMMA:
                        self.lexer.next_token()
                    self.classification(mode)
            else:
                raise SyntaxError('cant init more 1 var')

    def parse(self):
        self.lexer.next_token()
        while self.lexer.token != EOF:
            if self.lexer.token in Lexer.TYPES.values():
                self.determination(mode=ANNOUNCEMENT)
            else:
                self.determination(mode=INITIALIZE)

            self.lexer.next_token()

# todo : переписать логику инициализации и обьявления, нужно индентифицировать конструкцию [*]var[[expr]]
if __name__ == '__main__':
    l = Lexer('int a[] = {77 -(91*2)/3}; int c = 33; c = a[0]')
    # l = Lexer('int a[] = {77 -(91*2)/3}; int c = 33;')
    # l = Lexer('int a[4] = {7 - 99*2- (88/3),3, 566.2, 4554-888};')
    p = Parser(l)
    p.parse()
    print(p.memory)
    # print(p.calculate_expression())
