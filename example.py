from handmath import render_expression
import os

# Ensure dummy symbols exist
if not os.path.exists("symbols"):
    print("Generating dummy symbols for testing...")
    import generate_dummy_symbols

tokens = ["x", "^2", "+", "2", "x", "+", "1", "=", "0"]

print(f"Rendering expression: {' '.join(tokens)}")
render_expression(
    tokens=tokens,
    symbols_dir="symbols",
    output_path="output.svg",
    seed=42,
    export_png=False # Set to True if cairosvg is installed
)
print("Done! Check output.svg")
