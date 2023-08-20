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

    def arg1(self):
        if self.current_command in ["add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"]:
            return self.current_command
        elif self.current_command.startswith("push") or self.current_command.startswith("pop"):
            return self.current_command.split()[1]

    def arg2(self):
        return self.current_command.split()[2]


class CodeWriter:
    def __init__(self, output_file):
        self.output_file = open(output_file, "w")
        self.current_file_name = ""
        self.lbl_count = 0

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
                self.output_file.write("@" + str(index) + "\n")
                self.output_file.write("D=A\n")
                self.output_file.write("@SP\n")
                self.output_file.write("A=M\n")
                self.output_file.write("M=D\n")
                self.output_file.write("@SP\n")
                self.output_file.write("M=M+1\n")

    def close(self):
        self.output_file.close()


if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename, "r") as file:
        lines = file.readlines()
    parser = Parser(lines)
    output_filename = os.path.splitext(filename)[0] + ".asm"
    codewriter = CodeWriter(output_filename)
    while parser.has_more_commands():
        parser.advance()
        if parser.command_type() == "C_ARITHMETIC":
            arg = parser.arg1()
            codewriter.write_arithmetic(arg)
        elif parser.command_type() in ["C_PUSH"]:
            arg1 = parser.arg1()
            arg2 = parser.arg2()
            codewriter.write_push_pop(parser.command_type(), arg1, arg2)
    codewriter.close()
