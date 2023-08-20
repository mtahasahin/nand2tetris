import os
import sys


VOID = "void"
CLASS = "class"
RETURN = "return"
DO = "do"
WHILE = "while"
IF = "if"
LET = "let"
ELSE = "else"
NOT = "not"
EQ = "eq"
GT = "gt"
LT = "lt"
OR = "or"
AND = "and"
SUB = "sub"
ADD = "add"
NEG = "neg"
STRING_CONST = "STRING_CONST"
INTEGER_CONST = "INTEGER_CONST"
TEMP = "temp"
NULL = "null"
FALSE = "false"
TRUE = "true"
CONSTANT = "constant"
KEYWORD = "KEYWORD"
THAT = "that"
POINTER = "pointer"
SYMBOL = "SYMBOL"
BOOLEAN = "boolean"
CHAR = "char"
INT = "int"
IDENTIFIER = "IDENTIFIER"
VAR = "var"
LOCAL = "local"
ARG = "arg"
ARGUMENT = "ARGUMENT"
STATIC = "static"
FIELD = "field"
THIS = "this"
NAME = "name"
TYPE = "type"
KIND = "kind"
INDEX = "index"
METHOD = "method"
CONSTRUCTOR = "constructor"
FUNCTION = "function"


class SymbolTable:
    def __init__(self):
        self.class_symbol_table = {}
        self.subroutine_symbol_table = {}
        self.subroutine_type = None
        self.index_map = {}

    def _get_index(self, kind):
        index = self.index_map.get(kind, -1) + 1
        self.index_map[kind] = index
        return index

    def _get_info(self, name, key):
        symbol_table = self.subroutine_symbol_table if name in self.subroutine_symbol_table else self.class_symbol_table
        return symbol_table.get(name, {}).get(key)

    def start_subroutine(self, subroutine_type):
        self.subroutine_symbol_table = {}
        self.index_map[VAR] = -1
        self.index_map[ARG] = -1
        self.subroutine_type = subroutine_type

    def define(self, name, type, kind):
        symbol_table = self.class_symbol_table if kind in [STATIC, FIELD] else self.subroutine_symbol_table
        index = self._get_index(kind)
        symbol_table[name] = {NAME: name, TYPE: type, KIND: kind, INDEX: index}

    def var_count(self, kind):
        return self.index_map[kind] + 1

    def kind_of(self, name):
        return self._get_info(name, KIND)

    def type_of(self, name):
        return self._get_info(name, TYPE)

    def index_of(self, name):
        if self.subroutine_type == METHOD and self.kind_of(name) == ARG:
            return self._get_info(name, INDEX) + 1
        else:
            return self._get_info(name, INDEX)


class VMWriter:
    def __init__(self, output_file):
        self.output_file = output_file

    def write_push(self, segment, value):
        self.output_file.write(f"push {segment.lower()} {value}\n")

    def write_pop(self, segment, value):
        self.output_file.write(f"pop {segment.lower()} {value}\n")

    def write_arithmetic(self, command):
        self.output_file.write(f"{command.lower()}\n")

    def write_label(self, label):
        self.output_file.write(f"label {label}\n")

    def write_goto(self, label):
        self.output_file.write(f"goto {label}\n")

    def write_if(self, label):
        self.output_file.write(f"if-goto {label}\n")

    def write_call(self, name, n_args):
        self.output_file.write(f"call {name} {n_args}\n")

    def write_function(self, name, n_locals):
        self.output_file.write(f"function {name} {n_locals}\n")

    def write_return(self):
        self.output_file.write(f"return\n")


