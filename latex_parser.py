import re
import json
from dataclasses import dataclass
from typing import List, Optional, Any, Dict, Set, Callable, Tuple

@dataclass
class Token:
    type: str
    value: str

class ParseError(Exception):
    pass

# Token specifications
TOKEN_SPEC = [
    ('TEXT_MODE', r'\\(?:text|textbf|textit|mathrm|intertext)\s*\{.*?\}|\\(?:text|textbf|textit|mathrm|intertext)\s*\(.*?\)'),
    ('COMMAND', r'\\[a-zA-Z]+|\\[,;:\!|.{}|*]'),
    ('NEWLINE', r'\\\\'),
    ('AMPERSAND', r'&'),
    ('NUMBER', r'\d+(\.\d+)?'),
    ('VARIABLE', r'[a-zA-Z]'),
    ('OPERATOR', r'[+\-=<>/!]'),
    ('LBRACE', r'\{'),
    ('RBRACE', r'\}'),
    ('LPAREN', r'\('),
    ('RPAREN', r'\)'),
    ('LBRACKET', r'\['),
    ('RBRACKET', r'\]'),
    ('CARET', r'\^'),
    ('UNDERSCORE', r'_'),
    ('COMMA', r','),
    ('COMMENT', r'%.*'),
    ('WS', r'\s+'),
    ('MISC', r'.'),
]

def tokenize(code: str) -> List[Token]:
    """Converts a LaTeX math string into a list of semantic tokens."""
    tokens = []
    i = 0
    while i < len(code):
        # Skip whitespace
        if code[i].isspace():
            i += 1
            continue
        # Skip comments
        if code[i] == '%':
            while i < len(code) and code[i] != '\n':
                i += 1
            continue
            
        # Check for \text{...} or \text(...)
        m = re.match(r'\\(?:text|textbf|textit|mathrm|intertext)\s*([{(])', code[i:])
        if m:
            start_char = m.group(1)
            end_char = '}' if start_char == '{' else ')'
            start_idx = i + m.end()
            brace_count = 1
            j = start_idx
            while j < len(code):
                if code[j] == '\\':
                    j += 2
                    continue
                if code[j] == start_char:
                    brace_count += 1
                elif code[j] == end_char:
                    brace_count -= 1
                    if brace_count == 0:
                        break
                j += 1
            content = code[start_idx:j]
            tokens.append(Token('TEXT_MODE', content))
            i = j + 1 if j < len(code) else len(code)
            continue
            
        # Match other tokens
        matched = False
        for kind, pattern in TOKEN_SPEC:
            if kind == 'TEXT_MODE': continue
            m = re.match(pattern, code[i:])
            if m:
                value = m.group(0)
                if kind not in ('WS', 'COMMENT'):
                    tokens.append(Token(kind, value))
                i += len(value)
                matched = True
                break
        if not matched:
            i += 1
            
    tokens.append(Token('EOF', ''))
    return tokens

