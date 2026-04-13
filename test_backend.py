from backend import render_expression
import json

res = render_expression(r"\dfrac{1}{2} \text{ (dividir por } n^{1/3} \text{ )}", "LaTeX", "Medium", 42, "SVG")
print(res["status"])
if res["status"] == "ok":
    print("SVG length:", len(res["svg_content"]))
    print("Contains dfrac?", "\\dfrac" in res["svg_content"])
    print("Contains text?", "dividir por" in res["svg_content"])
else:
    print(res["notes"])
