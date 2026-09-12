
import json
from latex_parser import parse_latex_math
from layout_engine import layout_ast

formulas = [
    r"\frac{1}{1-u} = \sum_{n=0}^{\infty} u^n",
    r"|u|<1"
]

for formula in formulas:
    print(f"Testing: {formula}")
    try:
        ast = parse_latex_math(formula)
        print(f"AST: {json.dumps(ast, indent=2)}")
        box = layout_ast(ast)
        print(f"Box dimensions: {box.width}x{box.height}")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)
