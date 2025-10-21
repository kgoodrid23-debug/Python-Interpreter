# Python-Interpreter
This is a python interpreter/parser from my Programming Languages class. It's a custom-built interpreter written in Python that performs lexical analysis, parsing, and execution of a simplified programming language.  This project is a work in progress designed to deepen my understanding of compiler design, abstract syntax trees (ASTs), and recursive descent parsing.

---

## Features

**Lexical Analysis (Lexer)**
- Uses regular expressions to tokenize input code  
- Supports numbers, identifiers, operators, keywords, and comments  

**Parser (Recursive Descent)**
- Builds an abstract syntax tree (AST) for:
  - Arithmetic expressions  
  - Variable assignments  
  - Boolean expressions  
  - `if` / `then` / `else` conditionals  
  - `while` loops  

**Interpreter**
- Evaluates the AST and executes logic in real time  
- Maintains a variable environment for assignments and conditions  
- Supports:
  - Arithmetic: `+ - * /`
  - Logical operators: `and or not`
  - Comparisons: `< > ==`
  - Control flow: `if ... then ... else ...` and `while { ... }`

**Interactive REPL**
- Type commands directly into the console and see immediate results  
- Type `exit` or `quit` to leave the program  
```bash
python interpreter.py
