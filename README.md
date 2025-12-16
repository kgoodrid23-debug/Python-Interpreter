This project extends a custom mini-interpreter with exception handling support, including raise, try/catch, and proper exception propagation. The interpreter is implemented in Python.

Features Implemented:
Exception Handling

raise expr interrupts normal execution and throws a runtime exception

try { ... } catch(e) { ... } handles exceptions with correct scoping

Thrown values are bound to the catch variable

Exceptions bubble upward through nested try/catch blocks

Uncaught exceptions terminate execution with a runtime error

Runtime Semantics

Statements execute in order

Code after raise is skipped

try acts as an exception boundary

catch executes only when an exception occurs

Execution resumes normally after a handled exception

Interpreter Features

Recursive-descent parser

AST-based evaluation

Lexical scoping via environments

Built-in functions:

print(...)

len(array | string)

Array literals and indexing

Mutable arrays with index assignment

🧠 Example
try {
    print(1);
    raise 99;
    print(2);
} catch(e) {
    print("caught", e);
}
print(3);


Output:

1
caught 99
3

🧪 Tests

The project includes a comprehensive pytest test suite that validates:

Basic exception catching

Skipping execution after raise

Nested try/catch behavior

Exception bubbling

Uncaught exception termination

Array creation, indexing, and mutation

Built-in len on arrays and strings

Type errors for invalid indexing

All Studio 6 acceptance tests pass.

Running the Interpreter:
REPL Mode
python studio6.py

Run Tests:
python -m pytest tests_studio6.py -q

Project Structure:
studio6.py          # Lexer, parser, AST, interpreter
tests_studio6.py    # Pytest test suite for Studio 6
README.md           # Project documentation

Extra Notes:

print() outputs values but does not return them (by design).

Return values come from expression evaluation, not side effects.
>>> while x < 10 { x = x + 1; };
>>> x;
10
>>> quit
```
