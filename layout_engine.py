import json
from typing import Any, Dict, List, Tuple

class BoundingBox:
    """Represents a 2D bounding box for mathematical layout."""
    def __init__(self, width: float, height: float, baseline: float):
        self.width = width
        self.height = height
        self.baseline = baseline
        self.x = 0.0
        self.y = 0.0
        self.elements = []  # List of either BoundingBox or (dx, dy, svg_string)
        self.is_rect = False

    def render(self, offset_x: float = 0, offset_y: float = 0) -> str:
        out = []
        cx = offset_x + self.x
        cy = offset_y + self.y
        
        if self.is_rect:
            # Handwritten box using a path
            path = f"M {cx+2} {cy+2} L {cx+self.width-2} {cy+1} L {cx+self.width-1} {cy+self.height-2} L {cx+1} {cy+self.height-1} Z"
            out.append(f'<path d="{path}" fill="none" stroke="#222" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />')
            
        for el in self.elements:
            if isinstance(el, BoundingBox):
                out.append(el.render(cx, cy))
            else:
                dx, dy, svg = el
                out.append(f'<g transform="translate({cx + dx}, {cy + dy})">{svg}</g>')
        return "\n".join(out)

def get_symbol_box(symbol: str, scale: float = 1.0) -> BoundingBox:
    """
    Simulates loading a handwritten SVG symbol.
    In a full production system, this would load an actual SVG file,
    measure its viewBox, and apply natural handwriting variation (rotation/scale).
    """
    # Basic mapping for common LaTeX commands to Unicode for the fallback font
    charmap = {
        '\\int': '∫', '\\iint': '∬', '\\iiint': '∭', '\\oint': '∮', '\\oiint': '∯',
        '\\sum': '∑', '\\prod': '∏', '\\coprod': '∐', '\\bigcup': '⋃', '\\bigcap': '⋂',
        '\\partial': '∂', '\\nabla': '∇', '\\Delta': 'Δ', '\\delta': 'δ', '\\diracdelta': 'δ',
        '\\infty': '∞', '\\to': '→', '\\alpha': 'α', '\\beta': 'β',
        '\\theta': 'θ', '\\pi': 'π', '\\sin': 'sin', '\\cos': 'cos',
        '\\tan': 'tan', '\\log': 'log', '\\ln': 'ln',
        '\\div': '÷', '\\times': '×', '\\cdot': '·', '\\approx': '≈', '\\sim': '∼', '\\propto': '∝',
        '\\ast': '∗', '\\star': '⋆', '\\imath': 'ı', '\\jmath': 'ȷ',
        '\\,': ' ', '\\;': '  ', '\\:': '  ', '\\!': '', '\\quad': '    ', '\\qquad': '        ',
        '\\|': '∥', '\\ge': '≥', '\\le': '≤', '\\geq': '≥', '\\leq': '≤',
        '\\Rightarrow': '⇒', '\\Leftarrow': '⇐', '\\Leftrightarrow': '⇔',
        '\\rightarrow': '→', '\\leftarrow': '←', '\\leftrightarrow': '↔',
        '\\neq': '≠', '\\{': '{', '\\}': '}', '\\langle': '⟨', '\\rangle': '⟩',
        '\\mid': '|', '\\implies': '⟹',
        '\\dots': '...', '\\cdots': '⋯', '\\ddots': '⋱', '\\vdots': '⋮'
    }
    
    # Custom SVG paths for handwritten operators
    custom_svg_paths = {
        '\\int': '<path d="M 12 2 C 18 -2, 16 10, 12 18 C 8 26, 6 38, 12 34" stroke="#222" fill="none" stroke-width="1.5" stroke-linecap="round"/>',
        '\\iint': '<path d="M 8 2 C 14 -2, 12 10, 8 18 C 4 26, 2 38, 8 34 M 18 2 C 24 -2, 22 10, 18 18 C 14 26, 12 38, 18 34" stroke="#222" fill="none" stroke-width="1.5" stroke-linecap="round"/>',
        '\\iiint': '<path d="M 6 2 C 12 -2, 10 10, 6 18 C 2 26, 0 38, 6 34 M 14 2 C 20 -2, 18 10, 14 18 C 10 26, 8 38, 14 34 M 22 2 C 28 -2, 26 10, 22 18 C 18 26, 16 38, 22 34" stroke="#222" fill="none" stroke-width="1.5" stroke-linecap="round"/>',
        '\\oint': '<path d="M 12 2 C 18 -2, 16 10, 12 18 C 8 26, 6 38, 12 34 M 12 18 A 4 4 0 1 0 12 17.9" stroke="#222" fill="none" stroke-width="1.5" stroke-linecap="round"/>',
        '\\sum': '<path d="M 20 4 L 6 4 L 14 12 L 6 20 L 20 20" stroke="#222" fill="none" stroke-width="1.5" stroke-linejoin="round"/>',
        '\\prod': '<path d="M 6 20 L 6 4 L 18 4 L 18 20 M 6 4 L 18 4" stroke="#222" fill="none" stroke-width="1.5" stroke-linejoin="round"/>',
        '\\nabla': '<path d="M 2 4 L 22 4 L 12 20 Z" stroke="#222" fill="none" stroke-width="1.5" stroke-linejoin="round"/>',
        '\\partial': '<path d="M 14 4 C 8 4, 6 12, 6 16 C 6 20, 10 22, 14 20 C 18 18, 18 12, 14 10 C 10 8, 8 12, 8 16" stroke="#222" fill="none" stroke-width="1.5"/>',
    }

    if symbol in custom_svg_paths:
        width = 24 * scale
        height = 36 * scale
        baseline = 24 * scale
        if symbol in ('\\sum', '\\prod'):
            width = 26 * scale
            height = 24 * scale
            baseline = 20 * scale
        elif symbol in ('\\nabla', '\\partial'):
            width = 24 * scale
            height = 24 * scale
            baseline = 20 * scale
        elif symbol == '\\iint':
            width = 32 * scale
        elif symbol == '\\iiint':
            width = 40 * scale
            
        box = BoundingBox(width, height, baseline)
        svg_content = f'<g transform="scale({scale})">{custom_svg_paths[symbol]}</g>'
        box.elements.append((0, 0, svg_content))
        return box
        
    display_text = charmap.get(symbol, symbol)
    
    # Heuristic sizing
    font_size = 24 * scale
    char_width = font_size * 0.6
    width = char_width * len(display_text)
    height = font_size * 1.2
    baseline = font_size * 0.8
    
    # Special sizing for large operators
    if symbol in ('\\int', '\\iint', '\\iiint', '\\oint', '\\oiint', '\\sum', '\\prod', '\\coprod', '\\bigcup', '\\bigcap'):
        font_size *= 1.5
        width *= 1.5
        height *= 1.5
        baseline *= 1.5

    box = BoundingBox(width, height, baseline)
    safe_sym = display_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    # We use a cursive font to simulate handwriting for now
    svg = f'<text font-family="\'WaHandwriting-Regular\', cursive, sans-serif" font-size="{font_size}" fill="#222">{safe_sym}</text>'
    box.elements.append((0, baseline, svg))
    return box

