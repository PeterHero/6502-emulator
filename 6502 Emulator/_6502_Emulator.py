import re
import os
import time

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
https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html

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

        self.adrsMode = {"abs":1,"imm":4,"imp":5}

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
            elif n == -2:
                if self.IsNegative(self.X):
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
            elif n == -2:
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

    def DEX(self):
        self.X = self.X - 1
        self.X = self.X % 256
        

        self.UpdateStatusRegister(n=-2, z=-2)
        return

    def INX(self):
        self.X = self.X + 1
        self.x = self.X % 256

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

    def STA(self, thisMode):
        if thisMode == self.adrsMode["abs"]:
            address = self.RAM[self.PC+1] + (self.RAM[self.PC+2] << 8)
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

    def Translate(self, line, counter):
        line = line.split()

        if len(line) == 1:
            thisMode = 5 # implied
        elif re.match("^\$....$", line[1]):
            thisMode = self.adrsMode["abs"]
        elif re.match("^\$....,X$", line[1]):
            thisMode = 2 # absolute, X-indexed
        elif re.match("^\$....,Y$", line[1]):
            thisMode = 3 # absolute, Y-indexed
        elif re.match("^#\$..$", line[1]):
            thisMode = self.adrsMode["imm"]
                

        if line[0].lower() == "adc":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x6D
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0x69
        elif line[0].lower() == "clc":
                self.RAM[counter] = 0x18
        elif line[0].lower() == "dex":
                self.RAM[counter] = 0xCA
        elif line[0].lower() == "inx":
            self.RAM[counter] = 0xE8
        elif line[0].lower() == "jmp":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x4C
        elif line[0].lower() == "lda":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0xAD
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0xA9
        elif line[0].lower() == "ldx":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0xAE
            elif thisMode == self.adrsMode["imm"]:
                self.RAM[counter] = 0xA2
        elif line[0].lower() == "sta":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x8D
        elif line[0].lower() == "stx":
            if thisMode == self.adrsMode["abs"]:
                self.RAM[counter] = 0x8E
        elif line[0].lower() == "tax":
                self.RAM[counter] = 0xAA
        elif line[0].lower() == "txa":
                self.RAM[counter] = 0x8A

        counter += 1

        if thisMode == self.adrsMode["abs"]:
            self.RAM[counter] = int(line[1][3:], 16)
            self.RAM[counter+1] = int(line[1][1:3], 16)
            counter += 2
        elif thisMode == 2:
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
        elif thisMode == 5:
            pass

        return counter

    def AssemblyInputDirect(self):
        counter = self.resetVector
        line = input()
        while line != '':            
            counter = self.Translate(line, counter)

            line = input()

    def AssemblyInputFile(self):
        counter = self.resetVector
        with open("in.txt") as f:
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
        ins = self.RAM[index]

        if ins == 0x69:
            thisMode = self.adrsMode["imm"]
            ins_s = "adc"
        elif ins == 0x6D:
            thisMode = self.adrsMode["abs"]
            ins_s = "adc"
        elif ins == 0x18:
            thisMode = self.adrsMode["imp"]
            ins_s = "clc"
        elif ins == 0xCA:
            thisMode = self.adrsMode["imp"]
            ins_s = "dex"
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
        elif ins == 0xA2:
            thisMode = self.adrsMode["imm"]
            ins_s = "ldx"
        elif ins == 0xAE:
            thisMode = self.adrsMode["abs"]
            ins_s = "ldx"
        elif ins == 0x8D:
            thisMode = self.adrsMode["abs"]
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

        if thisMode == self.adrsMode["abs"]:
            ins_s += " $" + hex(self.RAM[index+2])[2:].zfill(2) + hex(self.RAM[index+1])[2:].zfill(2)
            index += 2
        elif thisMode == self.adrsMode["imm"]:
            ins_s += " #$" + hex(self.RAM[index+1])[2:].zfill(2)
            index += 1
        elif thisMode == self.adrsMode["imp"]:
            pass

        index += 1

        return ins_s, index
    """
    print(u"\u001b[32;1m", end='') # green
    print(u"\u001b[36;1m", end='') # cyan
    print(u"\u001b[33;1m", end='') # yellow
    print(u"\u001b[0m", end='') # reset
    """

    def PrintDebug(self, insIndex, dataIndex):
        colors = True
        print()
        clear()
        for i in range(15):
            ins_s, newInsIndex = self.Encode(insIndex)
            if colors:
                print(u"\u001b[32;1m", end='') # green
                print(f'I:{hex(insIndex)[2:].zfill(4).upper()}', end='')
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
                    print(hex(self.A)[2:].zfill(2))
                if i == 3:
                    print(u"\u001b[32;1m", end='') # green
                    print("X   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(hex(self.X)[2:].zfill(2))
                if i == 4:
                    print(u"\u001b[32;1m", end='') # green
                    print("Y   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(hex(self.Y)[2:].zfill(2))
                if i == 6:
                    print(u"\u001b[32;1m", end='') # green
                    print("PC  ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(hex(self.PC)[2:].zfill(4))
                if i == 8:
                    print(u"\u001b[32;1m", end='') # green
                    print("S   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(hex(self.S)[2:].zfill(2))
                if i == 9:
                    print(u"\u001b[32;1m", end='') # green
                    print("P   ", end='')
                    print(u"\u001b[36;1m", end='') # cyan
                    print(hex(self.P)[2:].zfill(2))
            else:
                if i == 2 or i == 3 or i == 4 or i == 6 or i == 8 or i == 9:
                    print("{:<22}".format(f'I:{hex(insIndex)[2:].zfill(4).upper()} {ins_s}'), end='')
                else:
                    print(f'I:{hex(insIndex)[2:].zfill(4).upper()} {ins_s}')
                if i == 2:
                    print(f"A   {hex(self.A)[2:].zfill(2)}")
                if i == 3:
                    print(f"X   {hex(self.X)[2:].zfill(2)}")
                if i == 4:
                    print(f"Y   {hex(self.Y)[2:].zfill(2)}")
                if i == 6:
                    print(f"PC  {hex(self.PC)[2:].zfill(4)}")
                if i == 8:
                    print(f"S   {hex(self.S)[2:].zfill(2)}")
                if i == 9:
                    print(f"P   {hex(self.P)[2:].zfill(2)}")
            insIndex = newInsIndex

        print()
        for i in range(10):
            if colors:
                print(u"\u001b[32;1m", end='') # green
            print(f'M:{hex(dataIndex)[2:].zfill(4).upper()}', end='')
            if colors:
                print(u"\u001b[36;1m", end='') # cyan
            for j in range(8):
                print(f' {hex(self.RAM[dataIndex])[2:].zfill(2)}', end='')
                dataIndex += 1
            print()
        
        if colors:
            print(u"\u001b[37;1m", end='') # white
        print(20 * "_")
        print('> ', end='')
        
        return

    # ---- MAIN LOOP ----

    def Run(self, debug = 0):
        self.PC = self.resetVector
        stepper = 0
        dataIndex = 0
        insIndex = self.PC

        while True:
            if debug == 1:
                insIndex = self.PC
                self.PrintDebug(insIndex, dataIndex)

            if debug == 1 and stepper == 0:
                exit = False
                while not exit:
                    command = input().split()
                    if command[0] == "step":
                        if len(command) == 1:
                            exit = True
                        else:
                            stepper = int(command[1])
                            exit = True
                    elif command[0] == "m":
                        dataIndex = int(command[1], 16)
                        self.PrintDebug(insIndex, dataIndex)   
                    elif command[0] == "i":
                        insIndex = int(command[1], 16)
                        self.PrintDebug(insIndex, dataIndex)
                    elif command[0] == "exit":
                        clear()
                        debug = 0
                        exit = True
                    else:
                        print("command not valid")
                        input()
                        self.PrintDebug(insIndex, dataIndex)
                    
            if stepper > 0:
                time.sleep(0.75)
                stepper -= 1

            ins = self.RAM[self.PC]
            if ins == 0x69:
                self.ADC(self.adrsMode["imm"])
            elif ins == 0x6D:
                self.ADC(self.adrsMode["abs"])
            elif ins == 0x18:
                self.CLC()
            elif ins == 0xCA:
                self.DEX()
            elif ins == 0xE8:
                self.INX()
            elif ins == 0x4C:
                self.JMP(self.adrsMode["abs"])
                continue
            elif ins == 0xA9:
                self.LDA(self.adrsMode["imm"])
            elif ins == 0xAD:
                self.LDA(self.adrsMode["abs"])
            elif ins == 0xA2:
                self.LDX(self.adrsMode["imm"])
            elif ins == 0xAE:
                self.LDX(self.adrsMode["abs"])
            elif ins == 0x8D:
                self.STA(self.adrsMode["abs"])
            elif ins == 0x8E:
                self.STX(self.adrsMode["abs"])
            elif ins == 0xAA:
                self.TAX()
            elif ins == 0x8A:
                self.TXA()
            else:
                print("instrctn not known")
                break
            self.PC += 1
        return

def clear():
        # for windows
        if os.name == 'nt':
            _ = os.system('cls')
        # for mac and linux(here, os.name is 'posix')
        else:
            _ = os.system('clear')

"""
ins to-do:
    x-indexed lda, sta, adc
    compare
    all/almostall branch instr

Debug mode !!! first

"""

cpu = CPU()
cpu.AssemblyInputFile()
cpu.Run(1)
print(cpu.A)