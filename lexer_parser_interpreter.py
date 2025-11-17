# -*- coding: utf-8 -*-

# Exceptions
class LexicalError(Exception):
    pass


class SyntaxError(Exception):
    pass


class ParsingError(Exception):
    pass


# Tokens
class TokenType:
    INTEGER = "INTEGER"
    PLUS = "PLUS"
    MINUS = "MINUS"
    MUL = "MUL"        # множення
    DIV = "DIV"        # ділення
    LPAREN = "LPAREN"  # (
    RPAREN = "RPAREN"  # )
    EOF = "EOF"        # кінець вхідного рядка


class Token:
    def __init__(self, type, value):
        self.type = type
        self.value = value

    def __str__(self):
        return f"Token({self.type}, {repr(self.value)})"


# Lexer
class Lexer:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        # Порожній рядок: захист від IndexError
        self.current_char = self.text[self.pos] if self.text else None

    def advance(self):
        # Переміщуємо 'вказівник' на наступний символ вхідного рядка
        self.pos += 1
        if self.pos > len(self.text) - 1:
            self.current_char = None  # Означає кінець введення
        else:
            self.current_char = self.text[self.pos]

    def skip_whitespace(self):
        # Пропускаємо пробільні символи
        while self.current_char is not None and self.current_char.isspace():
            self.advance()

    def integer(self):
        # Повертаємо ціле число, зібране з послідовності цифр
        result = ""
        while self.current_char is not None and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        # Лексичний аналізатор, що розбиває вхідний рядок на токени
        while self.current_char is not None:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(TokenType.INTEGER, self.integer())

            if self.current_char == "+":
                self.advance()
                return Token(TokenType.PLUS, "+")

            if self.current_char == "-":
                self.advance()
                return Token(TokenType.MINUS, "-")

            if self.current_char == "*":
                self.advance()
                return Token(TokenType.MUL, "*")

            if self.current_char == "/":
                self.advance()
                return Token(TokenType.DIV, "/")

            if self.current_char == "(":
                self.advance()
                return Token(TokenType.LPAREN, "(")

            if self.current_char == ")":
                self.advance()
                return Token(TokenType.RPAREN, ")")

            raise LexicalError("Помилка лексичного аналізу")

        return Token(TokenType.EOF, None)



# AST
class AST:
    pass


class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right


class Num(AST):
    def __init__(self, token):
        self.token = token
        self.value = token.value


# Parser
class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def error(self):
        raise ParsingError("Помилка синтаксичного аналізу")

    def eat(self, token_type):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            self.error()

    # Граматика:
    # expr   : term ((PLUS | MINUS) term)*
    # term   : factor ((MUL | DIV) factor)*
    # factor : INTEGER | LPAREN expr RPAREN

    def factor(self):
        # Обробка чисел та виразів у дужках
        token = self.current_token
        if token.type == TokenType.INTEGER:
            self.eat(TokenType.INTEGER)
            return Num(token)
        elif token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        else:
            self.error()

    def term(self):
        # Обробка множення та ділення
        node = self.factor()
        while self.current_token.type in (TokenType.MUL, TokenType.DIV):
            token = self.current_token
            if token.type == TokenType.MUL:
                self.eat(TokenType.MUL)
            elif token.type == TokenType.DIV:
                self.eat(TokenType.DIV)
            node = BinOp(left=node, op=token, right=self.factor())
        return node

    def expr(self):
        # Обробка додавання та віднімання (найнижчий пріоритет)
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            elif token.type == TokenType.MINUS:
                self.eat(TokenType.MINUS)
            node = BinOp(left=node, op=token, right=self.term())
        return node


# AST printer
def print_ast(node, level=0):
    indent = "  " * level
    if isinstance(node, Num):
        print(f"{indent}Num({node.value})")
    elif isinstance(node, BinOp):
        print(f"{indent}BinOp:")
        print(f"{indent}  left: ")
        print_ast(node.left, level + 2)
        print(f"{indent}  op: {node.op.type}")
        print(f"{indent}  right: ")
        print_ast(node.right, level + 2)
    else:
        print(f"{indent}Unknown node type: {type(node)}")


# Interpreter
class Interpreter:
    def __init__(self, parser):
        self.parser = parser

    def visit_BinOp(self, node):
        if node.op.type == TokenType.PLUS:
            return self.visit(node.left) + self.visit(node.right)
        elif node.op.type == TokenType.MINUS:
            return self.visit(node.left) - self.visit(node.right)
        elif node.op.type == TokenType.MUL:
            return self.visit(node.left) * self.visit(node.right)
        elif node.op.type == TokenType.DIV:
            # Виконуємо ділення з перевіркою на нуль
            right_val = self.visit(node.right)
            if right_val == 0:
                raise Exception("Ділення на нуль!")
            return self.visit(node.left) / right_val

    def visit_Num(self, node):
        return node.value

    def interpret(self):
        tree = self.parser.expr()
        return self.visit(tree)

    def visit(self, node):
        method_name = "visit_" + type(node).__name__
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Немає методу visit_{type(node).__name__}")


# Three original "main" behaviors as modes
def run_lexer_mode():
    while True:
        try:
            text = input('Введіть вираз (або "exit" для виходу): ')
            if text.lower() == "exit":
                print("Вихід із програми.")
                break
            lexer = Lexer(text)
            token = lexer.get_next_token()
            while token.type != TokenType.EOF:
                print(token)
                token = lexer.get_next_token()
        except Exception as e:
            print(e)


def run_parser_mode():
    while True:
        try:
            text = input('Введіть вираз (або "exit" для виходу): ')
            if text.lower() == "exit":
                print("Вихід із програми.")
                break
            lexer = Lexer(text)
            parser = Parser(lexer)
            tree = parser.expr()
            print_ast(tree)
        except Exception as e:
            print(e)


def run_interpreter_mode():
    while True:
        try:
            text = input('Введіть вираз (або "exit" для виходу): ')
            if text.lower() == "exit":
                print("Вихід із програми.")
                break
            lexer = Lexer(text)
            parser = Parser(lexer)
            interpreter = Interpreter(parser)
            result = interpreter.interpret()
            print(result)
        except Exception as e:
            print(e)


def main():
    print("Оберіть режим роботи:")
    print("  1 - Лексер (аналог початкового 01_lexer.py)")
    print("  2 - Парсер (аналог початкового 02_parser.py)")
    print("  3 - Інтерпретатор (аналог початкового 03_interpreter.py)")
    while True:
        mode = input("Введіть 1/2/3 (або 'exit' для виходу): ").strip().lower()
        if mode == "exit":
            print("Вихід із програми.")
            return
        if mode in ("1", "2", "3"):
            break
        print("Невідомий режим. Спробуйте ще раз.")

    if mode == "1":
        run_lexer_mode()
    elif mode == "2":
        run_parser_mode()
    else:
        run_interpreter_mode()


if __name__ == "__main__":
    main()
