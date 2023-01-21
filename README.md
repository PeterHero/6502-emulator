# 6502 Emulator

The goal of this project is to create a functional emulation of 6502 CPU with python code.
It was created as a project for the class Programming 1 on MFF CUNI by Petr Hrdina.

## What is 6502

**6502** is an **8**-bit CPU with **16**-bit address space on RAM.

## Description

To see full documentation on 6502 see for example: https://www.masswerk.at/6502/6502_instruction_set.html  
The following description is about how this implementation differs and what it covers.

### Implemented Address Modes
<br>
A &emsp;&emsp;&nbsp;. . . Accumulator &emsp;&emsp;&emsp;&ensp;&nbsp;OPC A &emsp;&emsp;&emsp;&ensp;&nbsp; operand is AC (implied single byte instruction)  

abs &emsp;&ensp;. . . absolute &emsp;&emsp;&emsp;&emsp;&emsp;&nbsp; OPC $LLHH&emsp;&ensp; operand is address $HHLL *  

abs,X &ensp;. . . absolute, X-indexed &ensp;OPC $LLHH,X&emsp;operand is address; effective address is address incremented by X with carry *  

\# &emsp;&emsp;&nbsp;. . . immediate &emsp;&emsp;&emsp;&emsp;&ensp;&nbsp;OPC #$BB &emsp;&emsp; operand is byte BB  

impl &emsp;. . . implied &emsp;&emsp;&emsp;&emsp;&emsp;&emsp; OPC&emsp;&emsp;&emsp;&emsp;&emsp;operand implied  

rel &emsp;&ensp;&nbsp;. . . relative &emsp;&emsp;&emsp;&emsp;&emsp;&ensp;&ensp; OPC $BB&emsp;&emsp;&emsp;branch target is PC + signed offset BB  

\* in the assembly the parameter is interpreted as big-endian number

### Implemented Instructions

ADC . . . add with carry
- abs
- abs,X
- imm

AND . . . and (with accumulator)  
- abs
- imm

ASL . . . arithmetic shift left  
- A

BCC . . . branch on carry clear  
- imp

BCS . . . branch on carry set  
- imp

BEQ . . . branch on equal (zero set)  
- imp

BMI . . . branch on minus (negative set)  
- imp

BNE . . . branch on not equal (zero clear)  
- imp

BPL . . . branch on plus (negative clear)  
- imp

BRK . . . break / interrupt  
- imp
- Break instruction isn't needed to be in the code, because RAM is filled with $00, which is interpreted as brk.

CLC . . . clear carry  
- imp

CMP . . . compare (with accumulator)  
- abs
- abs,X
- imm

DEX . . . decrement X  
- imp

DEY . . . decrement Y  
- imp

EOR . . . exclusive or (with accumulator)  
- abs
- imm

INX . . . increment X  
- imp

INY . . . increment Y  
- imp

JMP . . . jump  
- abs

LDA . . . load accumulator  
- abs
- abs,X
- imm
LDX . . . load X  
- abs
- imm

LDY . . . load Y  
- abs
- abs,X
- imm

LSR . . . logical shift right  
- A

ORA . . . or with accumulator  
- abs
- imm

ROL . . . rotate left  
- A

ROR . . . rotate right  
- A

SBC . . . subtract with carry  
- abs
- abs,X
- imm

SEC . . . set carry  
- imp

STA . . . store accumulator  
- abs
- abs,X

STX . . . store X  
- abs

STY . . . store Y  
- abs

TAX . . . transfer accumulator to X  
- imp

TAY . . . transfer accumulator to Y  
- imp

TXA . . . transfer X to accumulator  
- imp

TYA . . . transfer Y to accumulator   
- imp

### Registers

Internal registers are 8-bit in not said otherwise:

- **A** - accumulator which can be loaded with data. Arithmetic operations can be performed on it.
- **X** - register which can be loaded with data, which can be incremented or decremented. Used to perform x-indexed operations (see addressing modes)
- **Y** - same function as the X register, but in this version cannot be used to perform y-indexed operations
- **PC** - program counter is 16-bit register that determines at what location in memory is the current instruction
- **S** - stack register points to current address of stack in memory - is not used in this version
- **P** - status register with bits representing flags

