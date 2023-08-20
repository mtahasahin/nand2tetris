import os
import sys


class JackTokenizer:
    def __init__(self, code) -> None:
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
            self.__set_token(c, "SYMBOL")
        elif c == "/":
            if self.__match("/"):
                while self.__peek() != "\n" and not self.__is_at_end():
                    self.__advance_character()
                self.__set_token(None, None)
                self.advance() #
            elif self.__match("*"):
                while not(self.__peek() == "*" and self.__peek_next() == "/"):
                    self.__advance_character()
                self.__advance_character()
                self.__advance_character()
                self.__set_token(None, None)
                self.advance()#
            else:
                self.__set_token(c, "SYMBOL")
        elif c in [" ", "\r", "\t", "\n"]:
            self.__set_token(None, None)
            self.advance()#
        elif c == "\"":
            while self.__peek() != "\"" and not self.__is_at_end():
                self.__advance_character()

            if self.__is_at_end():
                raise RuntimeError("Unterminated string")

            self.__advance_character()

            val = self.code[start_index + 1: self.index - 1]
            self.__set_token(val, "STRING_CONST")
        elif c.isdigit():
            while self.__peek().isdigit():
                self.__advance_character()

            val = self.code[start_index: self.index]
            self.__set_token(val, "INTEGER_CONST")
        elif c.isalpha() or c == '_':
            while self.__peek().isalnum() or self.__peek() == "_":
                self.__advance_character()

            val = self.code[start_index: self.index]
            is_keyword = val in ["class", "constructor", "function", "method", "field", "static", "var", "int", "char",
                                 "boolean", "void", "true", "false", "null", "this", "let", "do", "if", "else", "while",
                                 "return"]
            self.__set_token(val, "KEYWORD" if is_keyword else "IDENTIFIER")

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


