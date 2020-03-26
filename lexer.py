import types_
from grammar import *


class Lexer:

    WORDS = {'if': IF,
             'else': ELSE,
             'while': WHILE}

    TYPES = {'char': types_.CHAR,
             'short': types_.SHORT,
             'int': types_.INT,
             'long': types_.LONG,
             'float': types_.FLOAT,
             'double': types_.DOUBLE}

    SYMBOLS = {',': COMMA,
               '=': ASSIGNMENT,
               ';': SEMICOLON,
               '(': LBR,
               ')': RBR,
               '+': ADD,
               '-': SUB,
               '*': MUL,
               '/': DIV,
               '?': QUESTION_MARK,
               ':': COLON,
               '<': LT,
               '>': GT,
               '!': NOT,
               '<=': LE,
               '>=': GE,
               '==': EQ,
               '!=': NE,
               '[': LSBR,
               ']': RSBR,
               '{': LBRC,
               '}': RBRC,
               '&': REFERENCE,
               '^': XOR,
               '||': OR,
               '&&': AND}

    ch = ' '  # assume the first char is a space (not EOF)

    def __init__(self, code):
        self.code = code
        self.iterator = iter(code)
        self.token = START
        self.index = -1  # because first ch is a space
        self.line = 0

    def _next_char(self):
        try:
            if self.ch == '\n':
                self.line += 1
                self.index = -1

            self.ch = next(self.iterator)
            self.index += 1
        except StopIteration:
            self.ch = ''

    def _recognize_symbol(self):
        ch = self.ch

        if self.ch in ('<', '>'):
            self._next_char()
            if self.ch == '=':
                self.token = LE if ch == '<' else GE
                self._next_char()
            else:
                self.token = LT if ch == '<' else GT

        elif self.ch == '=':
            self._next_char()
            if self.ch == '=':
                self.token = EQ
                self._next_char()
            else:
                self.token = ASSIGNMENT

        elif self.ch == '!':
            self._next_char()
            if self.ch == '=':
                self.token = NE
                self._next_char()
            else:
                self.token = NOT

        elif self.ch == '|':
            self._next_char()
            if self.ch == '|':
                self.token = OR
                self._next_char()
            else:
                raise SyntaxError(f'unknown symbol <|{self.ch}>')

        elif self.ch == '&':
            self._next_char()
            if self.ch == '&':
                self.token = AND
                self._next_char()
            else:
                self.token = REFERENCE
        else:
            self.token = Lexer.SYMBOLS[self.ch]
            self._next_char()

    def _recognize_number(self):
        temp_value = ''
        while self.ch.isdigit() or self.ch == '.':
            temp_value += self.ch
            self._next_char()
            if self.ch.isalpha():
                raise SyntaxError(f'numbers cannot contain letters <{self.ch}> error on the index - {self.index}')

        self.value = float(temp_value) if '.' in temp_value else int(temp_value)
        self.token = CONSTANT

    def _recognize_word(self):
        temp_var_name = ''
        while self.ch.isalnum() or self.ch == '_':
            temp_var_name += self.ch
            self._next_char()

        if temp_var_name in Lexer.WORDS:
            self.token = Lexer.WORDS[temp_var_name]
        elif temp_var_name in Lexer.TYPES:
            self.token = Lexer.TYPES[temp_var_name]
        else:
            self.token = VARIABLE
            self.name = temp_var_name

    @staticmethod
    def check_grammar(prev_token, curr_token):
        if prev_token in Lexer.TYPES.values():
            prev_token = prev_token(virtual_mode=True)
        else:
            prev_token = prev_token()
        prev_token.inheritor = curr_token

    def next_token(self):
        prev_token = self.token
        self.name = None
        self.value = None
        self.token = None
        while self.token is None:
            if self.ch.isspace():
                self._next_char()
            elif self.ch in Lexer.SYMBOLS:
                self._recognize_symbol()
            elif self.ch.isdigit():
                self._recognize_number()
            elif self.ch.isalpha() or self.ch == '_':
                self._recognize_word()
            elif len(self.ch) == 0:
                self.token = EOF
            else:
                raise SyntaxError(f'unexpected symbol <{self.ch}>')

            if self.token is not None:
                self.check_grammar(prev_token=prev_token, curr_token=self.token)