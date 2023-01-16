"""
This project was created by Petr Hrdina as a semestral project for the class Programming 1 of the year 2022/23 on MFF Charles University.

specifications:
    - 8-bit data bus
    - 16-bit address bus
    - 8-bit ALU, Accumulator, Stack Pointer, Index Registers, Processor Status Register
    - 16-bit Program Counter

https://www.mdawson.net/vic20chrome/cpu/mos_6500_mpu_preliminary_may_1976.pdf
https://www.masswerk.at/6502/6502_instruction_set.html
https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
"""

import re
import os
import time
from numpy import uint8, uint16
import readline # only to fix bug on vs code which doesnt have internally this package


class CPU():
    def __init__(self):
        self.RAM = bytearray(0x10000)

        self.A = 0 # 8-bit
        self.X = 0 # 8-bit
        self.Y = 0 # 8-bit
        self.PC = 0 # 16-bit
        self.S = 0 # 8-bit
        self.P = 0 # 8-bit

        self.resetVector = 0x8000 # starting address of the program

        self.adrsMode = {"A":0,"abs":1,"abs,X":2, "imm":4,"imp":5,"rel":9}

    # ---- GET FLAG METHODS ----
    """ Following methods return value of flag in the status register """

    def GetNegativeFlag(self):
        if self.P & 0b10000000 != 0:
            return 1
        else:
            return 0

    def GetCarryFlag(self):
        if self.P & 0b00000001 != 0:
            return 1
        else:
            return 0

    def GetZeroFlag(self):
        if self.P & 0b00000010 != 0:
            return 1
        else:
            return 0

    # ---- SET FLAG METHODS ----
    """ Following methods set flag in the status register to value (0 or 1) """

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
        """ Return True is value is negative in the two's complement view of the value """
        if value & 0b10000000 != 0:
            return True
        else:
            return False

    def UpdateStatusRegister(self, n=None, z=None, c=None, i=None, d=None, v=None):
        """ If parameter is 0 or 1, set flag to that value, if it is -1 check flag for Accumulator, if -2 check flag for X register.
            n - Negative flag
            z - Zero flag
            c - Carry flag
            i - Interrupt flag
            d - Decimal flag
            v - Overflow flag
        """
        
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
            elif n == -2:
                if self.IsNegative(self.X):
                    self.SetNegativeFlag(1)
                else:
                    self.SetNegativeFlag(0)

        if z != None:
            if z == 0:
                self.SetZeroFlag(0)
            elif z == 1:
                self.SetZeroFlag(1)
            elif z == -1:
                if self.A == 0:
                    self.SetZeroFlag(1)
                else:
                    self.SetZeroFlag(0)
            elif z == -2:
                if self.X == 0:
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

    def ADC(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            value = self.RAM[address]
            self.PC += 2
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1
        elif thisMode == self.adrsMode["abs,X"]:
            address = uint16(self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8) + self.X)
            value = self.RAM[address]
            self.PC += 2

        isANegative = self.IsNegative(self.A)
        isValueNegative = self.IsNegative(value)

        sum = self.A + value + self.GetCarryFlag()
        self.A = uint8(sum)

        if sum > 255:
            cFlag = 1
        else:
            cFlag = 0

        if isANegative == isValueNegative and isANegative != self.IsNegative(self.A):
            vFlag = 1
        else:
            vFlag = 0

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag, v=vFlag)
        return

    def AND(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            value = self.RAM[address]
            self.PC += 2
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1

        self.A = self.A & value
        self.UpdateStatusRegister(n=-1, z=-1)
        return

    def ASL(self, thisMode):
        if thisMode == self.adrsMode["A"]:
            if self.A & 0x80 != 0:
                cFlag = 1
            else:
                cFlag = 0

            self.A = (self.A << 1) & 0xff

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag)
        return

    def BCC(self):
        if self.GetCarryFlag() == 0:
            if self.IsNegative(self.RAM[self.PC+1]):
                self.PC = uint16(self.PC + self.RAM[self.PC+1] - 0x100)
            else:
                self.PC = uint16(self.PC + self.RAM[self.PC+1])

        self.PC += 1
        return

    def BCS(self):
        if self.GetCarryFlag() == 1:
            if self.IsNegative(self.RAM[self.PC+1]):
                self.PC = uint16(self.PC + self.RAM[self.PC+1] - 0x100)
            else:
                self.PC = uint16(self.PC + self.RAM[self.PC+1])

        self.PC += 1
        return

    def BEQ(self):
        if self.GetZeroFlag() == 1:
            if self.IsNegative(self.RAM[self.PC+1]):
                self.PC = uint16(self.PC + self.RAM[self.PC+1] - 0x100)
            else:
                self.PC = uint16(self.PC + self.RAM[self.PC+1])

        self.PC += 1
        return

    def BMI(self):
        if self.GetNegativeFlag() == 1:
            if self.IsNegative(self.RAM[self.PC+1]):
                self.PC = uint16(self.PC + self.RAM[self.PC+1] - 0x100)
            else:
                self.PC = uint16(self.PC + self.RAM[self.PC+1])

        self.PC += 1
        return

    def BNE(self):
        if self.GetZeroFlag() == 0:
            if self.IsNegative(self.RAM[self.PC+1]):
                self.PC = uint16(self.PC + self.RAM[self.PC+1] - 0x100)
            else:
                self.PC = uint16(self.PC + self.RAM[self.PC+1])

        self.PC += 1
        return

    def BPL(self):
        if self.GetNegativeFlag() == 0:
            if self.IsNegative(self.RAM[self.PC+1]):
                self.PC = uint16(self.PC + self.RAM[self.PC+1] - 0x100)
            else:
                self.PC = uint16(self.PC + self.RAM[self.PC+1])

        self.PC += 1
        return

    def CLC(self):
        self.SetCarryFlag(0)
        return

    def CMP(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            value = self.RAM[address]
            self.PC += 2
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1

        if self.A < value:
            zFlag = 0
            cFlag = 0
        elif self.A == value:
            zFlag = 1
            cFlag = 1
        elif self.A > value:
            zFlag = 0
            cFlag = 1

        result = uint8(self.A - value)

        if self.IsNegative(result):
            nFlag = 1
        else:
            nFlag = 0

        self.UpdateStatusRegister(n=nFlag, z=zFlag, c=cFlag)
        return

    def DEX(self):
        self.X = uint8(self.X - 1)        

        self.UpdateStatusRegister(n=-2, z=-2)
        return

    def EOR(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            value = self.RAM[address]
            self.PC += 2
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1

        self.A = self.A ^ value
        self.UpdateStatusRegister(n=-1, z=-1)
        return

    def INX(self):
        self.X = uint8(self.X + 1)

        self.UpdateStatusRegister(n=-2, z=-2)
        return

    def JMP(self, thisMode):
        if thisMode == self.adrsMode["abs"]: 
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
        self.PC = address
        return

    def LDA(self, thisMode):
        if thisMode == self.adrsMode["abs"]:            
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            self.PC += 2
            self.A = self.RAM[address]
        elif thisMode == self.adrsMode["abs,X"]:            
            address = uint16(self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8) + self.X)
            self.PC += 2
            self.A = self.RAM[address] 
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1
            self.A = value
            

        self.UpdateStatusRegister(n=-1, z=-1)
        return

    def LDX(self, thisMode):
        if thisMode == self.adrsMode["abs"]:            
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            self.PC += 2
            self.X = self.RAM[address]            
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1
            self.X = value
            

        self.UpdateStatusRegister(n=-2, z=-2)
        return

    def LSR(self, thisMode):
        if thisMode == self.adrsMode["A"]:
            if self.A & 0x01 != 0:
                cFlag = 1
            else:
                cFlag = 0

            self.A = self.A >> 1

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag)
        return

    def ORA(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            value = self.RAM[address]
            self.PC += 2
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1]
            self.PC += 1

        self.A = self.A | value
        self.UpdateStatusRegister(n=-1, z=-1)
        return

    def ROL(self, thisMode):
        if thisMode == self.adrsMode["A"]:
            if self.A & 0x80 != 0:
                cFlag = 1
            else:
                cFlag = 0

            self.A = (uint8(self.A << 1)) + self.GetCarryFlag()

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag)
        return

    def ROR(self, thisMode):
        if thisMode == self.adrsMode["A"]:
            if self.A & 0x01 != 0:
                cFlag = 1
            else:
                cFlag = 0

            self.A = (self.A >> 1) + self.GetCarryFlag() * 0x80

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag)
        return

    def SBC(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            value = self.RAM[address] + (self.GetCarryFlag() - 1)
            self.PC += 2
        elif thisMode == self.adrsMode["abs,X"]:
            address = uint16(self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8) + self.X)
            value = self.RAM[address] + (self.GetCarryFlag() - 1)
            self.PC += 2
        elif thisMode == self.adrsMode["imm"]:
            value = self.RAM[self.PC+1] + (self.GetCarryFlag() - 1)
            self.PC += 1

        isANegative = self.IsNegative(self.A)
        isValueNegative = self.IsNegative(value)

        if self.A < value:
            cFlag = 1
        else:
            cFlag = 0

        self.A = uint8(self.A - value)

        if isANegative != isValueNegative and isANegative != self.IsNegative(self.A):
            vFlag = 1
        else:
            vFlag = 0

        self.UpdateStatusRegister(n=-1, z=-1, c=cFlag, v=vFlag)
        return
    
    def SEC(self):
        self.SetCarryFlag(1)
        return

    def STA(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            self.PC += 2
        elif thisMode == self.adrsMode["abs,X"]:
            address = uint16(self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8) + self.X)
            self.PC += 2

        self.RAM[address] = self.A
        return

    def STX(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
            self.PC += 2

        self.RAM[address] = self.X
        return

    def TAX(self):
        self.X = self.A

        self.UpdateStatusRegister(n=-2, z=-2)
        return

    def TXA(self):
        self.A = self.X

        self.UpdateStatusRegister(n=-1, z=-1)
        return

    # ---- INPUT METHODS ----

    def HexInputConsole(self):
        """ Line by line writes input in hexadecimal into memory, until line is empy """
        counter = self.resetVector
        line = input()
        while line != '':
            line = line.split()
            for num in line:
                self.RAM[counter] = int(num, 16)
                counter += 1

            line = input()
        return

    def HexInputFile(self):
        """ Writes input from file 'in.txt' to memory """
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/in.txt") as f:
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

    def Translate(self, line, counter):
        """ Helper method of the assembly input methods. Matches line written in assembly with hexadecimal eqvivalent and writes it to memory. """
        line = line.split()

        if len(line) == 1:
            thisMode = self.adrsMode["imp"]
        elif line[1] == "A":
            thisMode = self.adrsMode["A"]
        elif re.match("^\$....$", line[1]):
            thisMode = self.adrsMode["abs"]
        elif re.match("^\$....,X$", line[1]):
            thisMode = self.adrsMode["abs,X"]
        elif re.match("^\$....,Y$", line[1]):
            thisMode = 3 # absolute, Y-indexed
        elif re.match("^#\$..$", line[1]):
            thisMode = self.adrsMode["imm"]
        elif re.match("^\$..$", line[1]):
            thisMode = self.adrsMode["rel"]

                

        if line[0].lower() == "adc":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x6D
            elif thisMode == self.adrsMode["abs,X"]:
                self.RAM[counter] = 0x7D
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0x69
        elif line[0].lower() == "and":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x2D
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0x29
        elif line[0].lower() == "asl":
            if thisMode == self.adrsMode["A"]:
                self.RAM[counter] = 0x0A
        elif line[0].lower() == "bcc":
            self.RAM[counter] = 0x90
        elif line[0].lower() == "bcs":
            self.RAM[counter] = 0xB0
        elif line[0].lower() == "beq":
            self.RAM[counter] = 0xF0
        elif line[0].lower() == "bmi":
            self.RAM[counter] = 0x30
        elif line[0].lower() == "bne":
            self.RAM[counter] = 0xD0
        elif line[0].lower() == "bpl":
            self.RAM[counter] = 0x10
        elif line[0].lower() == "clc":
            self.RAM[counter] = 0x18
        elif line[0].lower() == "cmp":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0xCD
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0xC9
        elif line[0].lower() == "dex":
            self.RAM[counter] = 0xCA
        elif line[0].lower() == "eor":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x4D
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0x49
        elif line[0].lower() == "inx":
            self.RAM[counter] = 0xE8
        elif line[0].lower() == "jmp":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x4C
        elif line[0].lower() == "lda":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0xAD
            elif thisMode == self.adrsMode["abs,X"]:
                self.RAM[counter] = 0xBD
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0xA9
        elif line[0].lower() == "ldx":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0xAE
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0xA2
        elif line[0].lower() == "lsr":
            if thisMode == self.adrsMode["A"]:
                self.RAM[counter] = 0x4A
        elif line[0].lower() == "ora":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x0D
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0x09
        elif line[0].lower() == "rol":
            if thisMode == self.adrsMode["A"]:
                self.RAM[counter] = 0x2A
        elif line[0].lower() == "ror":
            if thisMode == self.adrsMode["A"]:
                self.RAM[counter] = 0x6A
        elif line[0].lower() == "sbc":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0xED
            elif thisMode == self.adrsMode["abs,X"]:
                self.RAM[counter] = 0xFD
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0xE9
        elif line[0].lower() == "sec":
            self.RAM[counter] = 0x38
        elif line[0].lower() == "sta":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x8D
            elif thisMode == self.adrsMode["abs,X"]:
                self.RAM[counter] = 0x9D
        elif line[0].lower() == "stx":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x8E
        elif line[0].lower() == "tax":
                self.RAM[counter] = 0xAA
        elif line[0].lower() == "txa":
                self.RAM[counter] = 0x8A

        counter += 1

        if thisMode == self.adrsMode["A"]:
            pass
        elif thisMode == self.adrsMode["abs"]:
            self.RAM[counter] = int(line[1][3:], 16)
            self.RAM[counter+1] = int(line[1][1:3], 16)
            counter += 2
        elif thisMode == self.adrsMode["abs,X"]:
            self.RAM[counter] = int(line[1][3:5], 16)
            self.RAM[counter+1] = int(line[1][1:3], 16)
            counter += 2
        elif thisMode == 3:
            self.RAM[counter] = int(line[1][3:5], 16)
            self.RAM[counter+1] = int(line[1][1:3], 16)
            counter += 2
        elif thisMode == self.adrsMode["imm"]:
            self.RAM[counter] = int(line[1][2:], 16)
            counter += 1
        elif thisMode == self.adrsMode["rel"]:
            self.RAM[counter] = int(line[1][1:], 16)
            counter += 1
        elif thisMode == self.adrsMode["imp"]:
            pass

        return counter

    def AssemblyInputConsole(self):
        counter = self.resetVector
        line = input()
        while line != '':            
            counter = self.Translate(line, counter)

            line = input()

    def AssemblyInputFile(self):
        counter = self.resetVector
        with open(f"{os.path.dirname(os.path.realpath(__file__))}/in.txt") as f:
            line = f.readline()
            while True:
                endOfFile = not line.endswith("\n")
                if not endOfFile:
                    line = line[:-1]
                    
                counter = self.Translate(line, counter)

                if endOfFile:
                    break

                line = f.readline()
                
    # ---- DEBUG MODE ----
    
    def Encode(self, index):
        """ Encodes instruction on index in RAM from hexadecimal to assembly eqvivalent - stored in ins_s.
            Returns this string instruction and index of the next instruction.
        """

        ins = self.RAM[index]

        if ins == 0x69:
            thisMode = self.adrsMode["imm"]
            ins_s = "adc"
        elif ins == 0x6D:
            thisMode = self.adrsMode["abs"]
            ins_s = "adc"
        elif ins == 0x7D:
            thisMode = self.adrsMode["abs,X"]
            ins_s = "adc"
        elif ins == 0x29:
            thisMode = self.adrsMode["imm"]
            ins_s = "and"
        elif ins == 0x2D:
            thisMode = self.adrsMode["abs"]
            ins_s = "and"
        elif ins == 0x0A:
            thisMode = self.adrsMode["A"]
            ins_s = "asl"
        elif ins == 0x90:
            thisMode = self.adrsMode["rel"]
            ins_s = "bcc"
        elif ins == 0xB0:
            thisMode = self.adrsMode["rel"]
            ins_s = "bcs"
        elif ins == 0xF0:
            thisMode = self.adrsMode["rel"]
            ins_s = "beq"
        elif ins == 0x30:
            thisMode = self.adrsMode["rel"]
            ins_s = "bmi"
        elif ins == 0xD0:
            thisMode = self.adrsMode["rel"]
            ins_s = "bne"
        elif ins == 0x10:
            thisMode = self.adrsMode["rel"]
            ins_s = "bpl"
        elif ins == 0x00:
            thisMode = self.adrsMode["imp"]
            ins_s = "brk"
        elif ins == 0x18:
            thisMode = self.adrsMode["imp"]
            ins_s = "clc"
        elif ins == 0xC9:
            thisMode = self.adrsMode["imm"]
            ins_s = "cmp"
        elif ins == 0xCD:
            thisMode = self.adrsMode["abs"]
            ins_s = "cmp"
        elif ins == 0xCA:
            thisMode = self.adrsMode["imp"]
            ins_s = "dex"
        elif ins == 0x49:
            thisMode = self.adrsMode["imm"]
            ins_s = "eor"
        elif ins == 0x4D:
            thisMode = self.adrsMode["abs"]
            ins_s = "eor"
        elif ins == 0xE8:
            thisMode = self.adrsMode["imp"]
            ins_s = "inx"
        elif ins == 0x4C:
            thisMode = self.adrsMode["abs"]
            ins_s = "jmp"
        elif ins == 0xA9:
            thisMode = self.adrsMode["imm"]
            ins_s = "lda"
        elif ins == 0xAD:
            thisMode = self.adrsMode["abs"]
            ins_s = "lda"
        elif ins == 0xBD:
            thisMode = self.adrsMode["abs,X"]
            ins_s = "lda"
        elif ins == 0xA2:
            thisMode = self.adrsMode["imm"]
            ins_s = "ldx"
        elif ins == 0xAE:
            thisMode = self.adrsMode["abs"]
            ins_s = "ldx"
        elif ins == 0x4A:
            thisMode = self.adrsMode["A"]
            ins_s = "lsr"
        elif ins == 0x09:
            thisMode = self.adrsMode["imm"]
            ins_s = "ora"
        elif ins == 0x0D:
            thisMode = self.adrsMode["abs"]
            ins_s = "ora"
        elif ins == 0x2A:
            thisMode = self.adrsMode["A"]
            ins_s = "rol"
        elif ins == 0x6A:
            thisMode = self.adrsMode["A"]
            ins_s = "ror"
        elif ins == 0xE9:
            thisMode = self.adrsMode["imm"]
            ins_s = "sbc"
        elif ins == 0xED:
            thisMode = self.adrsMode["abs"]
            ins_s = "sbc"
        elif ins == 0xFD:
            thisMode = self.adrsMode["abs,X"]
            ins_s = "sbc"
        elif ins == 0x38:
            thisMode = self.adrsMode["imp"]
            ins_s = "sec"
        elif ins == 0x8D:
            thisMode = self.adrsMode["abs"]
            ins_s = "sta"
        elif ins == 0x9D:
            thisMode = self.adrsMode["abs,X"]
            ins_s = "sta"
        elif ins == 0x8E:
            thisMode = self.adrsMode["abs"]
            ins_s = "stx"
        elif ins == 0xAA:
            thisMode = self.adrsMode["imp"]
            ins_s = "tax"
        elif ins == 0x8A:
            thisMode = self.adrsMode["imp"]
            ins_s = "txa"
        else:
            thisMode = self.adrsMode["imp"]
            ins_s = "nao"

        if thisMode == self.adrsMode["A"]:
            ins_s += " A"
        if thisMode == self.adrsMode["abs"]:
            ins_s += " $" + format(self.RAM[index+2], "02X") + format(self.RAM[index+1], "02X")
            index += 2
        elif thisMode == self.adrsMode["abs,X"]:
            ins_s += " $" + format(self.RAM[index+2], "02X") + format(self.RAM[index+1], "02X") + ",X"
            index += 2
        elif thisMode == self.adrsMode["imm"]:
            ins_s += " #$" + format(self.RAM[index+1], "02X")
            index += 1
        elif thisMode == self.adrsMode["imp"]:
            pass
        elif thisMode == self.adrsMode["rel"]:
            ins_s += " $" + format(self.RAM[index+1], "02X")
            index += 1

        index += 1

        return ins_s, index

    def PrintDebug(self, insIndex, dataIndex, colors):
        """ Prints debug screen with x instructions in assembly in the top, y lines of hexdump of memory on the bottom, and on the right prints contents of CPU registers. """

        print()
        clear()
        for i in range(15):
            ins_s, newInsIndex = self.Encode(insIndex)
            if colors:
                print(u"\u001b[32;1m", end='') # green
                print(f'I:{format(insIndex, "04X")}', end='')
                if insIndex == self.PC:
                    print(u"\u001b[33;1m", end='') # yellow
                else:
                    print(u"\u001b[36;1m", end='') # cyan
                if i == 2 or i == 3 or i == 4 or i == 6 or i == 8 or i == 9:
                    print("{:<16}".format(f' {ins_s}'), end='')
                else:
                    print(f' {ins_s}')
                
                if i == 2:
                    print(u"\u001b[32;1m", end='') # green
                    print("A   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(format(self.A, "02X"))
                if i == 3:
                    print(u"\u001b[32;1m", end='') # green
                    print("X   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(format(self.X, "02X"))
                if i == 4:
                    print(u"\u001b[32;1m", end='') # green
                    print("Y   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(format(self.Y, "02X"))
                if i == 6:
                    print(u"\u001b[32;1m", end='') # green
                    print("PC  ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(format(self.PC, "02X"))
                if i == 8:
                    print(u"\u001b[32;1m", end='') # green
                    print("S   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(format(self.S, "02X"))
                if i == 9:
                    print(u"\u001b[32;1m", end='') # green
                    print("P   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(format(self.P, "02X"))
            else:
                if i == 2 or i == 3 or i == 4 or i == 6 or i == 8 or i == 9:
                    print("{:<22}".format(f'I:{format(insIndex, "04X")} {ins_s}'), end='')
                else:
                    print(f'I:{format(insIndex, "04X")} {ins_s}')
                if i == 2:
                    print(f"A   {format(self.A, '02X')}")
                if i == 3:
                    print(f"X   {format(self.X, '02X')}")
                if i == 4:
                    print(f"Y   {format(self.Y, '02X')}")
                if i == 6:
                    print(f"PC  {format(self.PC, '04X')}")
                if i == 8:
                    print(f"S   {format(self.S, '02X')}")
                if i == 9:
                    print(f"P   {format(self.P, '02X')}")
            insIndex = newInsIndex

        print()
        for i in range(10):
            if colors:
                print(u"\u001b[32;1m", end='') # green
            print(f'M:{format(dataIndex, "04X")}', end='')
            if colors:
                print(u"\u001b[36;1m", end='') # cyan
            for j in range(8):
                print(f' {format(self.RAM[dataIndex], "02X")}', end='')
                dataIndex += 1
            print()
        
        if colors:
            print(u"\u001b[37;1m", end='') # white
        print(20 * "_")
        print('> ', end='')
        
        return

    # ---- MAIN LOOP ----

    def Run(self, debug = 0, colors = False):
        """ Main loop which steps the instructions in memory and executes them until reaches a break or not known instruction.
            At the end of program prints interactive debug screen, where user can view data in specific locations in memory.
            If debug mode is enabled, after every step interactive debug screen is printed, which also allows user to step through the program.
        """

        self.PC = self.resetVector
        stepper = 0         # number of steps to be done without debug screen
        dataIndex = 0       # starting location of data in memory displayed in debug screen
        insIndex = self.PC  # starting location of instructions in memory displayed in debug screen
        exit = False        # indicator if end the program without an ending debug screen

        while True:
            if debug == 1:
                insIndex = self.PC
                self.PrintDebug(insIndex, dataIndex, colors)

            if debug == 1 and stepper == 0:
                # interactive debug screen
                execute = False # indicator if command executes another instruction
                while not execute:
                    command = input().split()
                    if len(command) == 0:
                        print("command not valid")
                        input()
                        self.PrintDebug(insIndex, dataIndex, colors)
                    elif command[0] == "step":
                        if len(command) == 1:
                            execute = True
                        else:
                            stepper = int(command[1])
                            execute = True
                    elif command[0] == "m":
                        dataIndex = int(command[1], 16)
                        self.PrintDebug(insIndex, dataIndex, colors)
                    elif command[0] == "i":
                        insIndex = int(command[1], 16)
                        self.PrintDebug(insIndex, dataIndex, colors)
                    elif command[0] == "end":
                        clear()
                        debug = 0
                        execute = True
                    elif command[0] == "exit":
                        debug = 0
                        execute = True
                        exit = True
                    else:
                        print("command not valid")
                        input()
                        self.PrintDebug(insIndex, dataIndex, colors)
                    
            if stepper > 0:         # if there are yet steps without debug screen to be done
                time.sleep(0.75)
                stepper -= 1

            ins = self.RAM[self.PC]
            if ins == 0x69:
                self.ADC(self.adrsMode["imm"])
            elif ins == 0x6D:
                self.ADC(self.adrsMode["abs"])
            elif ins == 0x7D:
                self.ADC(self.adrsMode["abs,X"])
            elif ins == 0x29:
                self.AND(self.adrsMode["imm"])
            elif ins == 0x2D:
                self.AND(self.adrsMode["abs"])
            elif ins == 0x0A:
                self.ASL(self.adrsMode["A"])
            elif ins == 0x90:
                self.BCC()
            elif ins == 0xB0:
                self.BCS()
            elif ins == 0xF0:
                self.BEQ()
            elif ins == 0x30:
                self.BMI()
            elif ins == 0xD0:
                self.BNE()
            elif ins == 0x10:
                self.BPL()
            elif ins == 0x00:   # BRK instruction
                break
            elif ins == 0x18:
                self.CLC()
            elif ins == 0xC9:
                self.CMP(self.adrsMode["imm"])
            elif ins == 0xCD:
                self.CMP(self.adrsMode["abs"])
            elif ins == 0xCA:
                self.DEX()
            elif ins == 0x49:
                self.EOR(self.adrsMode["imm"])
            elif ins == 0x4D:
                self.EOR(self.adrsMode["abs"])
            elif ins == 0xE8:
                self.INX()
            elif ins == 0x4C:
                self.JMP(self.adrsMode["abs"])
                continue
            elif ins == 0xA9:
                self.LDA(self.adrsMode["imm"])
            elif ins == 0xAD:
                self.LDA(self.adrsMode["abs"])
            elif ins == 0xBD:
                self.LDA(self.adrsMode["abs,X"])
            elif ins == 0xA2:
                self.LDX(self.adrsMode["imm"])
            elif ins == 0xAE:
                self.LDX(self.adrsMode["abs"])
            elif ins == 0x4A:
                self.LSR(self.adrsMode["A"])
            elif ins == 0x09:
                self.ORA(self.adrsMode["imm"])
            elif ins == 0x0D:
                self.ORA(self.adrsMode["abs"])
            elif ins == 0x2A:
                self.ROL(self.adrsMode["A"])
            elif ins == 0x6A:
                self.ROR(self.adrsMode["A"])
            elif ins == 0xE9:
                self.SBC(self.adrsMode["imm"])
            elif ins == 0xED:
                self.SBC(self.adrsMode["abs"])
            elif ins == 0xFD:
                self.SBC(self.adrsMode["abs,X"])
            elif ins == 0x38:
                self.SEC()
            elif ins == 0x8D:
                self.STA(self.adrsMode["abs"])
            elif ins == 0x9D:
                self.STA(self.adrsMode["abs,X"])
            elif ins == 0x8E:
                self.STX(self.adrsMode["abs"])
            elif ins == 0xAA:
                self.TAX()
            elif ins == 0x8A:
                self.TXA()
            else:   # not an instruction
                break
            
            self.PC += 1
        
        # interactive debug screen at the end of program
        insIndex = self.PC
        while not exit:
            self.PrintDebug(insIndex, dataIndex, colors)
            command = input().split()
            if len(command) == 0:
                print("command not valid")
                input()
                self.PrintDebug(insIndex, dataIndex, colors)
            elif command[0] == "m":
                dataIndex = int(command[1], 16)
                self.PrintDebug(insIndex, dataIndex, colors)
            elif command[0] == "i":
                insIndex = int(command[1], 16)
                self.PrintDebug(insIndex, dataIndex, colors)
            elif command[0] == "exit":
                exit = True
            else:
                print("command not valid - press any key to continue")
                input()
                self.PrintDebug(insIndex, dataIndex, colors)
            
        return

def clear():
        # for windows
        if os.name == 'nt':
            _ = os.system('cls')
        # for mac and linux(here, os.name is 'posix')
        else:
            _ = os.system('clear')

source = 0          # 0 - console, 1 - file
inputFormat = 0     # 0 - hex,     1 - assembly
color = False       # 0 - off,     1 - on
mode = 0            # 0 - run,     1 - debug
correctConfig = True

# reading configuration
with open(f"{os.path.dirname(os.path.realpath(__file__))}/config.txt", "r") as f:
    line = f.readline()[:-1]
    if line == "source=console":
        source = 0
    elif line == "source=file":
        source = 1
    else:
        correctConfig = False

    line = f.readline()[:-1]
    if line == "format=hex":
        inputFormat = 0
    elif line == "format=assembly":
        inputFormat = 1
    else:
        correctConfig = False

    line = f.readline()[:-1]
    if line == "color=off":
        color = False
    elif line == "color=on":
        color = True
    else:
        correctConfig = False

    line = f.readline()
    if line == "mode=run":
        mode = 0
    elif line == "mode=debug":
        mode = 1
    else:
        correctConfig = False

if correctConfig:
    cpu = CPU()
    if source == 0 and inputFormat == 0:
        cpu.HexInputConsole()
    elif source == 0 and inputFormat == 1:
        cpu.AssemblyInputConsole()
    elif source == 1 and inputFormat == 0:
        cpu.HexInputFile()
    elif source == 1 and inputFormat == 1:
        cpu.AssemblyInputFile()

    cpu.Run(mode, color)
else:
    print("Incorrect configuration in config.txt, please set up file config.txt correctly!")
