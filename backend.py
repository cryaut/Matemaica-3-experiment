import time
import os
import json
from latex_parser import parse_latex_math, ParseError
from document_parser import parse_document
from layout_engine import layout_document, layout_ast

def render_expression(expression: str, input_mode: str, variation_level: str, seed: int | None, output_format: str) -> dict:
    """
    Backend stub for the Handwritten Math Rendering System.
    Parses LaTeX into AST and uses the 2D layout engine to generate SVG.
    """
    
    # 1. Basic Validation & Error Handling
    if not expression.strip():
        return {
            "status": "error",
            "parsed_files": [],
            "entry_file": "",
            "document_structure": {},
            "unsupported_items": [],
            "render_plan": {},
            "output_files": {"svg": "", "pdf": "", "png": ""},
            "notes": ["Empty input. Please enter a mathematical expression."]
        }
        
    # 2. Parse AST
    try:
        if input_mode == 'LaTeX':
            # Heuristic to decide between document and pure math
            # Triggers for document mode:
            # 1. Explicit LaTeX document markers
            # 2. Multiple spaces (likely a sentence)
            # 3. No common math operators at the start
            is_doc = any(marker in expression for marker in [
                '\\[', '\\(', '\\textbf', '\\section', '\\subsection', 
                '\\begin', '\\itemize', '\\enumerate', '$$', '\\item',
                '\\text{', '\\mathrm{', '\\textit{'
            ])
            
            if not is_doc:
                # If it has multiple spaces and doesn't look like a simple math expression, treat as doc
                # Math expressions usually have operators and few spaces
                space_count = expression.count(' ')
                if space_count > 2:
                    # Check for words (3+ letters)
                    words = [w for w in expression.split() if len(w) > 2 and w.isalpha()]
                    if len(words) >= 2:
                        is_doc = True
            
            if is_doc:
                doc_ast = parse_document(expression)
                layout = layout_document(doc_ast, max_width=800, scale=1.0)
                is_document_mode = True
            else:
                # Pure math expression
                ast = parse_latex_math(expression)
                layout = layout_ast(ast, scale=1.0)
                is_document_mode = False
        else:
            ast = parse_latex_math(expression)
            layout = layout_ast(ast, scale=1.0)
            is_document_mode = False
            
        if not layout:
            raise Exception("Layout engine failed to produce a result.")
            
    except Exception as e:
        return {
            "status": "error",
            "parsed_files": [],
            "entry_file": "",
            "document_structure": {},
            "unsupported_items": [],
            "render_plan": {},
            "output_files": {"svg": "", "pdf": "", "png": ""},
            "notes": [f"Parse Error: {str(e)}"]
        }

    # Add some padding around the bounding box
    padding = 40
    view_width = max(layout.width + padding * 2, 800)
    view_height = layout.height + padding * 2
    
    # Render SVG elements
    svg_inner = layout.render(offset_x=padding, offset_y=padding)

    # Embed the font as base64
    font_def = ""
    font_path = os.path.join(os.getcwd(), "public", "WaHandwriting-Regular.ttf")
    if os.path.exists(font_path):
        import base64
        with open(font_path, "rb") as f:
            font_data = base64.b64encode(f.read()).decode('utf-8')
        font_def = f"""
        <defs>
            <style>
                @font-face {{
                    font-family: 'WaHandwriting-Regular';
                    src: url(data:font/ttf;base64,{font_data}) format('truetype');
                }}
            </style>
        </defs>
        """

    # STRICT OUTPUT RULES: No watermark, no placeholder text, no simulated labels
    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_width} {view_height}" width="{view_width}" height="{view_height}">
        {font_def}
        <rect width="100%" height="100%" fill="#fafafa" rx="10"/>
        {svg_inner}
    </svg>"""

    output_filename = f"output.{output_format.lower()}"
    output_path = os.path.join(os.getcwd(), output_filename)
    preview_path = os.path.join(os.getcwd(), "preview.svg")
    
    # Always write an SVG for the preview panel
    with open(preview_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    notes = ["Rendered successfully using 2D Layout Engine."]
    if is_document_mode:
        notes.append("Detected document/text mode. Automatic line wrapping applied.")
    
    if output_format == "SVG":
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(svg_content)
    else:
        try:
            import cairosvg
            if output_format == "PNG":
                cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=output_path)
            elif output_format == "PDF":
                cairosvg.svg2pdf(bytestring=svg_content.encode('utf-8'), write_to=output_path)
        except Exception as e:
            # Handle generative function errors cleanly
            notes.append(f"Generative function error (cairosvg missing or failed): {str(e)}. Falling back to SVG output.")
            output_path = preview_path
            output_format = "SVG"

    # 4. Return Strict JSON Structure
    return {
        "status": "ok",
        "parsed_files": ["input.tex"],
        "entry_file": "input.tex",
        "document_structure": {
            "type": "expression",
            "detected": ["AST Parsed"]
        },
        "unsupported_items": [],
        "render_plan": {
            "variation_level": variation_level,
            "symbols_used": len(expression.replace(" ", ""))
        },
        "output_files": {
            "svg": preview_path,
            "pdf": output_path if output_format == "PDF" else "",
            "png": output_path if output_format == "PNG" else ""
        },
        "notes": notes
    }