class JackTokenizer:
    def __init__(self, code):
        self.code = code
        self.current_token = None
        self.current_token_type = None
        self.index = 0

    def has_more_tokens(self):
        return self.index < len(self.code)

    def peek_next_token(self):
        index = self.index
        token = self.current_token
        token_type = self.current_token_type
        self.advance()
        next_token = self.current_token
        next_token_type = self.current_token_type
        self.index = index
        self.current_token = token
        self.current_token_type = token_type
        return next_token, next_token_type

    def advance(self):
        start_index = self.index
        c = self.__advance_character()
        if c in ["{", "}", "(", ")", "[", "]", ".", ",", ";", "+", "-", "*", "&", "|", "<", ">", "=", "~"]:
            self.__set_token(c, SYMBOL)
        elif c == "/":
            if self.__match("/"):
                while self.__peek() != "\n" and not self.__is_at_end():
                    self.__advance_character()
                self.__set_token(None, None)
                self.advance()
            elif self.__match("*"):
                while not (self.__peek() == "*" and self.__peek_next() == "/"):
                    self.__advance_character()
                self.__advance_character()
                self.__advance_character()
                self.__set_token(None, None)
                self.advance()
            else:
                self.__set_token(c, SYMBOL)
        elif c in [" ", "\r", "\t", "\n"]:
            self.__set_token(None, None)
            self.advance()
        elif c == "\"":
            while self.__peek() != "\"" and not self.__is_at_end():
                self.__advance_character()

            if self.__is_at_end():
                raise RuntimeError("Unterminated string")

            self.__advance_character()

            val = self.code[start_index + 1: self.index - 1]
            self.__set_token(val, STRING_CONST)
        elif c.isdigit():
            while self.__peek().isdigit():
                self.__advance_character()

            val = self.code[start_index: self.index]
            self.__set_token(val, INTEGER_CONST)
        elif c.isalpha() or c == '_':
            while self.__peek().isalnum() or self.__peek() == "_":
                self.__advance_character()

            val = self.code[start_index: self.index]
            is_keyword = val in [CLASS, CONSTRUCTOR, FUNCTION, METHOD, FIELD, STATIC, VAR, INT, CHAR,
                                 BOOLEAN, VOID, TRUE, FALSE, NULL, THIS, LET, DO, IF, ELSE, WHILE,
                                 RETURN]
            self.__set_token(val, KEYWORD if is_keyword else IDENTIFIER)

    def token_type(self):
        return self.current_token_type

    def key_word(self):
        return self.current_token

    def symbol(self):
        return self.current_token

    def identifier(self):
        return self.current_token

    def int_val(self):
        return self.current_token

    def string_val(self):
        return self.current_token

    def __is_at_end(self):
        return not self.has_more_tokens()

    def __match(self, expected):
        if not self.has_more_tokens():
            return False

        if self.code[self.index] != expected:
            return False

        self.index += 1
        return True

    def __peek(self):
        if self.__is_at_end():
            return "\0"
        return self.code[self.index]

    def __peek_next(self):
        if self.__is_at_end():
            return "\0"
        return self.code[self.index + 1]

    def __set_token(self, c, type):
        self.current_token = c
        self.current_token_type = type

    def __advance_character(self):
        if self.__is_at_end():
            return "\0"
        c = self.code[self.index]
        self.index += 1
        return c


def kts(kind):
    if kind == STATIC:
        return STATIC
    if kind == ARG:
        return ARGUMENT
    if kind == VAR:
        return LOCAL
    if kind == FIELD:
        return THIS


