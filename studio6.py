# /mnt/data/studio4.py
import re

# Added STRING, LBRACK, RBRACK tokens as requested by Part A
SPEC = [
    ("NUM", r"\d+"),
    ("STRING", r'"([^"\\]|\\.)*"'),   # double-quoted string (supports simple backslash escapes)
    ("IF", r"\bif\b"),
    ("WHILE", r"\bwhile\b"),
    ("ELSE", r"\belse\b"),
    ("TRY", r"\btry\b"),
    ("CATCH", r"\bcatch\b"),
    ("RAISE", r"\braise\b"),
    ("DEF", r"\bdef\b"),
    ("RETURN", r"\breturn\b"),
    ("REF", r"\bref\b"),
    ("ID", r"[A-Za-z_]\w*"),
    ("PLUS", r"\+"), ("MINUS", r"-"),
    ("STAR", r"\*"), ("SLASH", r"/"),
    ("EQ", r"=="),
    ("LT", r"<"), ("GT", r">"),
    ("AND", r"\band\b"), ("OR", r"\bor\b"), ("NOT", r"\bnot\b"),
    ("ASSIGN", r"="),
    ("SEMI", r";"),
    ("COMMA", r","),
    ("LPAREN", r"\("), ("RPAREN", r"\)"),
    ("LBRACE", r"\{"), ("RBRACE", r"\}"),
    ("LBRACK", r"\["), ("RBRACK", r"\]"),  # array indexing / literals
    ("WS", r"[ \t\r\n]+"),
    ("COMMENT", r"#.*"),
]

tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in SPEC)
get_token = re.compile(tok_regex).match

def lex(code):                             # step 1. Converts the raw code into one of the tokens above
    position = 0
    tokens = []
    while position < len(code):
        match = get_token(code, position)
        if not match:
            raise SyntaxError(f"Unexpected character {code[position]!r} at position {position}")
        kind = match.lastgroup
        value = match.group(kind)
        if kind not in ("WS", "COMMENT"):
            tokens.append((kind, value))
        position = match.end()
    tokens.append(("EOF",""))
    return tokens


class Number:
    def __init__(self, value): self.value = int(value)

class String:
    def __init__(self, raw): 
        # raw includes quotes; store processed Python string
        # remove surrounding quotes and unescape common sequences
        s = raw[1:-1]
        self.value = bytes(s, "utf-8").decode("unicode_escape")

class ArrayLiteral:
    def __init__(self, elements): self.elements = elements  # list of AST expressions

class BinOp:
    def __init__(self, left, op, right):
        self.left, self.op, self.right = left, op, right

class Bool:
    def __init__(self, value):
        self.value = bool(value) if not isinstance(value, str) else value.lower() in ("true","1")

class UnaryOp:
    def __init__(self, op, operand): self.op, self.operand = op, operand

class FunctionDef:
    def __init__(self, name, params, body): self.name, self.params, self.body = name, params, body

class Call:
    def __init__(self, func_expr, args): self.func_expr, self.args = func_expr, args

class FunctionValue:
    def __init__(self, params, body, env): self.params, self.body, self.env = params, body, env

class BuiltinFunction:
    def __init__(self, fn, arity=None):
        self.fn = fn
        self.arity = arity

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent
    def define(self, name, value): self.vars[name] = value
    def get(self, name):
        if name in self.vars: return self.vars[name]
        elif self.parent: return self.parent.get(name)
        else: raise NameError(f"Undefined variable '{name}'")
    def set(self, name, value):
        if name in self.vars: self.vars[name] = value
        elif self.parent: self.parent.set(name, value)
        else: raise NameError(f"Undefined variable '{name}'")

class Assign:
    def __init__(self, name, value): self.name, self.value = name, value

class AssignIndex:
    def __init__(self, name, indices, value):
        # name: string (variable name)
        # indices: list of AST expressions
        # value: AST expression to assign
        self.name, self.indices, self.value = name, indices, value

class Var:
    def __init__(self, name): self.name = name

class Index:
    def __init__(self, collection, index): self.collection, self.index = collection, index

class IfExpression:
    def __init__(self, condition, then_branch, else_branch):
        self.condition, self.then_branch, self.else_branch = condition, then_branch, else_branch

class WhileLoop:
    def __init__(self, condition, body): self.condition, self.body = condition, body

class Return:
    def __init__(self, value):
        self.value = value

class ReturnException(Exception):
    def __init__(self, value):
        self.value = value

