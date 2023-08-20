import os
import sys


class Parser:
    def __init__(self, file):
        self.lines = file
        self.current_line_index = 0
        self.current_command = None

    def has_more_commands(self):
        return len(self.lines) > self.current_line_index

    def advance(self):
        while True:
            line = self.lines[self.current_line_index].strip()
            self.current_line_index += 1
            if not line or line.startswith("//"):
                continue
            if line.find("//") != -1:
                line = line[0:line.find("//")]
            self.current_command = line
            break

    def command_type(self):
        if self.current_command in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return "C_ARITHMETIC"
        elif self.current_command.startswith("push"):
            return "C_PUSH"
        elif self.current_command.startswith("pop"):
            return "C_POP"
        elif self.current_command.startswith("label"):
            return "C_LABEL"
        elif self.current_command.startswith("goto"):
            return "C_GOTO"
        elif self.current_command.startswith("if-goto"):
            return "C_IF"
        elif self.current_command.startswith("function"):
            return "C_FUNCTION"
        elif self.current_command.startswith("return"):
            return "C_RETURN"
        elif self.current_command.startswith("call"):
            return "C_CALL"

    def arg1(self):
        if self.current_command in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return self.current_command
        elif self.current_command.startswith("push")\
                or self.current_command.startswith("pop")\
                or self.current_command.startswith("label")\
                or self.current_command.startswith("goto")\
                or self.current_command.startswith("if-goto"):
            return self.current_command.split()[1]

    def arg2(self):
        return int(self.current_command.split()[2])


def get_segment_symbol(segment):
    segment_to_symbol = {"argument": "ARG", "local": "LCL", "this": "THIS", "that": "THAT"}
    return segment_to_symbol.get(segment)


