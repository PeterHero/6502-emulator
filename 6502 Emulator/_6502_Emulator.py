import re

"""
6502-like cpu simulation

features - official:
    - 8-bit data bus
    - 16-bit address bus
    - 8-bit ALU, Accumulator, Stack Pointer, Index Registers, Processor Status Register
    - 16-bit Program Counter
    - 70 instructions
    - 212 Operation Codes (OpCodes)

src: https://eater.net/datasheets/w65c02s.pdf
https://www.mdawson.net/vic20chrome/cpu/mos_6500_mpu_preliminary_may_1976.pdf
https://www.masswerk.at/6502/6502_instruction_set.html

my features:
- Register A = accumulator
- Registers X,Y = index registers
- Processor Status Register - P
- Program Counter Register - PC
- Stack Pointer Register - S ?????

"""

class CPU():
    def __init__(self):
        self.RAM = [0]*0xffff

        self.A = 0 # 8-bit
        self.X = 0 # 8-bit
        self.Y = 0 # 8-bit
        self.PC = 0 # 16-bit
        self.S = 0 # 8-bit
        self.P = 0 # 8-bit

        self.resetVector = 0x8000

    # ---- GET FLAG METHODS ----

    def GetCarryFlag(self):
        if self.P & 0b00000001 != 0:
            return 1
        else:
            return 0

    # ---- SET FLAG METHODS ----
    
    def SetNegativeFlag(self, value):
        if value == 0:
            self.P = self.P & 0b01111111
        else:
            self.P = self.P | 0b10000000
        return

    def SetZeroFlag(self, value):
        if value == 0:
            self.P = self.P & 0b11111101
        else:
            self.P = self.P | 0b00000010
        return

    def SetCarryFlag(self, value):
        if value == 0:
            self.P = self.P & 0b11111110
        else:
            self.P = self.P | 0b00000001
        return

    def SetOverflowFlag(self, value):
        if value == 0:
            self.P = self.P & 0b10111111
        else:
            self.P = self.P | 0b01000000
        return

    # ---- HELPER METHODS ----

    def IsNegative(self, value):
        if value & 0b10000000 != 0:
            return True
        else:
            return False

    def UpdateStatusRegister(self, n=None, z=None, c=None, i=None, d=None, v=None):
        if n != None:
            if n == 0:
                self.SetNegativeFlag(0)
            elif n == 1:
                self.SetNegativeFlag(1)
            elif n == -1:
                if self.IsNegative(self.A):
                    self.SetNegativeFlag(1)
                else:
                    self.SetNegativeFlag(0)

        if z != None:
            if z == 0:
                self.SetZeroFlag(0)
            elif n == 1:
                self.SetZeroFlag(1)
            elif n == -1:
                if self.A == 0:
                    self.SetZeroFlag(1)
                else:
                    self.SetZeroFlag(0)

        if c != None:
            if c == 0:
                self.SetCarryFlag(0)
            elif c == 1:
                self.SetCarryFlag(1)

        if v != None:
            if v == 0:
                self.SetOverflowFlag(0)
            elif v == 1:
                self.SetOverflowFlag(1)

        return

    # ---- INSTRUCTION METHODS ----

    def ADC_Imm(self):
        value = self.RAM[self.PC+1]
        self.PC += 1

        isANegative = self.IsNegative(self.A)
        isValueNegative = self.IsNegative(value)

        sum = self.A + value + self.GetCarryFlag()
        self.A = sum & 0b11111111

        if sum > 255:
            cFlag = 1
        else:
            cFlag = 0

        if isANegative == isValueNegative and isANegative != self.IsNegative(sum):
            vFlag = 1
        else:
            vFlag = 0

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag, v=vFlag)
        return

    def ADC_Abs(self):
        address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
        value = self.RAM[address]
        self.PC += 2

        isANegative = self.IsNegative(self.A)
        isValueNegative = self.IsNegative(value)

        sum = self.A + value + self.GetCarryFlag()
        self.A = sum & 0b11111111

        if sum > 255:
            cFlag = 1
        else:
            cFlag = 0

        if isANegative == isValueNegative and isANegative != self.IsNegative(sum):
            vFlag = 1
        else:
            vFlag = 0

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag, v=vFlag)
        return

    def CLC(self):
        self.SetCarryFlag(0)
        return

    def JMP_Abs(self):
        address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
        self.PC = address
        return


    def LDA_Imm(self):
        value = self.RAM[self.PC+1]
        self.PC += 1

        self.A = value

        self.UpdateStatusRegister(n=-1, z=-1)
        return

    def LDA_Abs(self):
        address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
        self.PC += 2

        self.A = self.RAM[address]

        self.UpdateStatusRegister(n=-1, z=-1)
        return

    def STA_Abs(self):
        address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
        self.PC += 2

        self.RAM[address] = self.A
        return


    # ---- INPUT METHODS ----

    def HexInputDirect(self):
        counter = self.resetVector
        line = input()
        while line != '':
            line = line.split()
            for num in line:
                self.RAM[counter] = int(num, 16)
                counter += 1

            line = input()

    def HexInputFile(self):
        with open("in.txt") as f:
            counter = self.resetVector
            line = f.readline()
            while True:
                endOfFile = not line.endswith("\n")
                if not endOfFile:
                    line = line[:-1]
                line = line.split()
                for num in line:
                    self.RAM[counter] = int(num, 16)
                    counter += 1
                if endOfFile:
                    break

                line = f.readline()
        return

    def AssemblyInputFile(self):
        with open("in.txt") as f:
            counter = self.resetVector
            line = f.readline()
            while True:
                endOfFile = not line.endswith("\n")
                if not endOfFile:
                    line = line[:-1]
                line = line.split()

                if re.match("^\$....$", line[1]):
                    adrsMode = 1

                if line[0].lower() == "adc":
                    if line[1].startswith("#"):
                        self.RAM[counter] = 0x69





    # ---- MAIN LOOP ----

    def Run(self):
        self.PC = self.resetVector

        while True:
            ins = self.RAM[self.PC]
            if ins == 0x69:
                self.ADC_Imm()
            elif ins == 0x6D:
                self.ADC_Abs()
                print(self.A)
                input()
            elif ins == 0x18:
                self.CLC()
            elif ins == 0x4C:
                self.JMP_Abs()
                continue
            elif ins == 0xA9:
                self.LDA_Imm()
            elif ins == 0xAD:
                self.LDA_Abs()
            elif ins == 0x8D:
                self.STA_Abs()
            else:
                print("instrctn not known")
                break
            self.PC += 1
        return

cpu = CPU()
cpu.HexInputFile()
cpu.Run()
print(cpu.A)
