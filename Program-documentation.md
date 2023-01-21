# Program documentation

The core of the program is in the class 'CPU'.  
All the data in the registers and RAM are 8-bit (PC is 16-bit), so modulo operation is needed every time the number can overflow.

Methods in the CPU class are divided in groups depending on their purpose:
- get flag methods
- set flag methods
- helper methods
- instruction methods
- input 
- debug mode 
- main loop

## Get flag methods

These methods return value of flag in the status register using bit operation on the P register.

## Set flag methods

These ethods set flag in the status register to value (0 or 1) using bit operation on the P register.

## Helper

### IsNegative

Method returns boolean value whether the 8-bit number is negative in the two's complement - if the MSb is 1.

### UpdateStatusRegister

Allows to set multiple flags to 1, 0 or asign it a value based on value in the A, X or Y register.  
Parameters [flag]=[value], value 1, 0 to set the flag to the value, value -1, -2, -3 to adjust the flag value based on the meaning of the flag and the value of A, X, Y respectively.

## Instruction methods

Implemented instructions with a parameter thisMode which is the address mode of the performed instruction. Each instruction increments correctly the Program Counter based on how much parameters did it use. It also sets the correct flags.

## Input methods

There are 4 input methods based on the input source and format. Assembly input methods use 'Translate' method which interprets assembly instructions to hexadecimal and put them into RAM.

## Debug mode

### Encode

Interprets hexadecimal value in memory on the address of PC as an assembly instruction and returns the string.

### PrintDebug

Handles printing the debug screen. If colors are on in config.txt prints escape ANSI codes which are interpreted as color setting by the console.

## Main loop

Method Run is the main loop of the program. With each iteration of the while loop the program executes one instruction. In the debug mode there are also implemented interactive commands, which determine the run of the program - if it steps, q(uick)steps, skips to the end or exits. After the program of the CPU is ended by a brk instruction an interactive debug screen is handled.

## Other

### clear

Function clear handles the clearing of the screen of the console depending on OS on which is the program running.

### configuration

Code at the end of the program reads the config.txt and hadles corresponding input from the user and starts the program in corresponding mode and with color setting on or of.