class LatexMathParser:
    """
    A recursive descent parser for LaTeX math expressions.
    Converts a token stream into a structured Abstract Syntax Tree (AST).
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.stop_conditions: List[Callable[[], bool]] = []

    def push_stop_condition(self, condition: Optional[Callable[[], bool]]):
        if condition:
            self.stop_conditions.append(condition)

    def pop_stop_condition(self, condition: Optional[Callable[[], bool]]):
        if condition and self.stop_conditions:
            self.stop_conditions.pop()

    def _should_stop(self) -> bool:
        for cond in self.stop_conditions:
            if cond():
                return True
        return False

    def current(self) -> Token:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token('EOF', '')

    def peek(self, offset: int = 1) -> Token:
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return Token('EOF', '')

    def consume(self, expected_type: Optional[str] = None) -> Token:
        tok = self.current()
        if expected_type and tok.type != expected_type:
            raise ParseError(f"Expected {expected_type}, got {tok.type} '{tok.value}' at position {self.pos}")
        self.pos += 1
        return tok

    def parse(self) -> Dict[str, Any]:
        """Main entry point. Parses the entire token stream."""
        ast = self.parse_expression()
        if self.current().type != 'EOF':
            raise ParseError(f"Unexpected token {self.current().value} at end of input. Tokens: {[t.value for t in self.tokens]}")
        return ast if ast else {"type": "sequence", "items": []}

    def parse_expression(self, break_on: Optional[Set[str]] = None, stop_condition: Optional[Callable[[], bool]] = None) -> Optional[Dict[str, Any]]:
        """Parses a sequence of terms separated by binary operators (+, -, =, <, >)."""
        if break_on is None:
            break_on = set()
            
        self.push_stop_condition(stop_condition)
        try:
            nodes = []
            while self.current().type != 'EOF' and self.current().type not in break_on:
                if stop_condition and stop_condition():
                    break
                if self._should_stop():
                    break
                    
                term = self.parse_term(break_on, stop_condition)
                if term:
                    nodes.append(term)
                
                if self.current().type == 'OPERATOR' and self.current().value in ('+', '-', '=', '<', '>'):
                    op = self.consume()
                    nodes.append({"type": "operator", "value": op.value})
                elif self.current().type == 'EOF' or self.current().type in break_on:
                    break
                elif stop_condition and stop_condition():
                    break
                elif self._should_stop():
                    break
                else:
                    # If we have something else (like a symbol or variable), 
                    # it will be handled by the next iteration's parse_term
                    if self.current().type not in ('EOF', 'RBRACE', 'RPAREN', 'RBRACKET') and self.current().type not in break_on:
                        continue
                    else:
                        break
                    
            if len(nodes) == 1:
                return nodes[0]
            elif len(nodes) == 0:
                return None
            return {"type": "sequence", "items": nodes}
        finally:
            self.pop_stop_condition(stop_condition)

    def parse_term(self, break_on: Set[str], stop_condition: Optional[Callable[[], bool]]) -> Optional[Dict[str, Any]]:
        """Parses a sequence of items (implicit multiplication, fractions, etc.) until an operator or boundary."""
        nodes = []
        while self.current().type not in ('EOF', 'RBRACE', 'RPAREN', 'RBRACKET') and self.current().type not in break_on:
            if stop_condition and stop_condition():
                break
            if self._should_stop():
                break
            if self.current().type == 'OPERATOR' and self.current().value in ('+', '-', '=', '<', '>'):
                break
            item = self.parse_item(break_on, stop_condition)
            if item:
                nodes.append(item)
                
        if len(nodes) == 1:
            return nodes[0]
        elif len(nodes) == 0:
            return None
        return {"type": "sequence", "items": nodes}

    def parse_item(self, break_on: Optional[Set[str]] = None, stop_condition: Optional[Callable[[], bool]] = None) -> Optional[Dict[str, Any]]:
        """Parses a single mathematical item (atom, command, group) and its postfix scripts."""
        if break_on is None: break_on = set()
        tok = self.current()
        if tok.type == 'EOF':
            return None
            
        node = None
        if tok.type == 'TEXT_MODE':
            self.consume()
            # We wrap it in a text_mode node, with the raw text
            if tok.value.startswith('\\intertext'):
                node = {"type": "intertext", "text": tok.value}
            else:
                node = {"type": "text_mode", "text": tok.value}
        elif tok.type == 'COMMAND':
            if tok.value in ('\\frac', '\\dfrac', '\\tfrac'):
                node = self.parse_fraction(break_on, stop_condition)
            elif tok.value == '\\sqrt':
                node = self.parse_sqrt()
            elif tok.value in ('\\int', '\\iint', '\\iiint', '\\oint', '\\oiint'):
                node = self.parse_integral(tok.value, break_on, stop_condition)
            elif tok.value in ('\\sum', '\\prod', '\\coprod', '\\bigcup', '\\bigcap'):
                node = self.parse_sum(tok.value, break_on, stop_condition)
            elif tok.value == '\\begin':
                node = self.parse_environment()
            elif tok.value == '\\lim':
                node = self.parse_limit(break_on, stop_condition)
            elif tok.value in ('\\text', '\\textbf', '\\textit', '\\mathrm'):
                self.consume()
                arg = self.parse_required_argument()
                # We can just treat it as a group but maybe with a text style
                node = {"type": "text_mode", "content": arg}
            elif tok.value in ('\\vec', '\\mathbf', '\\hat', '\\dot', '\\ddot', '\\mathbb', '\\mathcal'):
                self.consume()
                arg = self.parse_required_argument()
                node = {"type": "accent", "name": tok.value, "body": arg}
            elif tok.value == '\\binom':
                self.consume()
                arg1 = self.parse_required_argument()
                arg2 = self.parse_required_argument()
                node = {"type": "binom", "upper": arg1, "lower": arg2}
            elif tok.value == '\\vspace':
                self.consume()
                if self.current().type == 'COMMAND' and self.current().value == '\\*':
                    self.consume()
                arg = self.parse_required_argument()
                node = {"type": "vspace", "amount": arg}
            elif tok.value == '\\boxed':
                self.consume()
                arg = self.parse_required_argument()
                node = {"type": "boxed", "content": arg}
            elif tok.value == '\\left':
                node = self.parse_left_right()
            elif tok.value == '\\right':
                self.consume()
                if self.current().value == '.':
                    self.consume()
                return None
            elif tok.value in ('\\big', '\\Big', '\\bigg', '\\Bigg', '\\bigl', '\\Bigl', '\\biggl', '\\Biggl', '\\bigr', '\\Bigr', '\\biggr', '\\Biggr'):
                self.consume()
                node = self.parse_item(break_on, stop_condition)
                if node:
                    node["scale_modifier"] = tok.value
            elif tok.value in ('\\partial', '\\nabla', '\\infty', '\\to', '\\sin', '\\cos', '\\log', '\\ln', '\\div', '\\times', '\\Delta', '\\cdot', '\\approx', '\\sim', '\\propto', '\\ast', '\\star', '\\delta', '\\diracdelta', '\\imath', '\\jmath', '\\quad', '\\qquad', '\\,', '\\;', '\\:', '\\!', '\\|', '\\ge', '\\le', '\\geq', '\\leq', '\\Rightarrow', '\\Leftarrow', '\\Leftrightarrow', '\\rightarrow', '\\leftarrow', '\\leftrightarrow', '\\neq', '\\{', '\\}', '\\langle', '\\rangle', '\\mid', '\\implies', '\\dots', '\\cdots', '\\ddots', '\\vdots'):
                self.consume()
                node = {"type": "symbol", "value": tok.value}
            elif tok.value in ('\\limits', '\\nolimits'):
                self.consume()
                return self.parse_item()
            elif tok.value == '\\end':
                self.consume()
                # Ignore \end and its argument if encountered outside an environment
                if self.current().type == 'LBRACE':
                    self.consume('LBRACE')
                    while self.current().type != 'RBRACE' and self.current().type != 'EOF':
                        self.consume()
                    if self.current().type == 'RBRACE':
                        self.consume('RBRACE')
                else:
                    # Heuristic to consume unbraced environment names like 'align*'
                    while self.current().type in ('VARIABLE', 'MISC') and (self.current().value.isalpha() or self.current().value == '*'):
                        self.consume()
                return None
            else:
                self.consume()
                node = {"type": "command", "name": tok.value}
        elif tok.type == 'NEWLINE':
            self.consume()
            node = {"type": "symbol", "value": "\\\\"}
        elif tok.type == 'LBRACE':
            node = self.parse_group()
        elif tok.type == 'LPAREN':
            node = self.parse_parenthesized()
        elif tok.type == 'LBRACKET':
            node = self.parse_bracketed()
        elif tok.type == 'NUMBER':
            self.consume()
            node = {"type": "number", "value": tok.value}
        elif tok.type == 'VARIABLE':
            self.consume()
            node = {"type": "variable", "name": tok.value}
        elif tok.type == 'OPERATOR':
            self.consume()
            node = {"type": "operator", "value": tok.value}
        else:
            self.consume()
            node = {"type": "symbol", "value": tok.value}
            
        if node:
            node = self.parse_postfix_scripts(node)
        return node

    def parse_postfix_scripts(self, base_node: Dict[str, Any]) -> Dict[str, Any]:
        """Parses superscripts (^) and subscripts (_) attached to a base node."""
        node = base_node
        while self.current().type in ('CARET', 'UNDERSCORE'):
            tok = self.consume()
            arg = self.parse_required_argument()
            if tok.type == 'CARET':
                node = {"type": "power", "base": node, "exponent": arg}
            else:
                node = {"type": "subscript", "base": node, "subscript": arg}
        return node

    def parse_required_argument(self) -> Optional[Dict[str, Any]]:
        """Parses a required argument, which can be a brace-enclosed group or a single item."""
        if self.current().type == 'LBRACE':
            return self.parse_group()
        else:
            return self.parse_item()

    def _with_isolated_stops(self, func, *args, **kwargs):
        old_stops = self.stop_conditions
        self.stop_conditions = []
        try:
            return func(*args, **kwargs)
        finally:
            self.stop_conditions = old_stops

    def parse_group(self) -> Optional[Dict[str, Any]]:
        """Parses a brace-enclosed group { ... }"""
        self.consume('LBRACE')
        node = self._with_isolated_stops(self.parse_expression, break_on={'RBRACE'})
        if self.current().type == 'RBRACE':
            self.consume('RBRACE')
        return node

    def parse_parenthesized(self) -> Dict[str, Any]:
        """Parses a parenthesis-enclosed group ( ... )"""
        self.consume('LPAREN')
        node = self._with_isolated_stops(self.parse_expression, break_on={'RPAREN'})
        if self.current().type == 'RPAREN':
            self.consume('RPAREN')
        return {"type": "group", "content": node, "style": "parentheses"}

    def parse_bracketed(self) -> Dict[str, Any]:
        """Parses a bracket-enclosed group [ ... ]"""
        self.consume('LBRACKET')
        node = self._with_isolated_stops(self.parse_expression, break_on={'RBRACKET'})
        if self.current().type == 'RBRACKET':
            self.consume('RBRACKET')
        return {"type": "group", "content": node, "style": "brackets"}

    def parse_left_right(self) -> Dict[str, Any]:
        """Parses a \left ... \right group."""
        self.consume('COMMAND') # \left
        left_delim = self.consume()
        
        node = self._with_isolated_stops(
            self.parse_expression, 
            stop_condition=lambda: self.current().type == 'COMMAND' and self.current().value == '\\right'
        )
        
        if self.current().type == 'COMMAND' and self.current().value == '\\right':
            self.consume('COMMAND') # \right
            right_delim = self.consume()
        else:
            right_delim = Token('MISC', '.') # Fallback if unmatched
            
        return {
            "type": "group",
            "style": "left_right",
            "left_delim": left_delim.value,
            "right_delim": right_delim.value,
            "content": node
        }

    def parse_fraction(self, break_on: Optional[Set[str]] = None, stop_condition: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """Parses a \\frac{num}{den} command and detects derivatives."""
        if break_on is None: break_on = set()
        self.consume('COMMAND') # \frac
        numerator = self.parse_required_argument()
        denominator = self.parse_required_argument()
        
        # Semantic check for derivative
        is_deriv, var, func, is_partial = self._check_derivative(numerator, denominator)
        if is_deriv:
            if func:
                body = None
            else:
                body = self.parse_term(break_on=break_on, stop_condition=stop_condition)
            return {
                "type": "partial_derivative" if is_partial else "derivative",
                "variable": var,
                "function": func,
                "body": body
            }
            
        return {
            "type": "fraction",
            "numerator": numerator,
            "denominator": denominator
        }

    def _check_derivative(self, num: Optional[Dict[str, Any]], den: Optional[Dict[str, Any]]) -> Tuple[bool, Any, Any, bool]:
        """Helper to detect if a fraction represents a derivative."""
        def is_d(node):
            if not node: return False, False
            if node.get("type") == "variable" and node.get("name") == "d": return True, False
            if node.get("type") == "symbol" and node.get("value") == "\\partial": return True, True
            return False, False

        den_is_d = False
        is_partial = False
        var = None
        
        if den and den.get("type") == "sequence":
            items = den.get("items", [])
            if len(items) == 2:
                den_is_d, is_partial = is_d(items[0])
                if den_is_d:
                    var = items[1]
                    
        if not den_is_d:
            return False, None, None, False
            
        num_is_d = False
        func = None
        
        if num:
            if num.get("type") in ("variable", "symbol"):
                num_is_d, num_partial = is_d(num)
                if num_is_d and num_partial == is_partial:
                    func = None
            elif num.get("type") == "sequence":
                items = num.get("items", [])
                if len(items) >= 2:
                    num_is_d, num_partial = is_d(items[0])
                    if num_is_d and num_partial == is_partial:
                        if len(items) == 2:
                            func = items[1]
                        else:
                            func = {"type": "sequence", "items": items[1:]}
                            
        if num_is_d:
            return True, var, func, is_partial
            
        return False, None, None, False

    def parse_sqrt(self) -> Dict[str, Any]:
        """Parses a \\sqrt[index]{radicand} command."""
        self.consume('COMMAND')
        index = None
        if self.current().type == 'LBRACKET':
            self.consume()
            index_items = []
            while self.current().type not in ('EOF', 'RBRACKET'):
                index_items.append(self.parse_item())
            self.consume('RBRACKET')
            index = index_items[0] if len(index_items) == 1 else {"type": "sequence", "items": index_items}
            
        radicand = self.parse_required_argument()
        node = {"type": "sqrt", "radicand": radicand}
        if index:
            node["index"] = index
        return node

    def is_differential_next(self) -> bool:
        """Lookahead to detect 'dx' or '\\partial x' at the end of an integral."""
        tok = self.current()
        if (tok.type == 'VARIABLE' and tok.value == 'd') or (tok.type == 'COMMAND' and tok.value == '\\partial'):
            nxt = self.peek()
            if nxt.type == 'VARIABLE' or nxt.type == 'COMMAND':
                return True
        return False

    def parse_differential(self) -> Dict[str, Any]:
        """Parses the 'dx' part of an integral."""
        tok = self.consume()
        nxt = self.consume()
        var_node = {"type": "variable", "name": nxt.value} if nxt.type == 'VARIABLE' else {"type": "symbol", "value": nxt.value}
        return {
            "type": "differential",
            "operator": tok.value,
            "variable": var_node
        }

    def parse_integral(self, command: str, break_on: Optional[Set[str]] = None, stop_condition: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """Parses an \\int, \\iint, \\iiint, or \\oint command, including bounds, integrand, and differential."""
        if break_on is None: break_on = set()
        self.consume('COMMAND')
        lower_bound = upper_bound = None
        limits = False
        while self.current().type in ('CARET', 'UNDERSCORE') or (self.current().type == 'COMMAND' and self.current().value in ('\\limits', '\\nolimits')):
            if self.current().type == 'COMMAND':
                if self.current().value == '\\limits':
                    limits = True
                self.consume()
                continue
            tok = self.consume()
            arg = self.parse_required_argument()
            if tok.type == 'CARET': upper_bound = arg
            else: lower_bound = arg
            
        integrand = self.parse_expression(stop_condition=self.is_differential_next, break_on=break_on)
        differential = None
        if self.is_differential_next():
            differential = self.parse_differential()
            
        return {
            "type": "integral",
            "variant": command,
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "integrand": integrand,
            "differential": differential,
            "limits": limits
        }

    def parse_sum(self, command: str, break_on: Optional[Set[str]] = None, stop_condition: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """Parses a \\sum or \\prod command, extracting the index variable and bounds."""
        if break_on is None: break_on = set()
        self.consume('COMMAND')
        lower_bound = upper_bound = None
        limits = True # Sums usually have limits by default in display mode
        while self.current().type in ('CARET', 'UNDERSCORE') or (self.current().type == 'COMMAND' and self.current().value in ('\\limits', '\\nolimits')):
            if self.current().type == 'COMMAND':
                if self.current().value == '\\nolimits':
                    limits = False
                self.consume()
                continue
            tok = self.consume()
            arg = self.parse_required_argument()
            if tok.type == 'CARET': upper_bound = arg
            else: lower_bound = arg
            
        body = self.parse_term(break_on=break_on, stop_condition=stop_condition)
        
        index_var = None
        lower_val = lower_bound
        if lower_bound and lower_bound.get("type") == "sequence":
            items = lower_bound.get("items", [])
            if len(items) == 3 and items[0].get("type") == "variable" and items[1].get("value") == "=":
                index_var = items[0]
                lower_val = items[2]
                
        return {
            "type": "summation" if command in ("\\sum", "\\bigcup") else "product",
            "variant": command,
            "index": index_var,
            "lower_bound": lower_val,
            "upper_bound": upper_bound,
            "body": body,
            "limits": limits
        }

    def _make_sequence(self, items: List[Any]) -> Any:
        if not items: return None
        if len(items) == 1: return items[0]
        return {"type": "sequence", "items": items}

    def parse_environment(self) -> Dict[str, Any]:
        """Parses \\begin{env} ... \\end{env} including matrix and align structures."""
        self.consume('COMMAND') # \begin
        self.consume('LBRACE')
        env_name = ""
        while self.current().type != 'RBRACE' and self.current().type != 'EOF':
            env_name += self.consume().value
        if self.current().type == 'RBRACE':
            self.consume('RBRACE')
        
        rows = []
        current_row = []
        current_cell = []
        
        old_stops = self.stop_conditions
        self.stop_conditions = []
        try:
            while self.current().type != 'EOF':
                tok = self.current()
                if tok.type == 'COMMAND' and tok.value == '\\end':
                    self.consume()
                    if self.current().type == 'LBRACE':
                        self.consume('LBRACE')
                        end_name = ""
                        while self.current().type != 'RBRACE' and self.current().type != 'EOF':
                            end_name += self.consume().value
                        if self.current().type == 'RBRACE':
                            self.consume('RBRACE')
                    break
                    
                if tok.type == 'AMPERSAND':
                    self.consume()
                    current_row.append(self._make_sequence(current_cell))
                    current_cell = []
                elif tok.type == 'NEWLINE':
                    self.consume()
                    # Consume optional argument like \\[4pt]
                    if self.current().type == 'MISC' and self.current().value == '[':
                        self.consume() # [
                        while self.current().type != 'EOF' and not (self.current().type == 'MISC' and self.current().value == ']'):
                            self.consume()
                        if self.current().type == 'MISC' and self.current().value == ']':
                            self.consume() # ]
                    current_row.append(self._make_sequence(current_cell))
                    rows.append(current_row)
                    current_row = []
                    current_cell = []
                else:
                    start_pos = self.pos
                    item = self.parse_expression(
                        break_on={'AMPERSAND', 'NEWLINE'},
                        stop_condition=lambda: self.current().type == 'COMMAND' and self.current().value == '\\end'
                    )
                    if item:
                        current_cell.append(item)
                    if self.pos == start_pos:
                        # parse_expression didn't consume anything (e.g., unmatched RBRACE)
                        # Consume to avoid infinite loop
                        tok = self.consume()
                        current_cell.append({"type": "symbol", "value": tok.value})
                        
            if current_cell or current_row:
                current_row.append(self._make_sequence(current_cell))
                rows.append(current_row)
        finally:
            self.stop_conditions = old_stops
            
        return {
            "type": "environment",
            "name": env_name,
            "rows": rows
        }

    def parse_limit(self, break_on: Optional[Set[str]] = None, stop_condition: Optional[Callable[[], bool]] = None) -> Dict[str, Any]:
        """Parses a \\lim command, extracting the variable and target."""
        if break_on is None: break_on = set()
        self.consume('COMMAND')
        
        condition = None
        if self.current().type == 'UNDERSCORE':
            self.consume()
            condition = self.parse_required_argument()
            
        var = None
        target = None
        if condition:
            def flatten(node):
                if not node: return []
                if node.get("type") == "sequence":
                    res = []
                    for item in node.get("items", []):
                        res.extend(flatten(item))
                    return res
                return [node]
                
            items = flatten(condition)
            to_idx = -1
            for i, item in enumerate(items):
                if item.get("type") == "symbol" and item.get("value") == "\\to":
                    to_idx = i
                    break
            if to_idx != -1:
                var = items[0] if to_idx == 1 else {"type": "sequence", "items": items[:to_idx]}
                target = items[to_idx+1] if to_idx == len(items)-2 else {"type": "sequence", "items": items[to_idx+1:]}
            else:
                var = condition
                
        body = self.parse_term(break_on=break_on, stop_condition=stop_condition)
        
        return {
            "type": "limit",
            "variable": var,
            "target": target,
            "body": body
        }

def parse_latex_math(expression: str) -> Dict[str, Any]:
    """Helper function to tokenize and parse a LaTeX math string."""
    tokens = tokenize(expression)
    parser = LatexMathParser(tokens)
    return parser.parse()

if __name__ == "__main__":
    test_expressions = [
        r"\frac{1}{x^2}",
        r"\int_0^1 x^2 dx",
        r"\sum_{n=1}^{\infty} \frac{1}{n^2}",
        r"\lim_{x \to 0} \frac{\sin x}{x}",
        r"\frac{d}{dx}(x^2+1)",
        r"\sqrt{x_n^2 + 1}"
    ]

    for expr in test_expressions:
        print(f"\n--- Parsing: {expr} ---")
        try:
            ast = parse_latex_math(expr)
            print(json.dumps(ast, indent=2))
        except ParseError as e:
            print(f"Parse Error: {e}")
