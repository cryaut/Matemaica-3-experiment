import time
import os
import json
from latex_parser import parse_latex_math, ParseError
from document_parser import parse_document
from layout_engine import layout_document, layout_ast, set_custom_symbols

def render_expression(expression: str, input_mode: str, variation_level: str, seed: int | None, output_format: str, page_style: str = "Blank", ink_color: str = "#333333", custom_symbols: list | None = None) -> dict:
    """
    Backend stub for the Handwritten Math Rendering System.
    Parses LaTeX into AST and uses the 2D layout engine to generate SVG.
    """
    
    set_custom_symbols(custom_symbols or [])
    notes = []

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
                '\\[', '\\(', '\\textbf', '\\section', '\\subsection', '\\subsubsection', '\\paragraph',
                '\\begin', '\\itemize', '\\enumerate', '\\item',
                '\\newpage', '\\newage', '\\documentclass'
            ])
            
            # If it has significant text as well as some math markers
            if not is_doc:
                has_math = any(m in expression for m in ['$', '\\frac', '\\sum', '\\int', '\\lim', '\\alpha', '\\beta', '\\gamma'])
                space_count = expression.count(' ')
                # If it has many spaces and at least one math marker, or very many spaces, it's a document
                if (space_count > 5 and has_math) or space_count > 10:
                    is_doc = True
            
            if is_doc:
                doc_ast = parse_document(expression)
                pages = layout_document(doc_ast, max_width=800, scale=1.0)
                is_document_mode = True
            else:
                try:
                    # Pure math expression
                    ast = parse_latex_math(expression)
                    layout = layout_ast(ast, scale=1.0)
                    pages = [layout]
                    is_document_mode = False
                except Exception:
                    # Fallback to document mode if pure math parsing fails
                    doc_ast = parse_document(expression)
                    pages = layout_document(doc_ast, max_width=800, scale=1.0)
                    is_document_mode = True
            
        else:
            ast = parse_latex_math(expression)
            layout = layout_ast(ast, scale=1.0)
            pages = [layout]
            is_document_mode = False
            
        if not pages:
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

    import base64
    font_b64 = ""
    try:
        font_path = os.path.join(os.getcwd(), "public", "WaHandwriting-Regular.ttf")
        if os.path.exists(font_path):
            with open(font_path, "rb") as f:
                font_b64 = base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        notes.append(f"Font embedding failed: {str(e)}")

    font_style = ""
    if font_b64:
        font_style = f"""
        <style>
        @font-face {{
            font-family: 'WaHandwriting-Regular';
            src: url('data:font/ttf;base64,{font_b64}') format('truetype');
            font-weight: normal;
            font-style: normal;
        }}
        </style>"""

    svg_pages = []
    for page in pages:
        if getattr(page, 'is_page', False):
            view_width = page.width
            view_height = page.height
            svg_inner = page.render(offset_x=0, offset_y=0, page_style=page_style)
            bg_rect = f'<rect width="100%" height="100%" fill="#ffffff" />'
        else:
            padding = 40
            view_width = max(page.width + padding * 2, 800)
            view_height = max(page.height + padding * 2, 400)
            svg_inner = page.render(offset_x=padding + 60, offset_y=padding, page_style="Blank") # Shift math right to avoid margin
            
            bg_lines = ""
            if page_style == "Lined":
                for y in range(30, int(view_height), 30):
                    bg_lines += f'<line x1="0" y1="{y}" x2="{view_width}" y2="{y}" stroke="#93c5fd" stroke-width="1"/>\n'
                bg_lines += f'<line x1="80" y1="0" x2="80" y2="{view_height}" stroke="#fca5a5" stroke-width="1.5"/>\n'
            elif page_style == "Grid":
                for y in range(30, int(view_height), 30):
                    bg_lines += f'<line x1="0" y1="{y}" x2="{view_width}" y2="{y}" stroke="#e5e7eb" stroke-width="1"/>\n'
                for x in range(30, int(view_width), 30):
                    bg_lines += f'<line x1="{x}" y1="0" x2="{x}" y2="{view_height}" stroke="#e5e7eb" stroke-width="1"/>\n'
                    
            bg_rect = f'<rect width="100%" height="100%" fill="#fafafa" rx="10"/>\n{bg_lines}'
            
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {view_width} {view_height}" width="{view_width}" height="{view_height}">
            <defs>{font_style}</defs>
            {bg_rect}
            {svg_inner}
        </svg>"""
        
        # Apply ink color
        if ink_color != "#333333":
            svg_content = svg_content.replace('stroke="#333"', f'stroke="{ink_color}"')
            svg_content = svg_content.replace('fill="#333"', f'fill="{ink_color}"')
            
        svg_pages.append(svg_content)

    notes = ["Rendered successfully using 2D Layout Engine."]
    if is_document_mode:
        notes.append("Detected document/text mode. Automatic line wrapping applied.")
    
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
            "svg": "" # We don't write files anymore, we send the content directly
        },
        "svg_content": svg_pages[0] if svg_pages else "",
        "svg_pages": svg_pages,
        "notes": notes
    }
