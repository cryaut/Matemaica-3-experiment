from latex_parser import parse_latex_math
import json

try:
    ast = parse_latex_math(r"\lim_{n\to +\infty}")
    print(json.dumps(ast, indent=2))
except Exception as e:
    print("Error:", e)
