GPP to RISC-V Compiler

A custom compiler written in Python that translates **GPP** (a procedural language with Greek syntax) into **RISC-V Assembly**.

This project implements the full compilation pipeline, including lexical analysis, symbol table management, intermediate code generation, and final target code generation for the RISC-V architecture.

## Features

* **Lexical Analysis:** Tokenizes source code, handling language-specific keywords, operators, and delimiters.
* **Symbol Table:** Manages variable declarations, scope levels, and memory addresses.
* **Syntax Analysis:** Implements a Recursive Descent Parser to validate the grammatical structure of the code.
* **Intermediate Code:** Generates platform-independent Quadruples (Quads).
* **Target Code Generation:** Translates intermediate code into executable RISC-V Assembly (`.asm`).
* **Error Handling:** Detects and reports syntax errors, undeclared variables, and duplicate declarations.
Tech Stack

* **Language:** Python 3.x
* **Target Architecture:** RISC-V
* **Paradigms:** Object-Oriented Programming (OOP)

## Project Structure

```text
.
├── GPP_compiler.py       # Main compiler logic (Lexer, Parser, Generator)
├── input.gpp             # (Example) Source code file
├── input.int             # (Output) Intermediate code
├── input.sym             # (Output) Symbol table dump
└── input.asm             # (Output) Final RISC-V Assembly
