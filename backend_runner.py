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
        
        result = render_expression(expression, input_mode, variation_level, seed, output_format)
        
        # We need to return the actual SVG content to the Node server
        if result.get("output_files", {}).get("svg"):
            with open(result["output_files"]["svg"], "r", encoding="utf-8") as f:
                result["svg_content"] = f.read()
                
        print(json.dumps(result))
    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"status": "error", "notes": [str(e)]}))

if __name__ == "__main__":
    main()
