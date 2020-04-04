"""
Defines the grammar of the language according to LL(1)
by indicating the directional characters of each token
"""

from types_ import Integer, Floating
from utilities import *


class START(Checker):

    @cached_property
    def allowed_inheritors(self):
        find_all_sub(Integer, Floating)
        return subclasses


class VARIABLE(Checker):

    @cached_property
    def allowed_inheritors(self):
        return COMMA, LSBR, RSBR, SEMICOLON, ASSIGNMENT, RBRC, ADD, SUB, MUL,\
               DIV, RBR, QUESTION_MARK, COLON, LE, GE, LT, GT, NE, EQ


class CONSTANT(Checker):

    @cached_property
    def allowed_inheritors(self):
        return ADD, SUB, MUL, DIV, SEMICOLON, RBR, COMMA, RBRC, RSBR,\
               QUESTION_MARK, COLON, LE, GE, LT, GT, NE, EQ, RBR


class LOGIC(Checker):

    @cached_property
    def allowed_inheritors(self):
        return LBR, VARIABLE, CONSTANT, MUL


class LT(LOGIC):

    operator = '<'


class GT(LOGIC):

    operator = '>'


class LE(LOGIC):

    operator = '<='


class GE(LOGIC):

    operator = '>='


class EQ(LOGIC):

    operator = '=='


class NE(LOGIC):

    operator = '!='


class NOT(LOGIC):

    operator = '!'


class QUESTION_MARK(LOGIC):

    operator = '?'


class COLON(LOGIC):

    operator = ':'


class OR(LOGIC):

    operator = '||'


class AND(LOGIC):

    operator = '&&'


class XOR(LOGIC):

    operator = '^'


class SEMICOLON(Checker):

    @cached_property
    def allowed_inheritors(self):
        find_all_sub(Integer, Floating)
        return VARIABLE, LBR, EOF, *subclasses


class OPERATOR(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT, LBR, ADD, SUB


class ADD(OPERATOR):

    operator = '+'


class SUB(OPERATOR):

    operator = '-'


class MUL(OPERATOR):

    operator = '*'


class DIV(OPERATOR):

    operator = '/'


class REFERENCE(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT


class ASSIGNMENT(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT, REFERENCE, LBR, MUL, LBRC, ADD, MUL, DIV, SUB


class COMMA(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT, MUL, RBRC, ADD, SUB, MUL, DIV


# (
class LBR(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT, LBR, REFERENCE, MUL


# )
class RBR(Checker):

    @cached_property
    def allowed_inheritors(self):
        return ADD, SUB, MUL, DIV, SEMICOLON, ASSIGNMENT, RBR, LE, GE, LT, GT, NE, EQ, QUESTION_MARK, COLON, RSBR,  COMMA


# [
class LSBR(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT, MUL, RSBR


# ]
class RSBR(Checker):

    @cached_property
    def allowed_inheritors(self):
        return ASSIGNMENT, LE, GE, LT, GT, NE, EQ, SEMICOLON, QUESTION_MARK, COMMA


# {
class LBRC(Checker):

    @cached_property
    def allowed_inheritors(self):
        return VARIABLE, CONSTANT, MUL, LBR, ADD, SUB


# }
class RBRC(Checker):

    @cached_property
    def allowed_inheritors(self):
        return SEMICOLON,


# no implementation
class IF(Checker):
    pass


# no implementation
class ELSE(Checker):
    pass


# no implementation
class WHILE(Checker):
    pass


class EOF(Checker):

    @cached_property
    def allowed_inheritors(self):
        return None,