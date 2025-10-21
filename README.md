
# Python Interpreter

A lightweight interpreter written in Python that performs lexical analysis, parsing, and evaluation of a simplified programming language.  
This project was created to explore the core concepts of compiler and interpreter design, including tokenization, recursive descent parsing, and abstract syntax trees (ASTs).  
It supports arithmetic, boolean logic, variable assignment, and simple control flow statements such as `if` and `while`.

---

## Features

- Lexical analysis using regular expressions to tokenize input
- Parsing expressions and statements using recursive descent
- Evaluation of arithmetic and logical expressions
- Variable assignment and environment management
- Conditional and looping constructs (`if`, `while`)
- Interactive REPL for testing expressions and statements

---
## Example Usage

Run the program from the command line:

```bash
python interpreter.py
```

Then enter these commands into the REPL:

```
>>> x = 5;
>>> y = 2;
>>> if x > y then x + y else x - y;
7
>>> while x < 10 { x = x + 1; };
>>> x;
10
>>> quit
```