class Reference:
    def __init__(self, env, name):
        self.env = env
        self.name = name

    def get(self):
        return self.env.get(self.name)

    def set(self, value):
        self.env.set(self.name, value)

class Raise:
    def __init__(self, expr):
        self.expr = expr

class TryBlock:
    def __init__(self, body, catch_name, catch_body):
        self.body = body
        self.catch_name = catch_name
        self.catch_body = catch_body

class ThrownException(Exception):
    def __init__(self, value):
        self.value = value


class Interpreter:                  
    def __init__(self):
        self.env = Environment()
        # Register builtin `len` as requested in Part B
        self.env.define("len", BuiltinFunction(self._builtin_len, arity=1))
        self.env.define("print", BuiltinFunction(self._builtin_print))

    def _builtin_print(self, args):
        # Convert each arg to string (Studio spec)
        print(*args)
        return None

    def _builtin_len(self, args): 
        if len(args) != 1:
            raise TypeError("len expects 1 argument")
        coll = args[0]
        if isinstance(coll, (list, str)):
            return len(coll)
        raise TypeError("len expects array or string")

    def evaluate(self, node, env=None):         # Since this gets called for every node in the tree, every node will run through this. 
        if env is None: env = self.env

        if isinstance(node, Number): 
            return node.value

        elif isinstance(node, String):
            return node.value

        elif isinstance(node, Bool):            # These are self-explanatory. 
            return node.value

        elif isinstance(node, ArrayLiteral):
            # Evaluate each element expression and return a *mutable* Python list
            return [self.evaluate(e, env) for e in node.elements]        # Used AI for this 

        elif isinstance(node, BinOp):       # BinOp = binary operation. This is for PEMDAS and AND/OR
            # Arithmetic/comparison/logic. Basic type-checking for clarity.
            op = node.op[0]
            # For logical operators, implement short-circuit semantics
            if op == "AND":
                left = self.evaluate(node.left, env)
                if isinstance(left, Reference): left = left.get()
                if not left:
                    return left
                right = self.evaluate(node.right, env)
                if isinstance(right, Reference): right = right.get()
                return right
            if op == "OR":
                left = self.evaluate(node.left, env)
                if isinstance(left, Reference): left = left.get()
                if left:
                    return left
                right = self.evaluate(node.right, env)
                if isinstance(right, Reference): right = right.get()
                return right

            left = self.evaluate(node.left, env)
            right = self.evaluate(node.right, env)
            if isinstance(left, Reference): left = left.get()   # If it's calling another function
            if isinstance(right, Reference): right = right.get()

            if op == "PLUS":
                # support number+number, string+string, list+list concatenation
                if isinstance(left, (int)) and isinstance(right, (int)):
                    return left + right
                if isinstance(left, str) and isinstance(right, str):
                    return left + right
                if isinstance(left, list) and isinstance(right, list): 
                    return left + right        # This is essentially safeguarding someone trying to add two incompatible variables.
                raise TypeError("Unsupported operand types for +")
            if op == "MINUS":
                if isinstance(left, int) and isinstance(right, int):
                    return left - right
                raise TypeError("Unsupported operand types for -")
            if op == "STAR":
                if isinstance(left, int) and isinstance(right, int):
                    return left * right
                raise TypeError("Unsupported operand types for *")
            if op == "SLASH":
                if isinstance(left, int) and isinstance(right, int):
                    if right == 0:
                        raise ZeroDivisionError("division by zero")     # AI recommended I throw this in so I did
                    # keep integer division semantics consistent with earlier spec decisions
                    return left // right
                raise TypeError("Unsupported operand types for /")
            if op == "EQ": return left == right
            if op == "LT": return left < right
            if op == "GT": return left > right

        elif isinstance(node, UnaryOp):         # AI recommended this. This is basically if we're dealing with a negative variable
            val = self.evaluate(node.operand, env)
            if node.op[0] == "NOT": return not val
            if node.op[0] == "MINUS":
                if not isinstance(val, int): raise TypeError("Unary - expects number")
                return -val

        elif isinstance(node, Assign):
            val = self.evaluate(node.value, env)
            try:
                env.set(node.name, val)         # If x exists
            except NameError:
                env.define(node.name, val)      # If x doesn't exist yet
            return val

        elif isinstance(node, AssignIndex):     # Had to use AI for this one - pretty complex for me
            # Assign to array element: name[indices...] = value
            # Evaluate value first
            val = self.evaluate(node.value, env)
            # fetch the base container by variable name (must exist)
            container = env.get(node.name)
            # If the stored variable is a Reference-like object from ref param,
            # env.get will return the referenced *value* (mutating the list will still mutate the original).
            # Walk indices to the penultimate container
            if not node.indices:
                raise SyntaxError("Missing index for indexed assignment")
            cur = container
            for idx_ast in node.indices[:-1]:
                idx = self.evaluate(idx_ast, env)
                if isinstance(idx, Reference): idx = idx.get()
                if not isinstance(idx, int):
                    raise TypeError("Index must be an integer")
                if not isinstance(cur, list):
                    raise TypeError("Indexed assignment only allowed on arrays (intermediate element not array)")
                cur = cur[idx]
            # now cur is the container whose element we will set
            final_idx = self.evaluate(node.indices[-1], env)
            if isinstance(final_idx, Reference): final_idx = final_idx.get()
            if not isinstance(final_idx, int):
                raise TypeError("Index must be an integer")
            if not isinstance(cur, list):
                # explicit TypeError per assignment spec: only arrays are mutable/index-assignable
                raise TypeError("Indexed assignment only allowed on arrays")
            # MUTABILITY NOTE:
            # We mutate the Python list object `cur` in place. This is intentional:
            # arrays in the language are mutable containers — writing `a[0] = x`
            # modifies the existing array object stored in the variable `a`.
            cur[final_idx] = val
            return val

        elif isinstance(node, Var):
            val = env.get(node.name)            # Fetches a variable
            if isinstance(val, Reference):
                return val.get()
            return val

        elif isinstance(node, Index):
            # index read: collection[index]
            coll = self.evaluate(node.collection, env)  # Gets the type of whatever object it is.
            if isinstance(coll, Reference):
                coll = coll.get()
            idx = self.evaluate(node.index, env)
            if isinstance(idx, Reference):
                idx = idx.get()
            if not isinstance(idx, int):
                raise TypeError("Index must be integer")
            # allow read from arrays and strings
            if isinstance(coll, list):
                return coll[idx]
            if isinstance(coll, str):
                # return single-character string
                return coll[idx]
            raise TypeError("Indexing only supported on arrays and strings")

        elif isinstance(node, IfExpression):    
            cond = self.evaluate(node.condition, env)   # Gets the condition and then evaluates if it's true or not
            branch = node.then_branch if cond else node.else_branch
            result = None
            for stmt in branch: val = self.evaluate(stmt, env); result = val if val is not None else result
            return result

        elif isinstance(node, WhileLoop):
            result = None                           # Loops until val is none and condition is false
            while self.evaluate(node.condition, env):
                for stmt in node.body: 
                    val = self.evaluate(stmt, env); result = val if val is not None else result
            return result

        elif isinstance(node, FunctionDef):
            func_val = FunctionValue(node.params, node.body, env) # Used AI for this part
            env.define(node.name, func_val)
            return None

        elif isinstance(node, Call):
            func = self.evaluate(node.func_expr, env)
            # Builtin function handling
            if isinstance(func, BuiltinFunction):
                # evaluate args and pass Python values
                args = [self.evaluate(a, env) for a in node.args]
                return func.fn(args)

            if not isinstance(func, FunctionValue):
                raise TypeError("Attempted to call a non-function")

            # Prepare arguments
            if len(node.args) != len(func.params):  # If the arguments entered are too many or too few characters
                raise TypeError("Argument count mismatch")

            local_env = Environment(func.env)   # Builds the function it's own environment
    
            for (is_ref, param_name), arg_node in zip(func.params, node.args):  # Had to use AI for this part
                if is_ref:
                    # ref parameter must be a variable
                    if not isinstance(arg_node, Var):
                        raise TypeError(f"ref parameter '{param_name}' must be a variable")
                    # Bind a Reference into the callee's environment that points to the caller's env variable.
                    local_env.define(param_name, Reference(env, arg_node.name))
                else:
                    # by-value: evaluate now
                    val = self.evaluate(arg_node, env)
                    local_env.define(param_name, val)

            # Execute function body
            result = None
            try:
                for stmt in func.body:
                    self.evaluate(stmt, local_env)
            except ReturnException as r:
                result = r.value
            return result

        elif isinstance(node, Return):
            val = self.evaluate(node.value, env) # Return x
            raise ReturnException(val)
        elif isinstance(node, Raise):
            val = self.evaluate(node.expr, env) # Raise x
            raise ThrownException(val)
        elif isinstance(node, TryBlock):
            try:
                # run try block
                result = None
                for stmt in node.body:
                    v = self.evaluate(stmt, env)
                    if v is not None:
                        result = v
                return result
            except ThrownException as exc:
                # create a new environment for catch
                local_env = Environment(env)
                local_env.define(node.catch_name, exc.value)

                result = None
                for stmt in node.catch_body:
                    v = self.evaluate(stmt, local_env)
                    if v is not None:
                        result = v
                return result
        else:
            raise TypeError(f"Unknown node type: {type(node)}")

