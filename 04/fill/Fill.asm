// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/04/Fill.asm

// Runs an infinite loop that listens to the keyboard input.
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel;
// the screen should remain fully black as long as the key is pressed. 
// When no key is pressed, the program clears the screen, i.e. writes
// "white" in every pixel;
// the screen should remain fully clear as long as no key is pressed.

// Put your code here.

(LOOP)
    @24576 // check screen
    D=M
    @WHITE
    D;JEQ
    @0
    D=A
    D=D-1
    @R3
    M=D
    @GG
    0;JMP
(WHITE)
    @0
    D=A
    @R3 // black or white
    M=D
    @R1 //loop variable
    M=D
(GG)
    @8192
    D=A 
    @R1
    M=D
(WRITELOOP)
    @R1
    D=M
    @LOOP
    D;JEQ
    @R1
    M=M-1 
    @SCREEN
    D=A
    @R1
    D=D+M // address
    @R2 // address variable
    M=D
    @R3
    D=M
    @R2
    A=M
    M=D
    @WRITELOOP
    0;JMP