def layout_ast(node: Any, scale: float = 1.0) -> BoundingBox:
    """Recursively computes the 2D layout for an AST node."""
    if not node:
        return BoundingBox(0, 0, 0)
        
    node_type = node.get("type")
    
    # Handle scale modifiers like \Big
    modifier = node.get("scale_modifier")
    if modifier:
        if modifier in ('\\big', '\\bigl', '\\bigr'): scale *= 1.2
        elif modifier in ('\\Big', '\\Bigl', '\\Bigr'): scale *= 1.5
        elif modifier in ('\\bigg', '\\biggl', '\\biggr'): scale *= 2.0
        elif modifier in ('\\Bigg', '\\Biggl', '\\Biggr'): scale *= 2.5
    
    if node_type in ("symbol", "variable", "number", "operator", "command"):
        val = node.get("value") or node.get("name") or ""
        return get_symbol_box(val, scale)
        
    elif node_type == "text_mode":
        # Just layout the content. In a real engine we'd change the font style,
        # but here everything is handwritten anyway.
        return layout_ast(node.get("content"), scale)
        
    elif node_type == "text":
        val = node.get("value") or ""
        # We can just treat it as a sequence of symbols, or a single string
        # Since it's text, we can just render it as a single block
        font_size = 32 * scale
        char_width = font_size * 0.55
        width = len(val) * char_width
        height = font_size * 1.2
        baseline = font_size
        
        box = BoundingBox(width, height, baseline)
        weight = "bold" if node.get("bold") else "normal"
        safe_val = val.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        svg = f'<text font-family="\'WaHandwriting-Regular\', cursive, sans-serif" font-weight="{weight}" font-size="{font_size}" fill="#222">{safe_val}</text>'
        box.elements.append((0, baseline, svg))
        return box
        
    elif node_type == "sequence":
        boxes = [layout_ast(child, scale) for child in node.get("items", [])]
        if not boxes:
            return BoundingBox(0, 0, 0)
            
        # Horizontal layout
        spacing = 4 * scale
        total_width = sum(b.width for b in boxes) + spacing * (len(boxes) - 1)
        max_baseline = max(b.baseline for b in boxes)
        max_descent = max(b.height - b.baseline for b in boxes)
        
        container = BoundingBox(total_width, max_baseline + max_descent, max_baseline)
        current_x = 0
        for b in boxes:
            b.x = current_x
            b.y = max_baseline - b.baseline
            container.elements.append(b)
            current_x += b.width + spacing
        return container
        
    elif node_type == "fraction":
        num = layout_ast(node.get("numerator"), scale * 0.85)
        den = layout_ast(node.get("denominator"), scale * 0.85)
        
        padding = 4 * scale
        width = max(num.width, den.width) + padding * 2
        
        num.x = (width - num.width) / 2
        den.x = (width - den.width) / 2
        
        num.y = 0
        bar_y = num.height + 2 * scale
        den.y = bar_y + 2 * scale
        
        total_height = den.y + den.height
        baseline = bar_y + 1 * scale
        
        container = BoundingBox(width, total_height, baseline)
        container.elements.append(num)
        container.elements.append(den)
        
        # Fraction bar (simulated hand-drawn line)
        curve_offset = 1.0 * scale
        bar_svg = f'<path d="M 2 {bar_y} Q {width/2} {bar_y + curve_offset} {width-2} {bar_y - (0.5 * scale)}" stroke="#222" stroke-width="{1.5*scale}" fill="none" stroke-linecap="round"/>'
        container.elements.append((0, 0, bar_svg))
        return container
        
    elif node_type == "power":
        base = layout_ast(node.get("base"), scale)
        exp = layout_ast(node.get("exponent"), scale * 0.7)
        
        exp.x = base.width + 2 * scale
        exp.y = base.y - exp.height * 0.5
        if exp.y < 0:
            shift = -exp.y
            base.y += shift
            exp.y += shift
            
        width = exp.x + exp.width
        height = max(base.y + base.height, exp.y + exp.height)
        baseline = base.y + base.baseline
        
        container = BoundingBox(width, height, baseline)
        container.elements.append(base)
        container.elements.append(exp)
        return container
        
    elif node_type == "subscript":
        base = layout_ast(node.get("base"), scale)
        sub = layout_ast(node.get("subscript"), scale * 0.7)
        
        sub.x = base.width + 2 * scale
        sub.y = base.y + base.baseline + 2 * scale
        
        width = sub.x + sub.width
        height = max(base.y + base.height, sub.y + sub.height)
        baseline = base.y + base.baseline
        
        container = BoundingBox(width, height, baseline)
        container.elements.append(base)
        container.elements.append(sub)
        return container
        
    elif node_type == "integral":
        variant = node.get("variant", "\\int")
        int_sym = get_symbol_box(variant, scale)
        
        lower = layout_ast(node.get("lower_bound"), scale * 0.7) if node.get("lower_bound") else None
        upper = layout_ast(node.get("upper_bound"), scale * 0.7) if node.get("upper_bound") else None
        
        # Place bounds
        if node.get("limits"):
            # Center above/below
            if upper:
                upper.x = (int_sym.width - upper.width) / 2
                upper.y = 0
                int_sym.y = upper.height + 2 * scale
            else:
                int_sym.y = 0
                
            if lower:
                lower.x = (int_sym.width - lower.width) / 2
                lower.y = int_sym.y + int_sym.height + 2 * scale
        else:
            # Side placement
            if upper:
                upper.x = int_sym.width * 0.6
                upper.y = 0
                int_sym.y = upper.height
            else:
                int_sym.y = 0
                
            if lower:
                lower.x = int_sym.width * 0.6
                lower.y = int_sym.y + int_sym.height - lower.height * 0.5
            
        sym_width = max([int_sym.width] + ([upper.x + upper.width] if upper else []) + ([lower.x + lower.width] if lower else []))
        
        integrand = layout_ast(node.get("integrand"), scale)
        integrand.x = sym_width + 8 * scale
        integrand.y = int_sym.y + int_sym.baseline - integrand.baseline
        
        diff = layout_ast(node.get("differential"), scale) if node.get("differential") else None
        if diff:
            diff.x = integrand.x + integrand.width + 8 * scale
            diff.y = int_sym.y + int_sym.baseline - diff.baseline
            
        total_width = (diff.x + diff.width) if diff else (integrand.x + integrand.width)
        total_height = max([b.y + b.height for b in filter(None, [int_sym, upper, lower, integrand, diff])])
        baseline = int_sym.y + int_sym.baseline
        
        container = BoundingBox(total_width, total_height, baseline)
        container.elements.append(int_sym)
        if upper: container.elements.append(upper)
        if lower: container.elements.append(lower)
        container.elements.append(integrand)
        if diff: container.elements.append(diff)
        return container
        
    elif node_type == "environment":
        name = node.get("name", "align")
        rows = node.get("rows", [])
        
        # Layout all cells
        layout_rows = []
        col_widths = []
        
        for row in rows:
            layout_row = []
            for i, cell in enumerate(row):
                cell_box = layout_ast(cell, scale)
                layout_row.append(cell_box)
                if i >= len(col_widths):
                    col_widths.append(cell_box.width)
                else:
                    col_widths[i] = max(col_widths[i], cell_box.width)
            layout_rows.append(layout_row)
            
        # Assemble grid
        col_spacing = 15 * scale
        row_spacing = 20 * scale
        
        current_y = 0
        container_elements = []
        max_width = 0
        
        for layout_row in layout_rows:
            current_x = 0
            row_baseline = max((c.baseline for c in layout_row), default=0)
            row_height = max((c.height for c in layout_row), default=0)
            
            for i, cell in enumerate(layout_row):
                # Align environments: alternating right/left alignment
                if name in ("align", "align*"):
                    if i % 2 == 0: # Right align
                        cell.x = current_x + (col_widths[i] - cell.width)
                    else: # Left align
                        cell.x = current_x
                else: # Matrix / cases: center or left align
                    cell.x = current_x + (col_widths[i] - cell.width) / 2
                    
                cell.y = current_y + (row_baseline - cell.baseline)
                container_elements.append(cell)
                current_x += col_widths[i] + col_spacing
                
            max_width = max(max_width, current_x)
            current_y += row_height + row_spacing
            
        container = BoundingBox(max_width, current_y, current_y / 2)
        container.elements.extend(container_elements)
        return container

    elif node_type == "group":
        content = layout_ast(node.get("content"), scale)
        
        # Calculate required scale for delimiters
        # A normal symbol has height ~ 28.8 * scale
        # We want the delimiter to be slightly larger than the content
        target_height = max(content.height, 28.8 * scale)
        delim_scale = scale * (target_height / (28.8 * scale)) * 0.9
        
        if node.get("style") == "parentheses":
            lparen = get_symbol_box("(", delim_scale)
            rparen = get_symbol_box(")", delim_scale)
        elif node.get("style") == "brackets":
            lparen = get_symbol_box("[", delim_scale)
            rparen = get_symbol_box("]", delim_scale)
        elif node.get("style") == "left_right":
            left_delim = node.get("left_delim")
            right_delim = node.get("right_delim")
            
            if left_delim != '.':
                lparen = get_symbol_box(left_delim, delim_scale)
            else:
                lparen = BoundingBox(0, 0, 0)
                
            if right_delim != '.':
                rparen = get_symbol_box(right_delim, delim_scale)
            else:
                rparen = BoundingBox(0, 0, 0)
        else:
            return content
            
        lparen.x = 0
        content.x = lparen.width
        rparen.x = content.x + content.width
        
        max_baseline = max(lparen.baseline, content.baseline, rparen.baseline)
        lparen.y = max_baseline - lparen.baseline
        content.y = max_baseline - content.baseline
        rparen.y = max_baseline - rparen.baseline
        
        width = rparen.x + rparen.width
        height = max(lparen.y + lparen.height, content.y + content.height, rparen.y + rparen.height)
        
        container = BoundingBox(width, height, max_baseline)
        container.elements.extend([lparen, content, rparen])
        return container
        
    elif node_type in ("summation", "product"):
        sym_val = node.get("variant", "\\sum" if node_type == "summation" else "\\prod")
        sym = get_symbol_box(sym_val, scale)
        
        lower_node = None
        if node.get("index"):
            lower_node = {"type": "sequence", "items": [node["index"], {"type": "operator", "value": "="}, node["lower_bound"]]}
        else:
            lower_node = node.get("lower_bound")
            
        lower = layout_ast(lower_node, scale * 0.7) if lower_node else None
        upper = layout_ast(node.get("upper_bound"), scale * 0.7) if node.get("upper_bound") else None
        
        sym_center = sym.width / 2
        
        if upper:
            upper.x = sym_center - upper.width / 2
            upper.y = 0
            sym.y = upper.height + 2 * scale
        else:
            sym.y = 0
            
        sym.x = max(0, (upper.width / 2 - sym_center) if upper else 0, (lower.width / 2 - sym_center) if lower else 0)
        if upper: upper.x += sym.x
        
        if lower:
            lower.x = sym.x + sym_center - lower.width / 2
            lower.y = sym.y + sym.height + 2 * scale
            
        sym_total_width = max([sym.x + sym.width] + ([upper.x + upper.width] if upper else []) + ([lower.x + lower.width] if lower else []))
        
        body = layout_ast(node.get("body"), scale)
        body.x = sym_total_width + 5 * scale
        body.y = sym.y + sym.baseline - body.baseline
        
        total_width = body.x + body.width
        total_height = max([b.y + b.height for b in filter(None, [sym, upper, lower, body])])
        baseline = sym.y + sym.baseline
        
        container = BoundingBox(total_width, total_height, baseline)
        container.elements.append(sym)
        if upper: container.elements.append(upper)
        if lower: container.elements.append(lower)
        container.elements.append(body)
        return container
        
    elif node_type == "limit":
        sym = get_symbol_box("lim", scale)
        
        var_node = node.get("variable")
        target_node = node.get("target")
        
        cond_node = None
        if var_node and target_node:
            cond_node = {"type": "sequence", "items": [var_node, {"type": "symbol", "value": "\\to"}, target_node]}
            
        cond = layout_ast(cond_node, scale * 0.7) if cond_node else None
        
        sym_center = sym.width / 2
        
        if cond:
            cond_center = cond.width / 2
            sym.x = max(0, cond_center - sym_center)
            sym.y = 0
            cond.x = max(0, sym_center - cond_center)
            cond.y = sym.height + 2 * scale
        else:
            sym.x = 0
            sym.y = 0
            
        sym_total_width = max(sym.x + sym.width, (cond.x + cond.width) if cond else 0)
        
        body = layout_ast(node.get("body"), scale)
        body.x = sym_total_width + 5 * scale
        body.y = sym.y + sym.baseline - body.baseline
        
        total_width = body.x + body.width
        total_height = max((cond.y + cond.height) if cond else sym.height, body.y + body.height)
        baseline = sym.y + sym.baseline
        
        container = BoundingBox(total_width, total_height, baseline)
        container.elements.append(sym)
        if cond: container.elements.append(cond)
        container.elements.append(body)
        return container
        
    elif node_type == "sqrt":
        radicand = layout_ast(node.get("radicand"), scale)
        
        padding = 4 * scale
        rad_x = 15 * scale
        rad_y = padding
        
        radicand.x = rad_x
        radicand.y = rad_y
        
        width = rad_x + radicand.width + padding
        height = radicand.height + padding * 2
        baseline = radicand.y + radicand.baseline
        
        container = BoundingBox(width, height, baseline)
        container.elements.append(radicand)
        
        # Handwritten sqrt path
        path = f"M 2 {height/2 + scale} L 7 {height-2} L {rad_x - 2} 2 Q {rad_x + (width-rad_x)/2} {2 + scale} {width} {2 - scale}"
        svg = f'<path d="{path}" stroke="#222" stroke-width="{1.5*scale}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        container.elements.append((0, 0, svg))
        
        return container

    elif node_type == "accent":
        body = layout_ast(node.get("body"), scale)
        name = node.get("name")
        
        accent_char = ""
        if name == "\\vec": accent_char = "→"
        elif name == "\\hat": accent_char = "^"
        elif name == "\\dot": accent_char = "˙"
        elif name == "\\ddot": accent_char = "¨"
        elif name == "\\mathbf":
            # Just render body bolder if possible, or just return body
            return body
            
        acc_box = get_symbol_box(accent_char, scale * 0.7)
        acc_box.x = (body.width - acc_box.width) / 2
        acc_box.y = 0
        body.x = 0
        body.y = acc_box.height
        
        width = max(body.width, acc_box.x + acc_box.width)
        height = body.y + body.height
        baseline = body.y + body.baseline
        
        container = BoundingBox(width, height, baseline)
        container.elements.append(acc_box)
        container.elements.append(body)
        return container
        
    elif node_type == "binom":
        upper = layout_ast(node.get("upper"), scale * 0.85)
        lower = layout_ast(node.get("lower"), scale * 0.85)
        
        lparen = get_symbol_box("(", scale * 1.5)
        rparen = get_symbol_box(")", scale * 1.5)
        
        padding = 4 * scale
        content_width = max(upper.width, lower.width)
        
        upper.x = lparen.width + padding + (content_width - upper.width) / 2
        lower.x = lparen.width + padding + (content_width - lower.width) / 2
        
        upper.y = 0
        lower.y = upper.height + 4 * scale
        
        content_height = lower.y + lower.height
        
        lparen.x = 0
        lparen.y = (content_height - lparen.height) / 2
        
        rparen.x = lparen.width + padding * 2 + content_width
        rparen.y = (content_height - rparen.height) / 2
        
        width = rparen.x + rparen.width
        baseline = upper.height + 2 * scale
        
        container = BoundingBox(width, content_height, baseline)
        container.elements.extend([lparen, upper, lower, rparen])
        return container

    elif node_type == "boxed":
        content = layout_ast(node.get("content"), scale)
        padding = 8 * scale
        
        content.x = padding
        content.y = padding
        
        width = content.width + padding * 2
        height = content.height + padding * 2
        baseline = content.baseline + padding
        
        container = BoundingBox(width, height, baseline)
        
        # Add a rectangle element for the box
        rect = BoundingBox(width, height, 0)
        rect.is_rect = True
        
        container.elements.extend([rect, content])
        return container

    elif node_type == "differential":
        op = get_symbol_box(node.get("operator", "d"), scale)
        var = layout_ast(node.get("variable"), scale)
        
        op.x = 0
        var.x = op.width
        
        max_baseline = max(op.baseline, var.baseline)
        op.y = max_baseline - op.baseline
        var.y = max_baseline - var.baseline
        
        width = var.x + var.width
        height = max(op.y + op.height, var.y + var.height)
        
        container = BoundingBox(width, height, max_baseline)
        container.elements.extend([op, var])
        return container

    # Fallback for unhandled nodes
    return get_symbol_box(f"[{node_type}]", scale)

