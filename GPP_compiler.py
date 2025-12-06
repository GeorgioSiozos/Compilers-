import sys

# --- Symbol Table Implementation ---
class Symbol:
    def __init__(self, name, kind, typ, scope_level, address):
        self.name = name
        self.kind = kind        
        self.type = typ         
        self.scope_level = scope_level
        self.address = address  

    def __repr__(self):
        return f"Symbol({self.name}, {self.kind}, {self.type}, scope={self.scope_level}, addr={self.address})"

class SymbolTable:
    def __init__(self):
        self.scopes = [{}]        
        self.next_address = [0]   

    def enter_scope(self):
        self.scopes.append({})
        self.next_address.append(0)

    def exit_scope(self):
        self.scopes.pop()
        self.next_address.pop()

    def declare(self, name, kind, typ='integer'):
        current = self.scopes[-1]
        if name in current:
            raise SyntaxError(f"Duplicate declaration: {name}")
        addr = self.next_address[-1]
        symbol = Symbol(name, kind, typ, len(self.scopes)-1, addr)
        current[name] = symbol
        self.next_address[-1] += 1
        return symbol

    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise SyntaxError(f"Undeclared identifier: {name}")

    def write_to_file(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== Πίνακας Συμβόλων ===\n")
            for level, scope in enumerate(self.scopes):
                f.write(f"Scope level {level}:\n")
                for sym in scope.values():
                    f.write(f" {sym}\n")




# Token class
class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

# Lexer class
class Lexer:
    KEYWORDS = {
        'πρόγραμμα', 'συνάρτηση', 'διαδικασία', 'δήλωση',
        'εάν', 'τότε', 'αλλιώς', 'εάν_τέλος', 'όσο', 'επανάλαβε',
        'όσο_τέλος', 'γράψε', 'διάβασε', 'εκτέλεσε', 'επιστροφή',
        'αρχή_προγράμματος', 'τέλος_προγράμματος',
        'είσοδος', 'έξοδος', 'είσοδος_εξοδος'
    }
    OPERATORS = {'+', '-', '*', '/', '=', '<', '>', '<=', '>=', '<>', ':='}
    DELIMITERS = {'(', ')', ',', ';', '{', '}'}

    def __init__(self, code):
        self.code = code

    def tokenize(self):
        tokens = []
        words = self.code.replace('(', ' ( ').replace(')', ' ) ').replace('{', ' { ').replace('}', ' } ')
        words = words.replace(';', ' ; ').replace(',', ' , ').replace('\n', ' ').split()
        for word in words:
            if word == ':=':
                tokens.append(Token('OPERATOR', ':='))
            elif word in self.KEYWORDS:
                tokens.append(Token('KEYWORD', word))
            elif word in self.OPERATORS:
                tokens.append(Token('OPERATOR', word))
            elif word in self.DELIMITERS:
                tokens.append(Token('DELIMITER', word))
            elif word.isdigit():
                tokens.append(Token('NUMBER', word))
            else:
                tokens.append(Token('IDENTIFIER', word))
        tokens.append(Token('EOF', ''))
        return tokens

# Intermediate Code class
class IntermediateCode:
    def __init__(self):
        self.instructions = []
        self.temp_counter = 0
        
        

    def new_temp(self):
        temp = f"T_{self.temp_counter}"
        self.temp_counter += 1
        return temp

    def emit(self, op, arg1='_', arg2='_', res='_'):
        self.instructions.append((op, arg1, arg2, res))

    def print_code(self):
        for idx, instr in enumerate(self.instructions, start=1):
            print(f"{idx}: {instr[0]} {instr[1]} {instr[2]} {instr[3]}")

    def write_to_file(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for idx, instr in enumerate(self.instructions, start=1):
                f.write(f"{idx}: {instr[0]} {instr[1]} {instr[2]} {instr[3]}\n")

#RISC-V Code Generator
class RiscVGenerator:
    def __init__(self, intermediate_code):
        self.code = intermediate_code.instructions
        self.output = []
        self.label_counter = 0
        self.s = []

    def new_label(self):
        label = f"L{self.label_counter}"
        self.label_counter += 1
        return label

    def generate(self):
        pending_labels = {}
        i = 0
        while i < len(self.code):
            op, a1, a2, res = self.code[i]

            if op == ':=':
                self.load(a1, 't0')
                self.emit(f"sw t0, {res}")

            elif op in ('+', '-', '*', '/'):
                self.load(a1, 't1')
                self.load(a2, 't2')
                inst = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}[op]
                self.emit(f"{inst} t3, t1, t2")
                self.emit(f"sw t3, {res}")

            elif op in ('<', '>', '<=', '>=', '=', '<>'):
                self.load(a1, 't1')
                self.load(a2, 't2')
                cmp_inst = {
                    '>':  f"ble t1, t2, SKIP_{res}",
                    '<':  f"bge t1, t2, SKIP_{res}",
                    '>=': f"blt t1, t2, SKIP_{res}",
                    '<=': f"bgt t1, t2, SKIP_{res}",
                    '=':  f"bne t1, t2, SKIP_{res}",
                    '<>': f"beq t1, t2, SKIP_{res}"
                }[op]
                self.emit(f"# if not ({a1} {op} {a2}) skip block")
                self.emit(cmp_inst)
                pending_labels[res] = f"SKIP_{res}"

            elif op == 'write':
                self.load(a1, 'a0')
                self.emit("li a7, 1")
                self.emit("ecall")

            elif op == 'begin_block' or op == 'end_block':
                self.emit(f"# {op} {a1}")

            if res in pending_labels:
                self.emit(f"{pending_labels[res]}:")
                del pending_labels[res]

            i += 1


    def load(self, value, reg):
        if value.isdigit():
            self.emit(f"li {reg}, {value}")
        else:
            self.emit(f"lw {reg}, {value}")

    def emit(self,line):
        self.label_counter += 1
        label = f"L{self.label_counter}"
        self.output.append(f"{label}:     {line}")

    def write_to_file(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            for line in self.output:
                f.write(line + '\n')

    

# Parser class
class Parser:
    def __init__(self, tokens, intermediate, symtab):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[self.pos]
        self.intermediate = intermediate
        self.symtab = symtab

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = Token('EOF', '')

    def expect(self, token_type, value=None):
        if self.current_token.type != token_type or (value and self.current_token.value != value):
            raise SyntaxError(f"Expected {token_type} '{value}' but got {self.current_token}")
        self.advance()

    def parse_program(self):
        self.symtab.enter_scope()
        self.expect('KEYWORD', 'πρόγραμμα')
        self.expect('IDENTIFIER')
        name = self.current_token.value
        self.expect('DELIMITER', '(')
        self.expect('DELIMITER', ')')
        self.expect('DELIMITER', '{')
        self.intermediate.emit('begin_block', 'main', '_', '_')
        self.parse_programblock()
        self.expect('DELIMITER', '}')
        self.intermediate.emit('end_block', 'main', '_', '_') 
        
        

    def parse_programblock(self):
        self.parse_declarations()
        self.parse_sequence()

    def parse_declarations(self):
        while self.current_token.value == 'δήλωση':
            self.advance()
            self.parse_varlist()
            self.expect('DELIMITER', ';')

    def parse_varlist(self):
        name = self.current_token.value
        self.symtab.declare(name, kind='var')
        self.expect('IDENTIFIER')
        while self.current_token.value == ',':
            self.advance()
            name = self.current_token.value
            self.symtab.declare(name, kind='var')
            self.expect('IDENTIFIER')

    def parse_sequence(self):
        while not (
            (self.current_token.type == 'DELIMITER' and self.current_token.value == '}')
            or (self.current_token.value in ('εάν_τέλος', 'όσο_τέλος', 'αλλιώς'))
                   ): 
                self.parse_statement()    
                if self.current_token.value == ';':
                    self.advance()

    def parse_statement(self):
        if self.current_token.type == 'IDENTIFIER':
            self.parse_assignment()
        elif self.current_token.value == 'εάν':
            self.parse_if()
        elif self.current_token.value == 'όσο':
            self.parse_while()
        elif self.current_token.value == 'γράψε':
            self.parse_print()
        elif self.current_token.value == 'διάβασε':
            self.parse_input()
        elif self.current_token.value in ['αρχή_προγράμματος', 'τέλος_προγράμματος']:
            self.advance()
        else:
            raise SyntaxError(f"Unrecognized statement: {self.current_token}")

    def parse_assignment(self):
        id_name = self.current_token.value
        self.advance()
        self.expect('OPERATOR', ':=')
        expr_result = self.parse_expression()
        self.intermediate.emit(':=', expr_result, '_', id_name)

    def parse_expression(self):
        left = self.parse_term()
        while self.current_token.value in ('+', '-'):
            op = self.current_token.value
            self.advance()
            right = self.parse_term()
            temp = self.intermediate.new_temp()
            self.intermediate.emit(op, left, right, temp)
            left = temp
        return left

    def parse_term(self):
        if self.current_token.type in ('NUMBER', 'IDENTIFIER'):
            val = self.current_token.value
            if self.current_token.type == 'IDENTIFIER':
                self.symtab.lookup(val)                            
            self.advance()
            return val
        elif self.current_token.value == '(' :
            self.advance()
            expr = self.parse_expression()
            self.expect('DELIMITER', ')')
            return expr
        else:
            raise SyntaxError("Expected expression")

    def parse_input(self):
        self.expect('KEYWORD', 'διάβασε')
        name = self.current_token.value
        self.symtab.lookup(name)
        self.expect('IDENTIFIER')
        
    def parse_print(self):
        self.expect('KEYWORD', 'γράψε')
        expr = self.parse_expression()
        self.intermediate.emit('write', expr, '_', '_') 

    def parse_if(self):
        self.expect('KEYWORD', 'εάν')
        self.parse_condition()
        self.expect('KEYWORD', 'τότε')
        self.parse_sequence()
        if self.current_token.value == 'αλλιώς':
            self.advance()
            self.parse_sequence()
        self.expect('KEYWORD', 'εάν_τέλος')

    def parse_while(self):
        self.expect('KEYWORD', 'όσο')
        self.parse_condition()
        self.expect('KEYWORD', 'επανάλαβε')
        self.parse_sequence()
        self.expect('KEYWORD', 'όσο_τέλος')

    def parse_condition(self):
        left = self.parse_expression()
        op = self.current_token.value
        if op not in ('>', '<', '>=', '<=', '=', '<>'):
            raise SyntaxError(f"Invalid comparison operator: {self.current_token}")
        self.advance()
        right = self.parse_expression()
        temp = self.intermediate.new_temp()
        self.intermediate.emit(op, left, right, temp)
        return temp

# Main
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python int2.py <source.gpp>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, 'r', encoding='utf-8') as f:
        code = f.read()

    lexer = Lexer(code)
    tokens = lexer.tokenize()
    intermediate = IntermediateCode()
    symtab = SymbolTable()
    parser = Parser(tokens, intermediate, symtab)
    parser.parse_program()

    print("\nΕνδιάμεσος Κώδικας:")
    intermediate.print_code()

    int_filename = filename.rsplit('.', 1)[0] + '.int'
    intermediate.write_to_file(int_filename)
    print(f"Ο ενδιάμεσος κώδικας aποθηκεύτηκε σε: {int_filename}")

    sym_filename = filename.rsplit('.', 1)[0] + '.sym'
    symtab.write_to_file(sym_filename)
    print(f"Ο πίνακας συμβόλων αποθηκεύτηκε σε: {sym_filename}")
    symtab.exit_scope()


    rv = RiscVGenerator(intermediate)
    rv.generate()
    asm_filename = filename.rsplit('.', 1)[0] + '.asm'
    rv.write_to_file(asm_filename)
    print(f"Ο κώδικας RISC-V αποθηκεύτηκε σε : {asm_filename}")