#### Status register flags (bit 7 to bit 0)

N . . . . Negative  
V . . . . Overflow  
\- . . . . ignored  
B . . . . Break  
D . . . . Decimal  
I . . . . Interrupt  
Z . . . . Zero  
C . . . . Carry 

- the **zero flag** (Z) indicates if all bits are zero and  
the **negative flag** (N) indicates if the 7th-bit - viewed also as the sign bit - is set
    - These flags are always updated, whenever a value is transferred to a CPU register (A,X,Y) and as a result of any logical ALU operations. The Z and N flags are also updated by increment and decrement operations.
- The **carry flag** (C) flag is used as a buffer and as a borrow in arithmetic operations. Any comparisons will update this additionally to the Z and N flags, as do shift and rotate operations.
- All arithmetic operations update the Z, N, C and V flags.
- The carrry flag may be set by an instruction. There are also branch instructions to conditionally divert the control flow depending on the respective state of the Z, N or C flag.
- Function of other flags is not implemented in this version and cannot be used.

## Config.txt

config.txt is the configuration file for the program on how to run.

### Source
You can choose **'file'** or **'console'** input.  
If **file** is chosen the program takes input from 'in.txt'.  
The input has to be formatted in a specific way - see format.  
In **console** format you end the input by an empty line.

### Format

You can choose **'assembly'** or **'hex'** (stands for hexadecimal).  

For **assembly input**: one instruction on a line.  
Example: "jmp $0123"  
For each address mode you have to exactly follow the pattern which is explicitely said - see the Implemented Address Modes. Remember that 16-bit numbers are in assembly interpreted big-endian.

For **hexadecimal input**: Bytes (two hex numbers - 'A9') separated by a single space. There isn't limited amount of bytes on a line, but it cannot and with a space. Remember that 6502 is a little-endian processor when using instructions with abs modes.

### Color

You can choose **'on'** or **'off'**.  
The color is created by printing 'escape ANSI codes', some consoles on older systems don't support it (e.g. cmd on Windows 8).  
If everything works fine leave it on.

### Mode

You can choose **'run'** or **'debug'**.  
In the **run** mode the program runs until ended by an brk instruction. At the end an interactive debug screen is printed where you can see instructions (on the screen the data in memory is interpreted as instructions in assembly) and data in the form of hexdump on specific address in memory.  
You can use **commands** to interact with the screen:
- **'i 0xHHLL'** - set instruction start address for printing to $HHLL
- **'m 0xHHLL'** - set data start address for printing to $HHLL
- **'exit'** - exits the program

In the **debug** mode the program freezes at the start and the interactive debug screen is printed.
You can use **commands** to interact with the screen in addition to the ones in the run mode:
- **'step'** - executes one instruction
- **'step x'** - executes x instructions with pausing for a little after each instruction
- **'qstep x'** - executes x instructions without pausing inbetween
- **'end'** - skip to the end of the program and print the interactive end debug screen

## Start vector

The program always starts on the address **$8000** in RAM and every input loads the program to memory starting from **$8000**.

## Tests

The project includes tests in the src/tests folder. To run the test move the file to the src folder, rename it to 'in.txt' and set up correctly the 'config.txt'.

### Bubble Sort

In the file 'bubbleSort.txt' is the code for bubble sort test. The program loads numbers to $0000 in RAM and then sorts them with bubble sort.

### Fibonacci

In the file 'fibonacci.txt' is the code for fibonacci test. The program generates 2-byte fibonacci numbers in $0000 in RAM until one overflows the 2-byte limit (is bigger than 65536), the other is the biggest 2-byte fibonacci number.

### Self destruct

In the file 'self-destruct.txt' is the code for self destruct test.
The program is stores into the RAM number $FF on address $80ff and decreasing, until rewriting the program itself and jumping to break.

## In case of problem

In case of error make sure your input in console or file 'in.txt' is correctly formated and that the files 'in.txt' and 'config.txt' are present in the src directory and that the config.txt is correctly set.