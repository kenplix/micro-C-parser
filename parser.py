from lexer import *
from expression_handler.calculator import Calculator

ID = 'id'
NAME = 'name'

ANNOUNCEMENT = 'announcement'
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
        value = self.calculate_expression(stop_token=RSBR)  # in [...]
        return define_action(value)

    #todo: есть массив нулевой длинны, создавать его заново когда длинна известна
    def array_init(self):
        psevdo_array = []

        self.lexer.next_token()
        if self.lexer.token is LBRC:
            while self.lexer.token is not RBRC:
                self.lexer.next_token()
                psevdo_array.append(self.calculate_expression(stop_token=COMMA))

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

    def parse_expression(self, stop_token):
        expression = Calculator()
        ch = None
        star_flag = None

        while self.lexer.token is not stop_token:
            self.lexer.next_token()

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
                stop_token = QUESTION_MARK

            elif self.lexer.token.__base__ is LOGIC:
                expression.token_storage.append(self.lexer.token.operator)

            elif self.lexer.token is not stop_token:
                raise SyntaxError(
                    f'unacceptable token - <{self.lexer.token}> in expression expected token <{stop_token}>')

        return expression, stop_token

    def calculate_expression(self, stop_token=SEMICOLON):
        expression, stop_token = self.parse_expression(stop_token)

        if stop_token is QUESTION_MARK:
            if expression.find_value():
                expression, *_ = self.parse_expression(stop_token=COLON)
                self.skip_to(token=SEMICOLON)
            else:
                self.skip_to(token=COLON)
                expression, *_ = self.parse_expression(stop_token=SEMICOLON)

        if stop_token is RSBR and not expression.token_storage:
            return 0 # for init unk length array

        return expression.find_value()

    def initialize(self, variable):
        if variable is None:
            raise SyntaxError('not ann')

        if isinstance(variable.value, types_.ARRAY):
            variable.value = self.array_init()
        elif variable.pointer:
            variable.value = self.pointer_init()
        else:
            variable.value = self.calculate_expression()

    def construction(self, type_, name, pointer):
        if self.memory.get(NAME, val=name) is None:
            self.lexer.next_token()
            variable = type_(name, pointer)

            if self.lexer.token in (COMMA, SEMICOLON, ASSIGNMENT):
                self.memory.append(variable)

            elif not self.is_WS_before(LSBR):
                array = self.parse_array(name, pointer, mode=ANNOUNCEMENT)
                variable.value = array
                self.memory.append(variable)
        else:
            variable = self.memory.last_viewed
            raise SyntaxError(
                f'redefinition of <{name}> : '
                f'(new) <{type_.__class__.__name__}> *{pointer} '
                f'(old) <{variable.__class__.__name__}> *{variable.pointer}')

    def classification(self, type_):
        self.lexer.next_token()

        if self.lexer.token is MUL:
            self.lexer.next_token()
            if not self.is_WS_before(VARIABLE):
                self.construction(type_, name=self.lexer.name, pointer=True)

        elif self.lexer.token is VARIABLE:
            self.construction(type_, name=self.lexer.name, pointer=False)


    def announcement(self, type_):
        self.classification(type_)
        # type var = expr;
        if self.lexer.token is ASSIGNMENT:
            self.initialize(variable=self.memory[-1])
        else:
            # type var1, *var2, var3[expr], ...;
            while self.lexer.token is not SEMICOLON:
                if self.lexer.token is COMMA:
                    self.lexer.next_token()
                self.classification(type_)

    def parse(self):
        self.lexer.next_token()
        while self.lexer.token != EOF:
            if self.lexer.token in Lexer.TYPES.values():
                self.announcement(type_=self.lexer.token)
            else:
                self.initialize(variable=self.memory.get(NAME, val=self.lexer.name))
            self.lexer.next_token()


if __name__ == '__main__':
    l = Lexer('int a[6];')
    # l = Lexer('5+ 3- (99 * 4),]')
    p = Parser(l)
    p.parse()
    print(p.memory)
    # print(p.calculate_expression())