class CompilationEngine:
    def __init__(self, input_file, output_file):
        self.output_file = output_file
        self.tokenizer = JackTokenizer(input_file)
        self.vm_writer = VMWriter(output_file)
        self.symbol_table = SymbolTable()
        self.class_name = ""
        self.lbl_count = 0

    def _get_next_lbl(self):
        self.lbl_count += 1
        return "lbl" + str(self.lbl_count)

    def compile_class(self):
        self.tokenizer.advance()
        self.tokenizer.advance()
        self.compile_class_name()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "{":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        while self.tokenizer.token_type() == KEYWORD and self.tokenizer.key_word() in [STATIC, FIELD]:
            self.compile_class_var_dec()

        while self.tokenizer.token_type() == KEYWORD and self.tokenizer.key_word() in [CONSTRUCTOR, FUNCTION, METHOD]:
            self.compile_subroutine_dec()

        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "}":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_class_name(self):
        if self.tokenizer.token_type() == IDENTIFIER:
            self.class_name = self.tokenizer.identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_class_var_dec(self):
        kind = self.tokenizer.key_word()
        self.tokenizer.advance()
        type = self.compile_type()
        name = self.compile_varname()
        self.symbol_table.define(name, type, kind)
        while self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ",":
            self.tokenizer.advance()
            name = self.compile_varname()
            self.symbol_table.define(name, type, kind)
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ";":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_subroutine_dec(self):
        subroutine_type = self.tokenizer.key_word()
        self.symbol_table.start_subroutine(subroutine_type)

        self.tokenizer.advance()
        self.tokenizer.advance()

        subroutine_name = self.compile_subroutine_name()

        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "(":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        self.compile_parameter_list()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        # subroutine body
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "{":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        while self.tokenizer.token_type() == KEYWORD and self.tokenizer.key_word() == VAR:
            self.compile_var_dec()

        n_local_variables = self.symbol_table.var_count(VAR)
        self.vm_writer.write_function(self.class_name + "." + subroutine_name, n_local_variables)
        if subroutine_type == METHOD:
            self.vm_writer.write_push(ARGUMENT, 0)
            self.vm_writer.write_pop(POINTER, 0)
        elif subroutine_type == CONSTRUCTOR:
            self.vm_writer.write_push(CONSTANT, self.symbol_table.var_count(FIELD))
            self.vm_writer.write_call("Memory.alloc", 1)
            self.vm_writer.write_pop(POINTER, 0)

        self.compile_statements()

        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "}":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_statements(self):
        while self.tokenizer.token_type() == KEYWORD:
            if self.tokenizer.key_word() == LET:
                self.compile_let_statement()
            elif self.tokenizer.key_word() == IF:
                self.compile_if_statement()
            elif self.tokenizer.key_word() == WHILE:
                self.compile_while_statement()
            elif self.tokenizer.key_word() == DO:
                self.compile_do_statement()
            elif self.tokenizer.key_word() == RETURN:
                self.compile_return_statement()

    def compile_let_statement(self):
        self.tokenizer.advance()
        name = self.compile_varname()
        if not self.symbol_table.type_of(name):
            raise RuntimeError()
        kind = self.symbol_table.kind_of(name)
        index = self.symbol_table.index_of(name)

        array = False
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "[":
            array = True
            self.vm_writer.write_push(kts(kind), index)
            self.tokenizer.advance()
            self.compile_expression()  # pushes value inside brackets
            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "]":
                self.tokenizer.advance()
            else:
                raise RuntimeError()
            self.vm_writer.write_arithmetic(ADD)
            self.vm_writer.write_pop(TEMP, 1)
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "=":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_expression()  # pushes right side value
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ";":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if array:
            self.vm_writer.write_push(TEMP, 1)
            self.vm_writer.write_pop(POINTER, 1)
            self.vm_writer.write_pop(THAT, 0)
        else:
            self.vm_writer.write_pop(kts(kind), index)

    def compile_if_statement(self):
        label1 = self._get_next_lbl()
        label2 = self._get_next_lbl()
        self.tokenizer.advance()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "(":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_expression()
        self.vm_writer.write_arithmetic(NOT)
        self.vm_writer.write_if(label1)
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "{":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_statements()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "}":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.vm_writer.write_goto(label2)
        self.vm_writer.write_label(label1)
        if self.tokenizer.token_type() == KEYWORD and self.tokenizer.key_word() == ELSE:
            self.tokenizer.advance()
            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "{":
                self.tokenizer.advance()
            else:
                raise RuntimeError()
            self.compile_statements()
            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "}":
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        self.vm_writer.write_label(label2)

    def compile_while_statement(self):
        label1 = self._get_next_lbl()
        label2 = self._get_next_lbl()
        self.vm_writer.write_label(label1)

        self.tokenizer.advance()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "(":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_expression()
        self.vm_writer.write_arithmetic(NOT)
        self.vm_writer.write_if(label2)
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "{":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_statements()
        self.vm_writer.write_goto(label1)
        self.vm_writer.write_label(label2)
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "}":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_do_statement(self):
        self.tokenizer.advance()
        self.compile_subroutine_call()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ";":
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.vm_writer.write_pop(TEMP, 0)

    def compile_return_statement(self):
        self.tokenizer.advance()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ";":
            self.tokenizer.advance()
            self.vm_writer.write_push(CONSTANT, 0)
        else:
            self.compile_expression()
            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ";":
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        self.vm_writer.write_return()

    def compile_expression(self):
        self.compile_term()
        while self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<",
                                                                                      ">", "="]:
            symbol = self.tokenizer.symbol()
            self.tokenizer.advance()
            self.compile_term()
            if symbol == "+":
                self.vm_writer.write_arithmetic(ADD)
            elif symbol == "-":
                self.vm_writer.write_arithmetic(SUB)
            elif symbol == "*":
                self.vm_writer.write_call("Math.multiply", 2)
            elif symbol == "/":
                self.vm_writer.write_call("Math.divide", 2)
            elif symbol == "&":
                self.vm_writer.write_arithmetic(AND)
            elif symbol == "|":
                self.vm_writer.write_arithmetic(OR)
            elif symbol == "<":
                self.vm_writer.write_arithmetic(LT)
            elif symbol == ">":
                self.vm_writer.write_arithmetic(GT)
            elif symbol == "=":
                self.vm_writer.write_arithmetic(EQ)

    def compile_term(self):
        if self.tokenizer.token_type() == INTEGER_CONST:
            self.vm_writer.write_push(CONSTANT, self.tokenizer.int_val())
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == STRING_CONST:
            val = self.tokenizer.identifier()
            self.vm_writer.write_push(CONSTANT, len(val))
            self.vm_writer.write_call("String.new", 1)
            self.vm_writer.write_pop(TEMP, 0)
            for char in val:
                self.vm_writer.write_push(TEMP, 0)
                self.vm_writer.write_push(CONSTANT, ord(char))
                self.vm_writer.write_call("String.appendChar", 2)
                self.vm_writer.write_pop(TEMP, 0)
            self.vm_writer.write_push(TEMP, 0)
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == KEYWORD and self.tokenizer.key_word() in [TRUE, FALSE, NULL, THIS]:
            if self.tokenizer.key_word() in [FALSE, NULL]:
                self.vm_writer.write_push(CONSTANT, 0)
            if self.tokenizer.key_word() == TRUE:
                self.vm_writer.write_push(CONSTANT, 1)
                self.vm_writer.write_arithmetic(NEG)
            if self.tokenizer.key_word() == THIS:
                self.vm_writer.write_push(POINTER, 0)

            self.tokenizer.advance()
        elif self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "(":
            self.tokenizer.advance()
            self.compile_expression()  # pushes the value
            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        elif self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() in ["-", "~"]:
            method = NEG if self.tokenizer.symbol() == "-" else "not"
            self.tokenizer.advance()
            self.compile_term()  # pushes the value
            self.vm_writer.write_arithmetic(method)

        elif self.tokenizer.token_type() == IDENTIFIER:
            if self.tokenizer.peek_next_token()[0] == "[":
                name = self.compile_varname()
                kind = self.symbol_table.kind_of(name)
                index = self.symbol_table.index_of(name)
                self.vm_writer.write_push(kts(kind), index)
                if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "[":
                    self.tokenizer.advance()
                else:
                    raise RuntimeError()
                self.compile_expression()  # pushed value inside bracket
                if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "]":
                    self.tokenizer.advance()
                else:
                    raise RuntimeError()
                self.vm_writer.write_arithmetic(ADD)
                self.vm_writer.write_pop(POINTER, 1)
                self.vm_writer.write_push(THAT, 0)

            elif self.tokenizer.peek_next_token()[0] in ["(", "."]:
                self.compile_subroutine_call()
            else:
                name = self.compile_varname()
                kind = self.symbol_table.kind_of(name)
                index = self.symbol_table.index_of(name)
                self.vm_writer.write_push(kts(kind), index)
        else:
            raise RuntimeError()

    def compile_expression_list(self):
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
            return 0
        self.compile_expression()
        i = 1
        while self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ",":
            i += 1
            self.tokenizer.advance()
            self.compile_expression()
        return i

    def compile_subroutine_call(self):
        if self.tokenizer.token_type() == IDENTIFIER:
            identifier_name = self.tokenizer.identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "(":
            self.tokenizer.advance()
            self.vm_writer.write_push(POINTER, 0)
            n_args = self.compile_expression_list()
            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
                self.tokenizer.advance()
            else:
                raise RuntimeError()
            self.vm_writer.write_call(self.class_name + "." + identifier_name, n_args + 1)
        elif self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ".":
            self.tokenizer.advance()
            method_name = self.compile_subroutine_name()
            is_object = self.symbol_table.kind_of(identifier_name) is not None

            if is_object:
                self.vm_writer.write_push(kts(self.symbol_table.kind_of(identifier_name)),
                                          self.symbol_table.index_of(identifier_name))

            if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == "(":
                self.tokenizer.advance()
                n_args = self.compile_expression_list()
                if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
                    self.tokenizer.advance()
                else:
                    raise RuntimeError()
                if is_object:
                    type = self.symbol_table.type_of(identifier_name)
                    self.vm_writer.write_call(type + "." + method_name, n_args + 1)
                else:
                    self.vm_writer.write_call(identifier_name + "." + method_name, n_args)

            else:
                raise RuntimeError()
        else:
            raise RuntimeError()

    def compile_var_dec(self):
        self.tokenizer.advance()
        type = self.compile_type()
        name = self.compile_varname()
        self.symbol_table.define(name, type, VAR)
        while self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ",":
            self.tokenizer.advance()
            name = self.compile_varname()
            self.symbol_table.define(name, type, VAR)

        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ";":
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_parameter_list(self):
        if self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ")":
            return

        type = self.compile_type()
        name = self.compile_varname()
        self.symbol_table.define(name, type, ARG)
        while self.tokenizer.token_type() == SYMBOL and self.tokenizer.symbol() == ",":
            self.tokenizer.advance()
            type = self.compile_type()
            name = self.compile_varname()
            self.symbol_table.define(name, type, ARG)

    def compile_subroutine_name(self):
        if self.tokenizer.token_type() == IDENTIFIER:
            identifier = self.tokenizer.identifier()
            self.tokenizer.advance()
            return identifier
        else:
            raise RuntimeError()

    def compile_type(self):
        if self.tokenizer.token_type() == KEYWORD and self.tokenizer.key_word() in [INT, CHAR, BOOLEAN]:
            type = self.tokenizer.key_word()
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == IDENTIFIER:
            type = self.tokenizer.identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        return type

    def compile_varname(self):
        if self.tokenizer.token_type() == IDENTIFIER:
            identifier = self.tokenizer.identifier()
            self.tokenizer.advance()
            return identifier
        else:
            raise RuntimeError()


if __name__ == '__main__':
    path = sys.argv[1]
    file_list = []
    if os.path.isfile(path):
        file_list.insert(0, path)
    elif os.path.isdir(path):
        for filename in os.listdir(path):
            if filename.endswith(".jack"):
                file_list.insert(0, os.path.join(path, filename))

    for filename in file_list:
        current_filename = os.path.splitext(filename)[0]
        with open(filename, "r") as file:
            code = file.read()
            output_filename = current_filename + ".vm"
            with open(output_filename, "w") as output_file:
                engine = CompilationEngine(code, output_file)
                engine.compile_class()
