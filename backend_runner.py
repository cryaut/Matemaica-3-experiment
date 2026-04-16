import sys
import json
import traceback
from backend import render_expression

def main():
    try:
        input_data = sys.stdin.read()
        if not input_data:
            return
        req = json.loads(input_data)
        
        expression = req.get("expression", "")
        input_mode = req.get("input_mode", "LaTeX")
        variation_level = req.get("variation_level", "Medium")
        seed = req.get("seed", None)
        output_format = req.get("output_format", "SVG")
        page_style = req.get("page_style", "Blank")
        ink_color = req.get("ink_color", "#333333")
        
        result = render_expression(expression, input_mode, variation_level, seed, output_format, page_style, ink_color)
        
        # We don't read from files anymore, the backend returns the content directly
        print(json.dumps(result))
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"status": "error", "notes": [str(e)]}))

if __name__ == "__main__":
    main()