def layout_paragraph(content: list, max_width: float, scale: float) -> BoundingBox:
    font_size = 20 * scale
    char_width = font_size * 0.55
    line_spacing = font_size * 1.5
    
    container = BoundingBox(max_width, 0, 0)
    current_x = 0
    current_y = 0
    max_baseline = font_size
    max_descent = font_size * 0.3
    
    line_elements = []
    
    def flush_line():
        nonlocal current_x, current_y, max_baseline, max_descent, line_elements
        if not line_elements: return
        
        for el in line_elements:
            el.y = current_y + (max_baseline - el.baseline)
            container.elements.append(el)
            
        current_y += max_baseline + max_descent + (line_spacing * 0.5)
        current_x = 0
        max_baseline = font_size
        max_descent = font_size * 0.3
        line_elements = []

    for item in content:
        if item["type"] == "text":
            # Split by whitespace but keep track of spaces
            words = item["value"].split()
            if not words:
                # Handle case with only spaces
                current_x += len(item["value"]) * char_width
                continue
                
            for word in words:
                word_width = len(word) * char_width
                if current_x + word_width > max_width and current_x > 0:
                    flush_line()
                
                box = BoundingBox(word_width, font_size * 1.2, font_size)
                weight = "bold" if item.get("bold") else "normal"
                safe_word = word.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                svg = f'<text font-family="\'WaHandwriting-Regular\', cursive, sans-serif" font-weight="{weight}" font-size="{font_size}" fill="#333">{safe_word}</text>'
                box.elements.append((0, font_size, svg))
                
                box.x = current_x
                line_elements.append(box)
                current_x += word_width + char_width
                
        elif item["type"] == "inline_math":
            box = layout_ast(item["ast"], scale * 0.9)
            if current_x + box.width > max_width and current_x > 0:
                flush_line()
            box.x = current_x
            line_elements.append(box)
            current_x += box.width + char_width
            max_baseline = max(max_baseline, box.baseline)
            max_descent = max(max_descent, box.height - box.baseline)
            
    flush_line()
    container.height = current_y
    return container

def layout_document(doc_ast: list, max_width: float = 800, scale: float = 1.0) -> BoundingBox:
    container = BoundingBox(max_width, 0, 0)
    current_y = 0
    for block in doc_ast:
        if block["type"] == "paragraph":
            box = layout_paragraph(block["content"], max_width, scale)
            box.y = current_y
            container.elements.append(box)
            current_y += box.height + 20 * scale
        elif block["type"] == "display_math":
            box = layout_ast(block["ast"], scale * 1.2)
            box.x = (max_width - box.width) / 2
            if box.x < 0: box.x = 0
            box.y = current_y + 10 * scale
            container.elements.append(box)
            current_y += box.height + 30 * scale
        elif block["type"] == "header":
            box = layout_paragraph(block["content"], max_width, scale * 1.2)
            box.y = current_y
            container.elements.append(box)
            current_y += box.height + 20 * scale
    container.height = current_y
    return container
