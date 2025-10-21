import re # Import Regular Expressions (regex) library
# 1) List token patterns (what to recognize)
SPEC = [
    ("NUM", r"\d+"),
    ("IF", r"\bif\b"),
    ("WHILE", r"\bwhile\b"),
    ("ELSE", r"\belse\b"),
    ("THEN", r"\bthen\b"),
    ("ID", r"[A-Za-z_]\w*"),
    ("PLUS", r"\+"), ("MINUS", r"-"),
    ("STAR", r"\*"), ("SLASH", r"/"),
    ("CARET", r"\^"),
    ("EQ", r"=="),
    ("LT", r"<"),
    ("GT", r">"),
    ("AND", r"\band\b"),
    ("OR", r"\bor\b"),
    ("NOT", r"\bnot\b"),
    ("ASSIGN", r"="),
    ("SEMI", r";"),
    ("LPAREN", r"\("),
    ("RPAREN", r"\)"),
    ("LBRACE", r"\{"),
    ("RBRACE", r"\}"),
    ("WS", r"[ \t\r\n]+"),
    ("COMMENT", r"#.*"),
]

# Had to look this regex syntax up - still kinda confused
tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in SPEC) 
get_token = re.compile(tok_regex).match

def lex(code):
    position = 0
    tokens = []
    while position < len(code):
        match = get_token(code,position)
        if not match:
            raise SyntaxError(f"You have the wrong characer: {code[position]!r} at position {position}")
        kind = match.lastgroup
        value = match.group(kind)     # This line was confusing for me - definetly had to look this up
        
        if kind not in ("WS", "COMMENT"):   # Ignore the spaces and comments
            tokens.append((kind, value))
        
        position = match.end()
    return tokens

class Number: # if its a number, go through and just set it equal to that value
    def __init__(self,value):
            self.value = int(value)

class BinOp:  # if its a binary operation, make sure we have the left and right as well as the op (+, -, etc) defined
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right

class Bool: 
    def __init__(self, value):
        if isinstance(value, str):
            self.value = value.lower() in ("true", "1")
        else:
            self.value = bool(value)

class UnaryOp:
     def __init__(self, op, operand):
          self.op = op
          self.operand = operand

class Environment:
    def __init__(self):
        self.vars = {}

    def define(self, name, value):
        self.vars[name] = value

    def get(self, name):
        if name not in self.vars:
            raise NameError(f"Undefined variable '{name}'")
        return self.vars[name]

    def set(self, name, value):
        if name not in self.vars:
            raise NameError(f"Undefined variable '{name}'")
        self.vars[name] = value

class Assign:
    def __init__(self, name, value):
        self.name = name
        self.value = value 

class Var:
    def __init__(self, name):
        self.name = name

class IfExpression:
    def __init__(self, condition, then_branch, else_branch):
        self.condition = condition
        self.then_branch = then_branch    # Had to look these up since this is different from my other AST Nodes
        self.else_branch = else_branch    # This too

class WhileLoop:
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body

class Interpreter:
    def __init__(self):
        self.env = Environment()

    def evaluate(self, node):
        if isinstance(node, Number):
            return node.value

        elif isinstance(node, Bool):
            return node.value

        elif isinstance(node, BinOp): # If its an actual binary operation or expression
            left = self.evaluate(node.left)
            right = self.evaluate(node.right)
            op = node.op[0]

            if op == "PLUS": return left + right
            if op == "MINUS": return left - right
            if op == "STAR": return left * right
            if op == "SLASH": return left / right
            if op == "EQ": return left == right
            if op == "LT": return left < right
            if op == "GT": return left > right
            if op == "AND": return left and right
            if op == "OR": return left or right

        elif isinstance(node, UnaryOp):
            operand = self.evaluate(node.operand)
            if node.op[0] == "NOT":
                return not operand

        elif isinstance(node, Assign):
            value = self.evaluate(node.value)
            if node.name in self.env.vars:
                self.env.set(node.name, value)
            else:
                self.env.define(node.name, value)
            return value


        elif isinstance(node, Var):
            return self.env.get(node.name)
        
        elif isinstance(node, IfExpression):
            condition = self.evaluate(node.condition)
            if condition:
                return self.evaluate(node.then_branch)
            else:
                return self.evaluate(node.else_branch)
        
        elif isinstance(node, WhileLoop):
            result = None
            while self.evaluate(node.condition):
                for stmt in node.body:
                    result = self.evaluate(stmt)
            return result