class CodeWriter:
    def __init__(self, output_file):
        self.output_file = open(output_file, "w")
        self.current_file_name = ""
        self.lbl_count = 0

    def write_label(self, label):
        self.output_file.write("("+label+")\n")

    def write_goto(self, label):
        self.output_file.write("@"+label+"\n")
        self.output_file.write("0;JMP\n")

    def write_if(self, label):
        self.dec_sp()
        self.sp_to_d()
        self.output_file.write("@"+label+"\n")
        self.output_file.write("D;JNE\n")

    def _get_next_lbl(self):
        self.lbl_count += 1
        return "lbl" + str(self.lbl_count)

    def set_file_name(self, file_name: str):
        self.current_file_name = file_name

    def write_arithmetic(self, command: str):
        commandset = {"add": "M=D+M", "sub": "M=M-D", "and": "M=M&D", "or": "M=M|D"}
        commandset2 = {"eq": "JNE", "gt": "JGE", "lt": "JLE"}

        self.output_file.write("@SP\n")
        self.output_file.write("M=M-1\n")
        self.output_file.write("A=M\n")
        if command in ["add", "sub", "and", "or", "eq", "gt", "lt"]:
            self.output_file.write("D=M\n")
            self.output_file.write("@SP\n")
            self.output_file.write("M=M-1\n")
            self.output_file.write("A=M\n")
            if command in ["add", "sub", "and", "or"]:
                self.output_file.write(commandset.get(command) + "\n")
            elif command in ["eq", "gt", "lt"]:
                self.output_file.write("D=D-M\n")
                self.output_file.write("M=0\n")
                lbl = self._get_next_lbl()
                self.output_file.write("@" + lbl + "\n")
                self.output_file.write("D;" + commandset2.get(command) + "\n")
                self.output_file.write("@SP\n")
                self.output_file.write("A=M\n")
                self.output_file.write("M=-1\n")
                self.output_file.write("(" + lbl + ")\n")
        elif command in ["neg"]:
            self.output_file.write("M=-M\n")
        elif command in ["not"]:
            self.output_file.write("M=!M\n")
        self.output_file.write("@SP\n")
        self.output_file.write("M=M+1\n")

    def write_push_pop(self, command, segment, index):
        if command == "C_PUSH":
            if segment == "constant":
                self.constant_to_d(index)
                self.d_to_sp()
                self.inc_sp()
            elif segment in ["argument", "local", "this", "that"]:
                self.segment_to_d(segment, index)
                self.d_to_sp()
                self.inc_sp()
            elif segment == "pointer":
                self.output_file.write("@" + str(3+index) + "\n")
                self.output_file.write("D=M\n")
                self.d_to_sp()
                self.inc_sp()
            elif segment == "temp":
                self.output_file.write("@" + str(5 + index) + "\n")
                self.output_file.write("D=M\n")
                self.d_to_sp()
                self.inc_sp()
            elif segment == "static":
                self.output_file.write("@" + self.current_file_name + "." + str(index) + "\n")
                self.output_file.write("D=M\n")
                self.d_to_sp()
                self.inc_sp()
        elif command == "C_POP":
            self.dec_sp()
            if segment in ["argument", "local", "this", "that"]:
                self.sp_to_segment(segment, index)
            elif segment == "pointer":
                self.sp_to_d()
                self.output_file.write("@"+str(3+index)+"\n")
                self.output_file.write("M=D\n")
            elif segment == "temp":
                self.sp_to_d()
                self.output_file.write("@" + str(5 + index) + "\n")
                self.output_file.write("M=D\n")
            elif segment == "static":
                self.sp_to_d()
                self.output_file.write("@" + self.current_file_name + "." + str(index) + "\n")
                self.output_file.write("M=D\n")

    def sp_to_d(self):
        self.output_file.write("@SP\n")
        self.output_file.write("A=M\n")
        self.output_file.write("D=M\n")

    def sp_to_segment(self, segment, index):
        self.sp_to_d()
        sym = get_segment_symbol(segment)
        self.output_file.write("@" + sym + "\n")
        self.output_file.write("D=D+M\n")
        self.output_file.write("@" + str(index) + "\n")
        self.output_file.write("D=D+A\n")
        self.output_file.write("@SP\n")
        self.output_file.write("A=M\n")
        self.output_file.write("A=M\n")
        self.output_file.write("A=D-A\n")
        self.output_file.write("M=D-A\n")

    def segment_to_d(self, segment, index):
        sym = get_segment_symbol(segment)
        self.output_file.write("@" + sym + "\n")
        self.output_file.write("D=M\n")
        self.output_file.write("@" + str(index) + "\n")
        self.output_file.write("A=D+A\n")
        self.output_file.write("D=M\n")

    def constant_to_d(self, constant):
        self.output_file.write("@" + str(constant) + "\n")
        self.output_file.write("D=A\n")

    def d_to_sp(self):
        self.output_file.write("@SP\n")
        self.output_file.write("A=M\n")
        self.output_file.write("M=D\n")

    def inc_sp(self):
        self.output_file.write("@SP\n")
        self.output_file.write("M=M+1\n")

    def dec_sp(self):
        self.output_file.write("@SP\n")
        self.output_file.write("M=M-1\n")

    def close(self):
        self.output_file.close()


if __name__ == '__main__':
    path = sys.argv[1]
    file_list = []
    if os.path.isfile(path):
        file_list.insert(0, path)
    elif os.path.isdir(path):
        for filename in os.listdir(path):
            if filename.endswith(".vm"):
                file_list.insert(0, os.path.join(path, filename))

    current_filename = os.path.splitext(path)[0]
    code_writer = CodeWriter(current_filename + ".asm")

    for filename in file_list:
        with open(filename, "r") as file:
            lines = file.readlines()
        parser = Parser(lines)
        code_writer.set_file_name(os.path.splitext(os.path.basename(filename))[0])
        while parser.has_more_commands():
            parser.advance()
            if parser.command_type() == "C_ARITHMETIC":
                arg = parser.arg1()
                code_writer.write_arithmetic(arg)
            elif parser.command_type() in ["C_PUSH", "C_POP"]:
                arg1 = parser.arg1()
                arg2 = parser.arg2()
                code_writer.write_push_pop(parser.command_type(), arg1, arg2)
            elif parser.command_type() == "C_LABEL":
                arg1 = parser.arg1()
                code_writer.write_label(arg1)
            elif parser.command_type() == "C_GOTO":
                arg1 = parser.arg1()
                code_writer.write_goto(arg1)
            elif parser.command_type() == "C_IF":
                arg1 = parser.arg1()
                code_writer.write_if(arg1)
    code_writer.close()
