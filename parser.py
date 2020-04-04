#!/usr/bin/python3
# -*- coding: UTF-8 -*-

from lexer import *
from expression_handler.calculator import Calculator

_ANNOUNCEMENT = 'announcement'
_INITIALIZE = 'initialize'

_GETITEM = 'getitem'
_SETITEM = 'setitem'
_REFERENCE = 'reference'


class Parser:

    def __init__(self, lexer) -> None:
        self._lexer = lexer
        self.memory = types_.Memory()

        self.token = None
        self.index = None

    def _step(self) -> None:
        self._lexer.next_token()
        self.ch = self._lexer.ch
        self.name = self._lexer.name
        self.value = self._lexer.value
        self.token = self._lexer.token

    # arr[<expression>] = {<expression>, <expression>, ..., <expression>}
    def _parse_array(self, name: str, pointer: bool = False, *, mode: str):
        """
        Defines actions with arrays
        """
        def define_action(dimension: int):
            if isinstance(dimension, int):
                if mode == _ANNOUNCEMENT:
                    self._step()
                    return types_.ARRAY(length=value)

                elif mode == _GETITEM:
                    variable = self.memory.get_by_name(name, throw=True)
                    return variable.value[dimension]

                elif mode == _SETITEM:
                    self._step()
                    self.memory.get_by_name(name, throw=True)
                    return dimension

                elif mode == _REFERENCE:
                    start = self.memory.get_by_name(name, throw=True)
                    return start.id + dimension
            else:
                raise SyntaxError('Define_action type must be <INTEGER> and not <FRACTIONAL>')

        if pointer:
            raise SyntaxError('Not implemented feature')

        self._step()
        value = self.calculate_expression(stop_tokens=(RSBR,))  # in [...]
        return define_action(value)

    def _set_array_elem(self, controller: types_.Controller) -> None:
        controller.setitem(self.calculate_expression(), self.index)

    def _array_init(self, controller: types_.Controller) -> None:
        temp_array = []
        if self.token is LBRC:
            self._step()
            while True:
                temp_array.append(self.calculate_expression(stop_tokens=(COMMA, RBRC)))
                if self.token is RBRC:
                    break
                self._step()

            if controller.length == 0:
                array = types_.ARRAY(length=len(temp_array))
                variable = controller.variable

                variable.value = array
                controller = types_.Controller(variable)

            elif controller.length >= len(temp_array):
                zeros = [0 for _ in range(controller.length - len(temp_array))]
                temp_array.extend(zeros)
            else:
                raise SyntaxError('Invalid array length')

            list(map(lambda element: controller.append(element), temp_array))
            self._step()
        else:
            raise SyntaxError(f'Unacceptable token {self.token}')

    def _pointer_init(self):
        if self.token is REFERENCE:
            self._step()
            if self.token is VARIABLE:
                variable = self.memory.get_by_name(self.name, throw=True)
                self._step()

                if self.token is SEMICOLON:
                    return variable.__class__, variable.id

                elif self.token is LSBR:
                    id_ = self._parse_array(variable.name, variable.pointer, mode=_REFERENCE)
                    self._step()
                    return variable.__class__, id_

        elif self.token is VARIABLE:
            variable = self.memory.get_by_name(self.name, throw=True)
            if variable.pointer:
                self._step()
                return variable.__class__, variable.reference
            else:
                raise SyntaxError(f'<{variable.name}> not a pointer variable')
        else:
            raise SyntaxError(f'Unacceptable token {self.token}')

    def _scroller(self, token) -> None:
        while self.token != token:
            self._step()
            if self.token is EOF:
                raise SyntaxError(f'Token not found {token}')

    def _expression_parser(self, stop_tokens: tuple):
        expression = Calculator()
        ch = None
        star_flag = None

        while True:
            if self.token is VARIABLE:
                name = self.name
                variable = self.memory.get_by_name(name, throw=True)

                if isinstance(variable.value, types_.ARRAY):
                    self._step()
                    if self.token is LSBR:
                        expression.token_storage.append(str(self._parse_array(name, mode=_GETITEM)))
                else:
                    if variable.pointer:
                        if star_flag and ch != ' ':
                            expression.token_storage.pop()
                            id_ = int(variable.reference)
                            value = str(self.memory.get_by_id(id_).value[id_])
                            expression.token_storage.append(value)
                        else:
                            raise SyntaxError('Error in pointer construction')
                    else:
                        if variable.value is not None:
                            expression.token_storage.append(str(variable.value))
                        else:
                            raise SyntaxError(f'Variable <{name}> not defined')

            elif self.token is CONSTANT:
                expression.token_storage.append(str(self.value))

            elif self.token is LBR:
                expression.token_storage.append('(')

            elif self.token is RBR:
                expression.token_storage.append(')')

            elif self.token.__base__ is OPERATOR:
                expression.token_storage.append(self.token.operator)
                if self.token is MUL:
                    star_flag = True
                    ch = self.ch

            elif self.token is QUESTION_MARK:
                stop_tokens = (QUESTION_MARK,)

            elif self.token.__base__ is LOGIC:
                expression.token_storage.append(self.token.operator)

            elif self.token in stop_tokens:
                break

            else:
                raise SyntaxError(f'Unacceptable token {self.token}')

            self._step()

        return expression, stop_tokens

    def calculate_expression(self, stop_tokens=(SEMICOLON,)):
        expression, stop_tokens = self._expression_parser(stop_tokens)

        if QUESTION_MARK in stop_tokens:
            if expression.find_value():
                expression, *_ = self._expression_parser(stop_tokens=(COLON,))
                self._scroller(token=SEMICOLON)
            else:
                self._scroller(token=COLON)
                expression, *_ = self._expression_parser(stop_tokens=(SEMICOLON,))

        if RSBR in stop_tokens and not expression.token_storage:
            return 0  # to initialize an array of undeclared lengths

        return expression.find_value()

    def _initializer(self, variable) -> None:
        """
        Defines initialization mode
        """
        if isinstance(variable.value, types_.ARRAY):
            if self.index is not None:
                self._set_array_elem(types_.Controller(variable))
            else:
                self._array_init(types_.Controller(variable))

        elif variable.pointer:
            type_, reference = self._pointer_init()
            if variable.__class__ is not type_:
                raise SyntaxError(f'Different types {variable.__class__} and {type_}')
            variable.reference = reference

        else:
            variable.value = self.calculate_expression()

    def _constructor(self, name: str, pointer: bool, mode: str) -> None:
        """
        Prepares collected data
        """
        if self.memory.get_by_name(name) is None:
            if mode == _INITIALIZE:
                raise SyntaxError(f'The variable <{name}> has not been declared')

            self._step()
            self.variable = self.type_(name, pointer)

            if self.token in (COMMA, SEMICOLON, ASSIGNMENT):
                self.memory.append(self.variable)

            elif self.token is LSBR:
                array = self._parse_array(name, pointer, mode=mode)
                self.variable.value = array
                self.memory.append(self.variable)
        else:
            if mode == _ANNOUNCEMENT:
                raise SyntaxError(f'Redefinition of <{name}>')

            self.variable = self.memory.last_viewed
            self._step()

            if self.token not in (ASSIGNMENT, LSBR):
                raise SyntaxError(f'Unacceptable token {self.token}')
            elif self.token is LSBR:
                self.index = self._parse_array(name, pointer, mode=_SETITEM)

    def _classifier(self, mode: str) -> None:
        """
        Defines a part: *var or var
        """
        if mode == _ANNOUNCEMENT:
            self._step()

        if self.token is MUL:
            self._step()
            if self.token is VARIABLE:
                self._constructor(name=self.name, pointer=True, mode=mode)

        elif self.token is VARIABLE:
            self._constructor(name=self.name, pointer=False, mode=mode)

    def _determinator(self, mode: str) -> None:
        """
        Determines the next step by set mode

        Modes: _ANNOUNCEMENT, _INITIALIZE

        In _ANNOUNCEMENT parses lines similar to:
        * type var1, *var2, var3[<expr>], ...;

        In _INITIALIZE parses lines similar to:
        * type var = ...;
        * type var[] = ...;
        After the assignment operator, control passes to the initializer,
        which parses the expression in accordance with the declaration
        """
        if mode == _ANNOUNCEMENT:
            self.type_ = self.token

        self._classifier(mode)
        if self.token is ASSIGNMENT:
            self._step()
            self._initializer(self.variable)
        else:
            if mode == _ANNOUNCEMENT:
                while self.token is not SEMICOLON:
                    if self.token is COMMA:
                        self._step()
                    self._classifier(mode)
            else:
                raise SyntaxError('You cannot initialize more than one variable in a declaration line')

    def parse(self) -> None:
        self._step()
        while self.token != EOF:
            if self.token in Lexer.TYPES.values():
                self._determinator(mode=_ANNOUNCEMENT)
            else:
                self._determinator(mode=_INITIALIZE)

            self._step()


if __name__ == '__main__':
    L = Lexer('int a [] = {77 -(91*2)/3, 5}; int *q = &a[1]; a[0] = *q + 2;')
    p = Parser(L)
    p.parse()
    print(p.memory)

    L1 = Lexer('int a[] = {77 -(91*2)/3}; int c = 33;')
    p1 = Parser(L1)
    p1.parse()
    print(p1.memory)

    L2 = Lexer('int a[4] = {7 - 99*2- (88/3),3, 566.2, 4554-888};')
    p2 = Parser(L2)
    p2.parse()
    print(p2.memory)