class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def current(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "") # Looked it up and said EOF is good to have for the end of the file so it knows when to stop

    def eat(self, kind):              #change positions if the current token matches one from SPECS
        if self.current()[0] == kind:
            self.pos += 1
        else:
            raise SyntaxError(f"Expected {kind}, got {self.current()[0]}")

    def parse(self):
        nodes = [self.assignment()]
        while self.current()[0] == "SEMI":
            self.eat("SEMI")
            nodes.append(self.assignment())
        if self.current()[0] != "EOF":
            raise SyntaxError("Unexpected token after expression")
        return nodes

    def assignment(self):
        if self.current()[0] == "ID":
            name = self.current()[1]
            self.eat("ID")
            if self.current()[0] == "ASSIGN": # If the next token is a =
                self.eat("ASSIGN")
                value = self.conditional() # Changing
                return Assign(name, value)
            else:
                return Var(name)
        else:
            return self.conditional()

    def logic(self):
        node = self.expr() #check if it's a plus or minus type token first
        while self.current()[0] in ("EQ", "LT", "GT", "AND", "OR"):
            op = self.current()
            self.eat(op[0])
            node = BinOp(node, op, self.expr())
        return node

    def expr(self):
        node = self.term()
        while self.current()[0] in ("PLUS", "MINUS"):
            op = self.current()
            self.eat(op[0])
            node = BinOp(node, op, self.term())
        return node
    
    def conditional(self):
        if self.current()[0] == "IF":
            self.eat("IF")
            condition = self.logic()
            self.eat("THEN")
            then_branch = self.logic()
            self.eat("ELSE")
            else_branch = self.logic()
            return IfExpression(condition, then_branch, else_branch)
        elif self.current()[0] == "WHILE":
            self.eat("WHILE")
            condition = self.logic()
            self.eat("LBRACE")
            body = []
            while self.current()[0] != "RBRACE":
                body.append(self.assignment())
                if self.current()[0] == "SEMI":
                    self.eat("SEMI")
            self.eat("RBRACE")
            return WhileLoop(condition, body)
        else:
            return self.logic()   # Putting my call to self.logic here as opposed to in the actual assign method

    def term(self): #second lowest level
        node = self.factor()
        while self.current()[0] in ("STAR", "SLASH"):
            op = self.current()
            self.eat(op[0])
            node = BinOp(node, op, self.factor())
        return node

    def factor(self): #lower most of these methods. Handles numbers and parentheses, also if it's negative
        token = self.current()
        if token[0] == "NUM":
            self.eat("NUM")
            return Number(token[1])
        elif token[0] == "ID":
            self.eat("ID")
            return Var(token[1])
        elif token[0] == "MINUS":
            self.eat("MINUS")
            return UnaryOp(("MINUS", "-"), self.factor())
        elif token[0] == "NOT":
            self.eat("NOT")
            return UnaryOp(("NOT", "not"), self.factor())
        elif token[0] == "LPAREN":
            self.eat("LPAREN")
            node = self.logic()
            self.eat("RPAREN")
            return node
        else:
            raise SyntaxError(f"Unexpected token {token}")

def repl():
    interp = Interpreter()
    while True:
        try:
            line = input(">>> ")
            if line.strip() in ("exit", "quit"):    # Built in function to quit the program if they type that
                break
            tokens = lex(line) # breaks it into tokens
            parser = Parser(tokens) #parses the tokens
            tree = parser.parse()
            result = None
            if isinstance(tree, list):
                for node in tree:
                    result = interp.evaluate(node)
            else:
                result = interp.evaluate(tree)
            if result is not None:
                print(result)

        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    repl()