class CompilationEngine:
    def __init__(self, input_file, output_file):
        self.tokenizer = JackTokenizer(input_file)
        self.output_file = output_file

    def convert(self, string):
        if string == "<":
            return "&lt;"
        if string == ">":
            return "&gt;"
        if string == "\"":
            return "&quot;"
        if string == "&":
            return "&amp;"
        return string

    def __print_key_word(self):
        self.output_file.write("<keyword> " + self.tokenizer.key_word() + " </keyword>\n ")

    def __print_identifier(self):
        self.output_file.write("<identifier> " + self.tokenizer.identifier() + " </identifier>\n ")

    def __print_symbol(self):
        self.output_file.write("<symbol> " + self.convert(self.tokenizer.symbol()) + " </symbol>\n ")

    def __print_integer_constant(self):
        self.output_file.write("<integerConstant> " + self.tokenizer.symbol() + " </integerConstant>\n ")

    def __print_string_constant(self):
        self.output_file.write("<stringConstant> " + self.tokenizer.symbol() + " </stringConstant>\n ")

    def compile_class(self):
        self.output_file.write("<class>\n")
        self.tokenizer.advance()
        self.__print_key_word()
        self.tokenizer.advance()
        self.compile_class_name()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "{":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        while self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() in ["static", "field"]:
            self.compile_class_var_dec()

        while self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() in ["constructor", "function", "method"]:
            self.compile_subroutine_dec()

        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "}":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        self.output_file.write("</class>\n")

    def compile_class_name(self):
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.__print_identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_class_var_dec(self):
        self.output_file.write("<classVarDec>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        self.compile_type()
        self.compile_varname()
        while self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ",":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_varname()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ";":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.output_file.write("</classVarDec>\n")

    def compile_subroutine_dec(self):
        self.output_file.write("<subroutineDec>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        if self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() == "void":
            self.__print_key_word()
            self.tokenizer.advance()
        else:
            self.compile_type()

        self.compile_subroutine_name()

        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "(":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        self.compile_parameter_list()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        self.compile_subroutine_body()

        self.output_file.write("</subroutineDec>\n")


    def compile_subroutine_body(self):
        self.output_file.write("<subroutineBody>\n")
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "{":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        while self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() == "var":
            self.compile_var_dec()

        self.compile_statements()

        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "}":
            self.__print_symbol()
            self.tokenizer.advance()
        self.output_file.write("</subroutineBody>\n")

    def compile_statements(self):
        self.output_file.write("<statements>\n")
        while self.tokenizer.token_type() == "KEYWORD":
            if self.tokenizer.key_word() == "let":
                self.compile_let_statement()
            elif self.tokenizer.key_word() == "if":
                self.compile_if_statement()
            elif self.tokenizer.key_word() == "while":
                self.compile_while_statement()
            elif self.tokenizer.key_word() == "do":
                self.compile_do_statement()
            elif self.tokenizer.key_word() == "return":
                self.compile_return_statement()

        self.output_file.write("</statements>\n")

    def compile_let_statement(self):
        self.output_file.write("<letStatement>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        self.compile_varname()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "[":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_expression()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "]":
                self.__print_symbol()
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "=":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_expression()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ";":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.output_file.write("</letStatement>\n")

    def compile_if_statement(self):
        self.output_file.write("<ifStatement>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "(":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_expression()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "{":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_statements()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "}":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() == "else":
            self.__print_key_word()
            self.tokenizer.advance()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "{":
                self.__print_symbol()
                self.tokenizer.advance()
            else:
                raise RuntimeError()
            self.compile_statements()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "}":
                self.__print_symbol()
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        self.output_file.write("</ifStatement>\n")

    def compile_while_statement(self):
        self.output_file.write("<whileStatement>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "(":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_expression()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "{":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.compile_statements()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "}":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.output_file.write("</whileStatement>\n")

    def compile_do_statement(self):
        self.output_file.write("<doStatement>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        self.compile_subroutine_call()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ";":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        self.output_file.write("</doStatement>\n")

    def compile_return_statement(self):
        self.output_file.write("<returnStatement>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ";":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            self.compile_expression()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ";":
                self.__print_symbol()
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        self.output_file.write("</returnStatement>\n")

    def compile_expression(self):
        self.output_file.write("<expression>\n")
        self.compile_term()
        while self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() in ["+", "-", "*", "/", "&", "|", "<", ">", "="]:
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_term()
        self.output_file.write("</expression>\n")

    def compile_term(self):
        self.output_file.write("<term>\n")
        if self.tokenizer.token_type() == "INTEGER_CONST":
            self.__print_integer_constant()
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == "STRING_CONST":
            self.__print_string_constant()
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() in ["true", "false", "null", "this"]:
            self.__print_key_word()
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "(":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_expression()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
                self.__print_symbol()
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        elif self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() in ["-", "~"]:
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_term()
        elif self.tokenizer.token_type() == "IDENTIFIER":
            if self.tokenizer.peek_next_token()[0] == "[":
                self.compile_varname()
                if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "[":
                    self.__print_symbol()
                    self.tokenizer.advance()
                else:
                    raise RuntimeError()
                self.compile_expression()
                if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "]":
                    self.__print_symbol()
                    self.tokenizer.advance()
                else:
                    raise RuntimeError()
            elif self.tokenizer.peek_next_token()[0] in ["(", "."]:
                self.compile_subroutine_call()
            else:
                self.compile_varname()
        else:
            raise RuntimeError()
        self.output_file.write("</term>\n")

    def compile_expression_list(self):
        self.output_file.write("<expressionList>\n")
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
            self.output_file.write("</expressionList>\n")
            return
        self.compile_expression()
        while self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ",":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_expression()
        self.output_file.write("</expressionList>\n")

    def compile_subroutine_call(self):
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.__print_identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()
        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "(":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_expression_list()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
                self.__print_symbol()
                self.tokenizer.advance()
            else:
                raise RuntimeError()
        elif self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ".":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_subroutine_name()
            if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == "(":
                self.__print_symbol()
                self.tokenizer.advance()
                self.compile_expression_list()
                if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
                    self.__print_symbol()
                    self.tokenizer.advance()
                else:
                    raise RuntimeError()
            else:
                raise RuntimeError()
        else:
            raise RuntimeError()

    def compile_var_dec(self):
        self.output_file.write("<varDec>\n")
        self.__print_key_word()
        self.tokenizer.advance()
        self.compile_type()
        self.compile_varname()
        while self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ",":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_varname()

        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ";":
            self.__print_symbol()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

        self.output_file.write("</varDec>\n")

    def compile_parameter_list(self):
        self.output_file.write("<parameterList>\n")

        if self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ")":
            self.output_file.write("</parameterList>\n")
            return

        self.compile_type()
        self.compile_varname()
        while self.tokenizer.token_type() == "SYMBOL" and self.tokenizer.symbol() == ",":
            self.__print_symbol()
            self.tokenizer.advance()
            self.compile_type()
            self.compile_varname()
        self.output_file.write("</parameterList>\n")

    def compile_subroutine_name(self):
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.__print_identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_type(self):
        if self.tokenizer.token_type() == "KEYWORD" and self.tokenizer.key_word() in ["int","char","boolean"]:
            self.__print_key_word()
            self.tokenizer.advance()
        elif self.tokenizer.token_type() == "IDENTIFIER":
            self.__print_identifier()
            self.tokenizer.advance()
        else:
            raise RuntimeError()

    def compile_varname(self):
        if self.tokenizer.token_type() == "IDENTIFIER":
            self.__print_identifier()
            self.tokenizer.advance()
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
            output_filename = current_filename + ".compiled.xml"
            with open(output_filename, "w") as output_file:
                engine = CompilationEngine(code, output_file)
                engine.compile_class()


