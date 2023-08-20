import sys
import os


class Parser:
    def __init__(self, file):
        self.lines = file
        self.current_line_index = 0
        self.current_command = None

    def hasMoreCommands(self):
        return len(self.lines) > self.current_line_index

    def advance(self):
        while True:
            line = self.lines[self.current_line_index].strip()
            self.current_line_index += 1
            if not line or line.startswith("//"):
                continue
            self.current_command = line
            break

    def commandType(self):
        if self.current_command.startswith("@"):
            return "A_COMMAND"
        elif self.current_command.startswith("("):
            return "L_COMMAND"
        else:
            return "C_COMMAND"

    def symbol(self):
        if self.commandType() == "A_COMMAND":
            return self.current_command[1:]
        elif self.commandType() == "L_COMMAND":
            return self.current_command[1:-1]
        else:
            raise Exception("no symbol")

    def dest(self):
        index = self.current_command.find("=")
        if index == -1:
            return "0"
        else:
            return self.current_command[0:index]

    def comp(self):
        eq_index = self.current_command.find("=")
        com_index = self.current_command.find(";")
        com_index = com_index if com_index != -1 else len(self.current_command)
        return self.current_command[eq_index + 1:com_index]

    def jump(self):
        index = self.current_command.find(";")
        if index == -1:
            return "0"
        else:
            return self.current_command[index + 1:]


class Code:
    def __init__(self) -> None:
        pass

    def dest(mnemonic: str):
        d1 = d2 = d3 = "0"
        if "A" in mnemonic:
            d1 = "1"
        if "M" in mnemonic:
            d3 = "1"
        if "D" in mnemonic:
            d2 = "1"
        return d1 + d2 + d3

    def comp(mnemonic: str):
        switcher = {
            "0": "0101010",
            "1": "0111111",
            "-1": "0111010",
            "D": "0001100",
            "A": "0110000",
            "!D": "0001101",
            "!A": "0110001",
            "-D": "0001111",
            "-A": "0110011",
            "D+1": "0011111",
            "A+1": "0110111",
            "D-1": "0001110",
            "A-1": "0110010",
            "D+A": "0000010",
            "D-A": "0010011",
            "A-D": "0000111",
            "D&A": "0000000",
            "D|A": "0010101",
            "M": "1110000",
            "!M": "1110001",
            "-M": "1110011",
            "M+1": "1110111",
            "M-1": "1110010",
            "D+M": "1000010",
            "D-M": "1010011",
            "M-D": "1000111",
            "D&M": "1000000",
            "D|M": "1010101"
        }

        return switcher.get(mnemonic, "invalid mnemonic")

    def jump(mnemonic: str):
        switcher = {
            "0": "000",
            "JGT": "001",
            "JEQ": "010",
            "JGE": "011",
            "JLT": "100",
            "JNE": "101",
            "JLE": "110",
            "JMP": "111"
        }

        return switcher.get(mnemonic, "invalid mnemonic")


symbolTable = {
    "SP": "0",
    "LCL": "1",
    "ARG": "2",
    "THIS": "3",
    "THAT": "4",
    "R0": "0",
    "R1": "1",
    "R2": "2",
    "R3": "3",
    "R4": "4",
    "R5": "5",
    "R6": "6",
    "R7": "7",
    "R8": "8",
    "R9": "9",
    "R10": "10",
    "R11": "11",
    "R12": "12",
    "R13": "13",
    "R14": "14",
    "R15": "15",
    "SCREEN": "16384",
    "KBD": "24576"
}

if __name__ == "__main__":
    filename = sys.argv[1]
    with open(filename, "r") as file:
        lines = file.readlines()
    parser = Parser(lines)
    current_memory_location = 0
    while parser.hasMoreCommands():
        parser.advance()
        if parser.commandType() in ["A_COMMAND", "C_COMMAND"]:
            current_memory_location += 1
        elif parser.commandType() == "L_COMMAND":
            symbol = parser.symbol()
            symbolTable[symbol] = str(current_memory_location)

    parser = Parser(lines)
    variable_memory_location = 16

    output_filename = os.path.splitext(filename)[0] + ".hack"
    with open(output_filename, "w") as output:
        while parser.hasMoreCommands():
            parser.advance()
            if parser.commandType() == "A_COMMAND":
                symbol = parser.symbol()
                if symbol[0].isdigit():
                    output.write(bin(int(symbol))[2:].zfill(16) + "\n")
                else:
                    val = symbolTable.get(symbol)
                    if not val:
                        val = symbolTable[symbol] = str(variable_memory_location)
                        variable_memory_location += 1
                    output.write(bin(int(val))[2:].zfill(16) + "\n")
            elif parser.commandType() == "C_COMMAND":
                dest = parser.dest()
                comp = parser.comp()
                jump = parser.jump()
                output.write("111" + Code.comp(comp) + Code.dest(dest) + Code.jump(jump) + "\n")