class Parser:                   # step 2 - builds the AST tree
    def __init__(self, tokens): self.tokens, self.pos = tokens, 0
    def current(self): return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF","")  # Gets current token
    def peek(self, offset=1):
        i = self.pos + offset
        return self.tokens[i] if i < len(self.tokens) else ("EOF","") # Check the next token without consuming. AI recommended this
    def eat(self, kind):
        if self.current()[0] == kind: self.pos += 1
        else: raise SyntaxError(f"Expected {kind}, got {self.current()[0]}") # Consume the current token and move on

    def parse(self):
        nodes = []
        while self.current()[0] != "EOF": # This method stops at the end of the file
            nodes.append(self.statement())
            if self.current()[0] == "SEMI": self.eat("SEMI")
        return nodes

    def statement(self):
        tok = self.current()[0]

        if tok == "DEF":
            return self.parse_function_def()

        elif tok == "RETURN":
            self.eat("RETURN")
            expr = self.expr()
            if self.current()[0] == "SEMI": self.eat("SEMI")
            return Return(expr)

        elif tok == "RAISE":
            self.eat("RAISE")
            expr = self.expr()
            if self.current()[0] == "SEMI": self.eat("SEMI")
            return Raise(expr)

        elif tok == "TRY":
            return self.parse_try()

        else:
            return self.assignment()  # If the token isn't a statement, recursive descent downward
        
    def parse_try(self):
        self.eat("TRY")
        try_body = self.parse_block()

        self.eat("CATCH")
        self.eat("LPAREN")
        if self.current()[0] != "ID":
            raise SyntaxError("Expected identifier in catch(...)")
        catch_name = self.current()[1]
        self.eat("ID")
        self.eat("RPAREN")

        catch_body = self.parse_block()

        return TryBlock(try_body, catch_name, catch_body)

    def parse_function_def(self):
        self.eat("DEF")
        if self.current()[0] != "ID":
            raise SyntaxError("Expected function name after 'def'")
        name = self.current()[1]; self.eat("ID")
        params = []
        self.eat("LPAREN")
        while self.current()[0] != "RPAREN":
            is_ref = False
            if self.current()[0] == "REF":
                is_ref = True
                self.eat("REF")
            if self.current()[0] != "ID":
                raise SyntaxError("Expected parameter name")
            param_name = self.current()[1]; self.eat("ID")
            params.append((is_ref, param_name))
            if self.current()[0] == "COMMA": self.eat("COMMA")
            else: break
        self.eat("RPAREN")
        body = self.parse_block()
        return FunctionDef(name, params, body)

    def assignment(self):
        if self.current()[0] == "ID":
            # Peek for simple assignment
            if self.peek()[0] == "ASSIGN":
                name = self.current()[1]; self.eat("ID")
                self.eat("ASSIGN")
                return Assign(name, self.conditional())
            # Peek for indexed assignment (arr[...]=...)
            if self.peek()[0] == "LBRACK":
                # parse name and a sequence of index expressions
                name = self.current()[1]; self.eat("ID")
                indices = []
                while self.current()[0] == "LBRACK":
                    self.eat("LBRACK")
                    indices.append(self.expr())
                    self.eat("RBRACK")
                # If followed by ASSIGN, create AssignIndex; otherwise fall back to an expression
                if self.current()[0] == "ASSIGN":
                    self.eat("ASSIGN")
                    return AssignIndex(name, indices, self.conditional())
                # not an assignment -> build Index/Var chain and return as expression
                node = Var(name)
                for idx_ast in indices:
                    node = Index(node, idx_ast)
                return node
        return self.conditional() # Recursive Descent downward

    def conditional(self):
        if self.current()[0] == "IF":
            self.eat("IF")
            cond = self.logic()
            then_branch = []
            if self.current()[0] == "LBRACE": then_branch = self.parse_block()
            else: then_branch = [self.expr()]
            if self.current()[0] == "ELSE":
                self.eat("ELSE")
                else_branch = self.parse_block() if self.current()[0] == "LBRACE" else [self.expr()]
            else: else_branch = []
            return IfExpression(cond, then_branch, else_branch)
        elif self.current()[0] == "WHILE":
            self.eat("WHILE")
            cond = self.logic()
            body = self.parse_block()
            return WhileLoop(cond, body)
        else: return self.logic() # Recursive descent downward

    def logic(self):
        node = self.expr() # Recursive descent downward
        while self.current()[0] in ("EQ","LT","GT","AND","OR"):
            op = self.current(); self.eat(op[0])
            node = BinOp(node, op, self.expr())
        return node

    def expr(self):
        node = self.term() # Recursive Descent downward
        while self.current()[0] in ("PLUS","MINUS"):
            op = self.current(); self.eat(op[0])
            node = BinOp(node, op, self.term())
        return node

    def term(self):
        node = self.factor() # Recursive Descent downward
        while self.current()[0] in ("STAR","SLASH"):
            op = self.current(); self.eat(op[0])
            node = BinOp(node, op, self.factor())
        return node

    def factor(self): # This is the bottom level of my Recursive Descent
        tok = self.current()
        if tok[0] == "NUM": self.eat("NUM"); return Number(tok[1])
        elif tok[0] == "STRING":
            self.eat("STRING")
            return String(tok[1])
        elif tok[0] == "ID":
            name = tok[1]; self.eat("ID")
            node = Var(name)
            # allow calls after any primary, and allow indexing
            while True:
                if self.current()[0] == "LPAREN":
                    args = self.parse_argument_list()
                    node = Call(node, args)
                    continue
                if self.current()[0] == "LBRACK":
                    # parse single index and wrap into Index node
                    self.eat("LBRACK")
                    idx = self.expr()
                    self.eat("RBRACK")
                    node = Index(node, idx)
                    continue
                break
            return node
        elif tok[0] == "LBRACK":
            # array literal: [ a, b, c ]
            self.eat("LBRACK")
            elements = []
            while self.current()[0] != "RBRACK":
                elements.append(self.expr())
                if self.current()[0] == "COMMA": self.eat("COMMA")
                else: break
            self.eat("RBRACK")
            return ArrayLiteral(elements)
        elif tok[0] == "PLUS": self.eat("PLUS"); return self.factor()
        elif tok[0] == "MINUS": self.eat("MINUS"); return UnaryOp(("MINUS","-"), self.factor())
        elif tok[0] == "NOT": self.eat("NOT"); return UnaryOp(("NOT","not"), self.factor())
        elif tok[0] == "LPAREN":
            self.eat("LPAREN"); node = self.expr(); self.eat("RPAREN")
            while self.current()[0] == "LPAREN":
                args = self.parse_argument_list()
                node = Call(node, args)
            return node
        else: raise SyntaxError(f"Unexpected token {tok}")

    def parse_argument_list(self):
        args = []
        self.eat("LPAREN")
        while self.current()[0] != "RPAREN":
            args.append(self.expr())
            if self.current()[0] == "COMMA": self.eat("COMMA")
            else: break
        self.eat("RPAREN")
        return args

    def parse_block(self):
        self.eat("LBRACE")
        stmts = []
        while self.current()[0] != "RBRACE":
            stmts.append(self.statement())
            if self.current()[0] == "SEMI": self.eat("SEMI")
        self.eat("RBRACE")
        return stmts

def run(code):
    tokens = lex(code)
    parser = Parser(tokens)
    tree = parser.parse()
    interp = Interpreter()

    last_value = None

    try:
        for node in tree:
            val = interp.evaluate(node)
            # ignore built-in function definitions
            if val is not None and not isinstance(val, BuiltinFunction):
                last_value = val
    except ThrownException as e:
        raise RuntimeError(f"Uncaught exception: {e.value}")

    return last_value

def repl():
    interp = Interpreter()
    while True:
        try:
            line = input(">>> ")
            if line.strip() in ("exit", "quit"):    # If any of the words entered are exit or quit
                break
            tokens = lex(line)
            # For REPL convenience accept single-line statements without semicolon
            if len(tokens) >= 2 and tokens[-2][0] != "SEMI":
                tokens.insert(-1, ("SEMI",";"))
            parser = Parser(tokens)
            tree = parser.parse()           
            result = None
            for node in tree:
                val = interp.evaluate(node)
                if val is not None:
                    result = val
            if result is not None:
                print(result)
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__": repl()
