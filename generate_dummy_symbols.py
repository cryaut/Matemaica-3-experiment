import os

def create_svg(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Create a simple SVG that looks somewhat handwritten using a cursive font
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 50 50" width="50" height="50">
  <text x="25" y="35" font-family="cursive, sans-serif" font-style="italic" font-size="40" text-anchor="middle" fill="black">{text}</text>
</svg>"""
    with open(path, 'w') as f:
        f.write(svg_content)

symbols = {
    "x": ["x_1", "x_2"],
    "plus": ["plus_1", "plus_2"],
    "equals": ["equals_1"],
    "digits/0": ["0_1"],
    "digits/1": ["1_1"],
    "digits/2": ["2_1"],
    "n": ["n_1"]
}

text_map = {
    "x": "x",
    "plus": "+",
    "equals": "=",
    "digits/0": "0",
    "digits/1": "1",
    "digits/2": "2",
    "n": "n"
}

for folder, files in symbols.items():
    for file in files:
        create_svg(f"symbols/{folder}/{file}.svg", text_map[folder])
