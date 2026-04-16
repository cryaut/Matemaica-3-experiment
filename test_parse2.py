from latex_parser import tokenize, LatexMathParser
import json

tokens = tokenize(r"{n\to +\infty}")
parser = LatexMathParser(tokens)
ast = parser.parse_required_argument()
print(json.dumps(ast, indent=2))
