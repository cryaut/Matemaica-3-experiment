import json
import re
import random
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
        self.is_intertext = False

    def render(self, offset_x: float = 0, offset_y: float = 0, page_style: str = "Blank") -> str:
        out = []
        cx = offset_x + self.x
        cy = offset_y + self.y
        
        if getattr(self, 'is_page', False):
            # Draw a white page with a fake shadow
            out.append(f'<rect x="{cx+4}" y="{cy+4}" width="{self.width}" height="{self.height}" fill="#d1d5db" rx="4" />')
            out.append(f'<rect x="{cx}" y="{cy}" width="{self.width}" height="{self.height}" fill="#ffffff" stroke="#e5e7eb" stroke-width="1" rx="4" />')
            
            if page_style == "Lined":
                # Draw horizontal lines
                for y in range(30, int(self.height), 30):
                    out.append(f'<line x1="{cx}" y1="{cy+y}" x2="{cx+self.width}" y2="{cy+y}" stroke="#93c5fd" stroke-width="1"/>')
                # Draw red margin line
                out.append(f'<line x1="{cx+80}" y1="{cy}" x2="{cx+80}" y2="{cy+self.height}" stroke="#fca5a5" stroke-width="1.5"/>')
            elif page_style == "Grid":
                # Draw grid lines
                for y in range(30, int(self.height), 30):
                    out.append(f'<line x1="{cx}" y1="{cy+y}" x2="{cx+self.width}" y2="{cy+y}" stroke="#e5e7eb" stroke-width="1"/>')
                for x in range(30, int(self.width), 30):
                    out.append(f'<line x1="{cx+x}" y1="{cy}" x2="{cx+x}" y2="{cy+self.height}" stroke="#e5e7eb" stroke-width="1"/>')
            
        if self.is_rect:
            # Handwritten box using a path
            path = f"M {cx+2} {cy+2} L {cx+self.width-2} {cy+1} L {cx+self.width-1} {cy+self.height-2} L {cx+1} {cy+self.height-1} Z"
            out.append(f'<path d="{path}" fill="none" stroke="#333" stroke-width="0.6" stroke-linejoin="round" stroke-linecap="round" />')
            
        for el in self.elements:
            if isinstance(el, BoundingBox):
                out.append(el.render(cx, cy, page_style))
            else:
                dx, dy, svg = el
                out.append(f'<g transform="translate({cx + dx}, {cy + dy})">{svg}</g>')
        return "\\n".join(out)

def get_symbol_box(symbol: str, scale: float = 1.0, scale_y: float = None) -> BoundingBox:
    if scale_y is None:
        scale_y = scale
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
        '\\int': '<path d="M 12 2 C 18 -2, 16 10, 12 18 C 8 26, 6 38, 12 34" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\iint': '<path d="M 8 2 C 14 -2, 12 10, 8 18 C 4 26, 2 38, 8 34 M 18 2 C 24 -2, 22 10, 18 18 C 14 26, 12 38, 18 34" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\iiint': '<path d="M 6 2 C 12 -2, 10 10, 6 18 C 2 26, 0 38, 6 34 M 14 2 C 20 -2, 18 10, 14 18 C 10 26, 8 38, 14 34 M 22 2 C 28 -2, 26 10, 22 18 C 18 26, 16 38, 22 34" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\oint': '<path d="M 12 2 C 18 -2, 16 10, 12 18 C 8 26, 6 38, 12 34 M 12 18 A 4 4 0 1 0 12 17.9" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\sum': '<path d="M 18.6 6.4 C 18.2 6.0 18.3 5.2 18.3 4.7 C 18.3 4.7 18.3 4.2 18.3 4.2 C 18.4 4.1 18.7 4.1 18.7 4.0 C 18.2 4.0 17.8 4.1 17.3 4.2 C 16.4 4.4 15.4 4.5 14.4 4.7 C 13.7 4.9 13.0 5.0 12.3 5.1 C 12.0 5.2 11.7 5.1 11.4 5.1 C 10.8 5.1 10.1 5.1 9.4 5.1 C 9.2 5.1 9.0 5.2 8.8 5.1 C 8.7 5.1 8.6 5.1 8.5 5.1 C 8.5 5.1 8.4 4.9 8.4 5.0 C 8.4 5.4 9.0 5.8 9.3 6.1 C 9.5 6.3 9.5 6.3 9.7 6.5 C 9.9 6.5 10.0 6.5 10.1 6.6 C 10.3 6.7 10.6 6.9 10.7 7.1 C 11.1 7.6 11.2 8.3 11.7 8.7 C 12.2 9.2 13.1 9.6 13.5 10.3 C 13.6 10.5 13.9 10.7 14.0 11.0 C 14.2 11.2 14.3 11.2 14.3 11.4 C 14.2 11.8 13.9 12.0 13.7 12.3 C 13.3 12.7 13.0 13.2 12.5 13.6 C 12.1 13.9 11.8 14.5 11.5 14.9 C 11.3 15.2 10.9 15.4 10.6 15.6 C 9.9 16.2 10.9 15.4 10.4 15.9 C 9.9 16.4 9.2 16.9 8.7 17.2 C 8.4 17.4 8.3 17.6 8.1 17.9 C 8.0 18.0 7.8 18.0 7.8 18.2 C 7.7 18.3 7.7 18.4 7.7 18.6 C 7.7 18.6 7.5 18.9 7.4 18.9 C 7.4 18.9 7.3 18.9 7.3 18.9 C 7.5 19.2 7.8 19.1 8.1 19.1 C 8.8 19.1 9.5 19.1 10.2 19.1 C 11.6 19.1 13.0 19.2 14.3 18.9 C 14.7 18.9 15.2 18.9 15.6 18.9 C 16.5 18.9 17.4 18.9 18.3 18.9 C 17.5 17.2 18.3 20.0 17.9 18.8 C 17.8 18.5 18.0 18.2 18.1 18.0 C 18.1 17.9 18.1 17.7 18.1 17.6 C 18.2 17.3 18.2 17.1 18.0 16.8" stroke="#333" fill="none" stroke-width="0.6" stroke-linecap="round"/>',
        '\\prod': '<path d="M 6 20 L 6 4 L 18 4 L 18 20 M 6 4 L 18 4" stroke="#333" fill="none" stroke-width="1.0" stroke-linejoin="round"/>',
        '\\nabla': '<path d="M 2 4 L 22 4 L 12 20 Z" stroke="#333" fill="none" stroke-width="1.0" stroke-linejoin="round"/>',
        '\\partial': '<path d="M 14 4 C 8 4, 6 12, 6 16 C 6 20, 10 22, 14 20 C 18 18, 18 12, 14 10 C 10 8, 8 12, 8 16" stroke="#333" fill="none" stroke-width="1.0"/>',
        '\\{': '<path d="M 11 4 C 8 7, 9 11, 7 16 C 6 18, 4 20, 2 20 C 5 21, 6 23, 7 25 C 8 31, 7 34, 11 36" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\}': '<path d="M 5 4 C 8 7, 7 11, 9 16 C 10 18, 12 20, 14 20 C 11 21, 10 23, 9 25 C 8 31, 9 34, 5 36" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\mid': '<path d="M 6 4 Q 7 16 5 28" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\|': '<path d="M 4 4 Q 5 16 3 28 M 8 4 Q 7 16 9 28" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\le': '<path d="M 18 10 L 6 16 L 18 22 M 6 26 L 18 26" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\leq': '<path d="M 18 10 L 6 16 L 18 22 M 6 26 L 18 26" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\ge': '<path d="M 6 10 L 18 16 L 6 22 M 6 26 L 18 26" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\geq': '<path d="M 6 10 L 18 16 L 6 22 M 6 26 L 18 26" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\neq': '<path d="M 6 14 L 18 14 M 6 20 L 18 20 M 16 8 L 8 26" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\approx': '<path d="M 6 14 C 10 10, 14 18, 18 14 M 6 20 C 10 16, 14 24, 18 20" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\rightarrow': '<path d="M 4.0 16.2 C 4.4 16.2 4.8 16.2 5.2 16.3 C 5.4 16.3 5.6 16.2 5.9 16.3 C 6.2 16.3 6.7 16.4 7.1 16.3 C 7.5 16.2 7.9 16.0 8.3 15.8 C 8.5 15.8 8.8 15.8 9.0 15.8 C 9.6 15.8 10.1 15.8 10.7 15.8 C 12.7 15.8 14.7 15.8 16.7 15.8 M 13.2 11.8 C 14.6 12.1 15.7 12.9 16.8 13.7 C 17.0 13.7 17.0 13.9 17.1 14.0 C 17.3 14.1 17.5 14.2 17.7 14.4 C 17.9 14.5 18.3 14.7 18.5 14.8 C 18.6 14.9 18.8 14.8 18.9 14.8 C 19.2 14.9 19.3 15.0 19.5 15.1 C 19.6 15.2 20.0 15.2 20.0 15.3 C 19.8 15.7 19.5 15.7 19.2 15.9 C 18.9 16.1 18.6 16.3 18.4 16.5 C 18.1 16.7 18.0 17.0 17.7 17.2 C 17.6 17.2 17.4 17.3 17.4 17.3 C 17.1 17.6 16.8 17.8 16.4 18.0 C 16.0 18.2 15.6 18.2 15.2 18.4 C 15.0 18.5 14.9 18.6 14.8 18.7 C 14.4 18.9 13.9 19.0 13.5 19.1 C 13.1 19.3 12.7 19.5 12.4 19.6" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\to': '<path d="M 4.0 16.2 C 4.4 16.2 4.8 16.2 5.2 16.3 C 5.4 16.3 5.6 16.2 5.9 16.3 C 6.2 16.3 6.7 16.4 7.1 16.3 C 7.5 16.2 7.9 16.0 8.3 15.8 C 8.5 15.8 8.8 15.8 9.0 15.8 C 9.6 15.8 10.1 15.8 10.7 15.8 C 12.7 15.8 14.7 15.8 16.7 15.8 M 13.2 11.8 C 14.6 12.1 15.7 12.9 16.8 13.7 C 17.0 13.7 17.0 13.9 17.1 14.0 C 17.3 14.1 17.5 14.2 17.7 14.4 C 17.9 14.5 18.3 14.7 18.5 14.8 C 18.6 14.9 18.8 14.8 18.9 14.8 C 19.2 14.9 19.3 15.0 19.5 15.1 C 19.6 15.2 20.0 15.2 20.0 15.3 C 19.8 15.7 19.5 15.7 19.2 15.9 C 18.9 16.1 18.6 16.3 18.4 16.5 C 18.1 16.7 18.0 17.0 17.7 17.2 C 17.6 17.2 17.4 17.3 17.4 17.3 C 17.1 17.6 16.8 17.8 16.4 18.0 C 16.0 18.2 15.6 18.2 15.2 18.4 C 15.0 18.5 14.9 18.6 14.8 18.7 C 14.4 18.9 13.9 19.0 13.5 19.1 C 13.1 19.3 12.7 19.5 12.4 19.6" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\leftarrow': '<path d="M 20.0 16.2 C 19.6 16.2 19.2 16.2 18.8 16.3 C 18.6 16.3 18.4 16.2 18.1 16.3 C 17.8 16.3 17.3 16.4 16.9 16.3 C 16.5 16.2 16.1 16.0 15.7 15.8 C 15.5 15.8 15.2 15.8 15.0 15.8 C 14.4 15.8 13.9 15.8 13.3 15.8 C 11.3 15.8 9.3 15.8 7.3 15.8 M 10.8 11.8 C 9.4 12.1 8.3 12.9 7.2 13.7 C 7.0 13.7 7.0 13.9 6.9 14.0 C 6.7 14.1 6.5 14.2 6.3 14.4 C 6.1 14.5 5.7 14.7 5.5 14.8 C 5.4 14.9 5.2 14.8 5.1 14.8 C 4.8 14.9 4.7 15.0 4.5 15.1 C 4.4 15.2 4.0 15.2 4.0 15.3 C 4.2 15.7 4.5 15.7 4.8 15.9 C 5.1 16.1 5.4 16.3 5.6 16.5 C 5.9 16.7 6.0 17.0 6.3 17.2 C 6.4 17.2 6.6 17.3 6.6 17.3 C 6.9 17.6 7.2 17.8 7.6 18.0 C 8.0 18.2 8.4 18.2 8.8 18.4 C 9.0 18.5 9.1 18.6 9.2 18.7 C 9.6 18.9 10.1 19.0 10.5 19.1 C 10.9 19.3 11.3 19.5 11.6 19.6" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\Rightarrow': '<path d="M 4 14 L 18 14 M 4 18 L 18 18 M 14 10 L 20 16 L 14 22" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\implies': '<path d="M 4 14 L 18 14 M 4 18 L 18 18 M 14 10 L 20 16 L 14 22" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\infty': '<path d="M 7.896 12.315 C 7.543 11.963 6.343 12.188 5.849 12.188 C 5.267 12.188 4.756 12.201 4.186 12.315 C 3.874 12.378 3.466 12.215 3.163 12.315 C 2.689 12.474 2.329 12.86 1.883 13.083 C 1.284 13.383 0.662 13.606 0.348 14.235 C 0.047 14.835 -0.002 15.488 0.22 16.154 C 0.343 16.522 0.29 16.933 0.476 17.305 C 0.62 17.593 0.799 18.042 1.115 18.2 C 1.217 18.251 1.391 18.164 1.499 18.2 C 1.852 18.318 2.163 18.622 2.523 18.712 C 3.434 18.94 1.874 18.325 3.163 18.84 C 3.506 18.977 3.911 19.23 4.314 19.096 C 4.955 18.882 5.437 18.305 5.977 17.945 C 6.608 17.524 7.16 16.994 7.768 16.538 C 8.141 16.257 7.944 16.601 8.28 16.154 C 8.881 15.352 9.439 14.513 10.071 13.723 C 10.393 13.32 10.809 12.999 11.094 12.572 C 11.443 12.048 11.752 11.525 12.118 11.036 C 12.261 10.845 12.486 10.716 12.629 10.524 C 12.748 10.366 12.812 10.113 13.013 10.013 C 14.394 9.323 15.785 9.351 17.107 10.013 C 17.347 10.133 17.321 10.482 17.491 10.652 C 17.558 10.72 17.679 10.713 17.747 10.781 C 17.926 10.96 17.9 11.267 18.13 11.42 C 18.536 11.69 18.7 11.99 19.026 12.315 C 19.17 12.459 19.495 12.585 19.666 12.699 C 19.865 12.832 19.924 13.023 20.05 13.211 C 20.148 13.359 20.335 13.447 20.433 13.595 C 20.83 14.19 21.284 15.078 21.457 15.77 C 21.566 16.205 21.457 16.856 21.457 17.305 C 21.457 17.776 21.607 18.517 21.457 18.968 C 21.354 19.275 21.11 19.359 20.945 19.608 C 20.839 19.766 20.824 19.985 20.689 20.12 C 20.585 20.224 20.088 20.393 19.922 20.503 C 19.732 20.63 19.612 20.913 19.41 21.015 C 19.233 21.104 18.833 20.983 18.642 21.015 C 18.206 21.087 17.799 21.198 17.363 21.271 C 16.356 21.438 15.16 21.242 14.165 21.143 C 13.136 21.04 11.92 20.98 10.966 20.503 C 10.6 20.32 10.143 20.192 9.815 19.863 C 9.465 19.514 9.442 18.857 9.175 18.456 C 8.838 17.951 8.816 17.355 8.536 16.793 C 8.369 16.459 8.149 16.144 8.024 15.77 C 7.985 15.654 8.062 15.501 8.024 15.386 C 7.905 15.029 7.652 14.712 7.512 14.363 C 7.381 14.034 7.24 13.673 7.129 13.339 C 7.093 13.231 7.179 13.056 7.129 12.955 C 7.003 12.704 6.757 12.584 6.617 12.443" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\theta': '<path d="M 12 4 C 6 4, 4 12, 4 16 C 4 20, 6 28, 12 28 C 18 28, 20 20, 20 16 C 20 12, 18 4, 12 4 Z M 4 16 L 20 16" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '\\pi': '<path d="M 4 8 L 20 8 M 8 8 L 8 24 M 16 8 L 16 24 C 16 26, 18 28, 20 28" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        '|': '<path d="M 6.205 2.303 C 6.205 3.419 6.306 4.583 6.205 5.693 C 6.124 6.579 5.855 7.434 5.757 8.316 C 5.686 8.958 5.757 9.652 5.757 10.298 C 5.757 10.779 5.746 11.23 5.693 11.706 C 5.66 12.0 5.735 12.309 5.693 12.601 C 5.668 12.775 5.59 12.939 5.565 13.113 C 5.468 13.79 5.609 14.555 5.693 15.224 C 5.743 15.62 5.627 16.046 5.693 16.439 C 5.778 16.949 6.019 17.503 5.885 18.038 C 5.51 19.536 5.501 21.102 5.501 22.644 C 5.501 23.497 5.501 24.35 5.501 25.203 C 5.501 25.568 5.441 25.994 5.501 26.354 C 5.559 26.699 5.625 27.038 5.693 27.377 C 5.744 27.63 5.693 27.952 5.693 28.209 C 5.693 28.785 5.693 29.36 5.693 29.936" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '\\cdot': '<circle cx="12" cy="16" r="2" fill="#333"/>',
        '(': '<path d="M 9 2 C 7 5, 5 12, 6 18 C 5 24, 6 30, 8 34" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        ')': '<path d="M 3 2 C 5 5, 7 12, 6 18 C 7 24, 6 30, 4 34" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round"/>',
        '[': '<path d="M 8 3 L 5 4 L 4 32 L 8 33" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
        ']': '<path d="M 4 3 L 7 4 L 8 32 L 4 33" stroke="#333" fill="none" stroke-width="1.0" stroke-linecap="round" stroke-linejoin="round"/>',
    }

    if symbol in custom_svg_paths:
        width = 24 * scale
        height = 36 * scale_y
        baseline = 24 * scale_y
        if symbol in ('\\sum', '\\prod'):
            width = 26 * scale
            height = 24 * scale_y
            baseline = 20 * scale_y
        elif symbol == '\\infty':
            width = 22 * scale
            height = 24 * scale_y
            baseline = 22 * scale_y
        elif symbol in ('\\nabla', '\\partial'):
            width = 24 * scale
            height = 24 * scale_y
            baseline = 20 * scale_y
        elif symbol == '\\iint':
            width = 32 * scale
        elif symbol == '\\iiint':
            width = 40 * scale
        elif symbol in ('(', ')', '[', ']', '\\{', '\\}', '|', '\\mid', '\\|'):
            width = 12 * scale
            
        box = BoundingBox(width, height, baseline)
        path_data = custom_svg_paths[symbol]
        if isinstance(path_data, list):
            path_data = random.choice(path_data)
        path_str = re.sub(r'stroke-width="[^"]+"', f'stroke-width="0.6"', path_data)
        svg_content = f'<g transform="scale({scale}, {scale_y})">{path_str}</g>'
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
    svg = f'<text font-family="WaHandwriting-Regular" font-size="{font_size}" fill="#333">{safe_sym}</text>'
    box.elements.append((0, baseline, svg))
    return box

def remove_accents(text: str) -> str:
    accents = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U'}
    for k, v in accents.items():
        text = text.replace(k, v)
    return text

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
        if "text" in node:
            text_val = node["text"]
            from document_parser import parse_inline
            inline_blocks = parse_inline(text_val)
            return layout_inline_blocks(inline_blocks, scale)
        elif "content" in node:
            return layout_ast(node["content"], scale)
            
    elif node_type == "intertext":
        if "text" in node:
            text_val = node["text"]
            # Extract content from \intertext{...}
            import re
            m = re.match(r'\\intertext\s*\{([^}]*)\}', text_val)
            if m:
                text_val = m.group(1)
            from document_parser import parse_inline
            inline_blocks = parse_inline(text_val)
            box = layout_inline_blocks(inline_blocks, scale)
            box.is_intertext = True
            return box
        else:
            return layout_ast(node.get("content"), scale)
        
    elif node_type == "text":
        val = node.get("value") or ""
        # We can just treat it as a sequence of symbols, or a single string
        # Since it's text, we can just render it as a single block
        font_size = 20 * scale
        char_width = font_size * 0.45
        width = len(val) * char_width
        height = font_size * 1.2
        baseline = font_size
        
        box = BoundingBox(width, height, baseline)
        safe_val = remove_accents(val).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        svg = f'<text font-family="WaHandwriting-Regular" font-size="{font_size}" fill="#333">{safe_val}</text>'
        box.elements.append((0, baseline, svg))
        return box
        
    elif node_type == "sequence":
        items = node.get("items", [])
        boxes = [layout_ast(child, scale) for child in items]
        if not boxes:
            return BoundingBox(0, 0, 0)
            
        # Horizontal layout
        default_spacing = 4 * scale
        spacings = []
        
        for i in range(len(boxes) - 1):
            current_item = items[i]
            next_item = items[i+1]
            
            current_spacing = default_spacing
            
            is_unary = False
            if current_item.get("type") == "operator" and current_item.get("value") in ("+", "-"):
                if i == 0:
                    is_unary = True
                else:
                    prev_item = items[i-1]
                    if prev_item.get("type") in ("operator", "relation", "punctuation") or (prev_item.get("type") == "symbol" and prev_item.get("value") in ("\\to", "=", "<", ">", "\\le", "\\ge")):
                        is_unary = True
            
            if is_unary:
                current_spacing = 1 * scale
                
            if next_item.get("type") == "punctuation":
                current_spacing = 1 * scale
                
            spacings.append(current_spacing)
            
        total_width = sum(b.width for b in boxes) + sum(spacings)
        max_baseline = max(b.baseline for b in boxes)
        max_descent = max(b.height - b.baseline for b in boxes)
        
        container = BoundingBox(total_width, max_baseline + max_descent, max_baseline)
        current_x = 0
        for i, b in enumerate(boxes):
            b.x = current_x
            b.y = max_baseline - b.baseline
            container.elements.append(b)
            if i < len(spacings):
                current_x += b.width + spacings[i]
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
        import random
        curve_offset1 = random.uniform(-1.0, 1.0) * scale
        curve_offset2 = random.uniform(-1.0, 1.0) * scale
        mid_x = width / 2
        bar_svg = f'<path d="M 2 {bar_y} Q {mid_x/2} {bar_y + curve_offset1} {mid_x} {bar_y} T {width-2} {bar_y + curve_offset2}" stroke="#333" stroke-width="{0.6*scale}" fill="none" stroke-linecap="round"/>'
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
                int_sym.y = upper.height - 2 * scale
            else:
                int_sym.y = 0
                
            if lower:
                lower.x = (int_sym.width - lower.width) / 2
                lower.y = int_sym.y + int_sym.height - 2 * scale
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
            layout_rows.append(layout_row)
            
            is_intertext_row = len(layout_row) == 1 and getattr(layout_row[0], 'is_intertext', False)
            if not is_intertext_row:
                for i, cell_box in enumerate(layout_row):
                    if i >= len(col_widths):
                        col_widths.append(cell_box.width)
                    else:
                        col_widths[i] = max(col_widths[i], cell_box.width)
            
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
            
            is_intertext_row = len(layout_row) == 1 and getattr(layout_row[0], 'is_intertext', False)
            
            if is_intertext_row:
                cell = layout_row[0]
                cell.x = 0
                cell.y = current_y + (row_baseline - cell.baseline)
                container_elements.append(cell)
                max_width = max(max_width, cell.width)
            else:
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
            lparen = get_symbol_box("(", scale, delim_scale)
            rparen = get_symbol_box(")", scale, delim_scale)
        elif node.get("style") == "brackets":
            lparen = get_symbol_box("[", scale, delim_scale)
            rparen = get_symbol_box("]", scale, delim_scale)
        elif node.get("style") == "pipes":
            lparen = get_symbol_box("|", scale, delim_scale)
            rparen = get_symbol_box("|", scale, delim_scale)
        elif node.get("style") == "left_right":
            left_delim = node.get("left_delim")
            right_delim = node.get("right_delim")
            
            if left_delim != '.':
                lparen = get_symbol_box(left_delim, scale, delim_scale)
            else:
                lparen = BoundingBox(0, 0, 0)
                
            if right_delim != '.':
                rparen = get_symbol_box(right_delim, scale, delim_scale)
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
        sym = get_symbol_box(sym_val, scale * 1.5)
        
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
            sym.y = upper.height - 2 * scale
        else:
            sym.y = 0
            
        sym.x = max(0, (upper.width / 2 - sym_center) if upper else 0, (lower.width / 2 - sym_center) if lower else 0)
        if upper: upper.x += sym.x
        
        if lower:
            lower.x = sym.x + sym_center - lower.width / 2
            lower.y = sym.y + sym.height - 2 * scale
            
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
        
    elif node_type == "vspace":
        # Parse the amount, e.g., "1em", "10pt"
        amount_str = ""
        amount_node = node.get("amount")
        if amount_node:
            if amount_node.get("type") == "sequence":
                for item in amount_node.get("items", []):
                    if item.get("type") == "variable":
                        amount_str += item.get("name", "")
                    elif item.get("type") == "number":
                        amount_str += item.get("value", "")
                    elif item.get("type") == "text_mode":
                        amount_str += item.get("text", "")
                    elif item.get("type") == "text":
                        amount_str += item.get("value", "")
            elif amount_node.get("type") == "variable":
                amount_str = amount_node.get("name", "")
            elif amount_node.get("type") == "number":
                amount_str = amount_node.get("value", "")
            elif amount_node.get("type") == "text_mode":
                amount_str = amount_node.get("text", "")
            elif amount_node.get("type") == "text":
                amount_str = amount_node.get("value", "")
                
        # Heuristic conversion
        height = 10 * scale
        if "pt" in amount_str:
            try:
                height = float(amount_str.replace("pt", "")) * scale
            except: pass
        elif "em" in amount_str:
            try:
                height = float(amount_str.replace("em", "")) * 24 * scale
            except: pass
        elif "cm" in amount_str:
            try:
                height = float(amount_str.replace("cm", "")) * 28 * scale
            except: pass
            
        return BoundingBox(0, height, height)
        
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
            cond.y = sym.height - 4 * scale
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
        svg = f'<path d="{path}" stroke="#333" stroke-width="{0.6*scale}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
        container.elements.append((0, 0, svg))
        
        return container

    elif node_type == "accent":
        name = node.get("name")
        body_node = node.get("body")
        
        if name in ("\\mathbb", "\\mathcal"):
            inner = body_node
            if body_node and body_node.get("type") == "group":
                inner = body_node.get("content")
            
            if inner and inner.get("type") == "variable":
                val = inner.get("name")
                bb_map = {'R': 'ℝ', 'Z': 'ℤ', 'N': 'ℕ', 'Q': 'ℚ', 'C': 'ℂ', 'P': 'ℙ', 'E': '𝔼'}
                cal_map = {'L': 'ℒ', 'F': 'ℱ', 'O': '𝒪', 'P': '𝒫', 'S': '𝒮', 'M': 'ℳ', 'C': '𝒞', 'D': '𝒟'}
                if name == "\\mathbb" and val in bb_map:
                    return get_symbol_box(bb_map[val], scale)
                elif name == "\\mathcal" and val in cal_map:
                    return get_symbol_box(cal_map[val], scale)
                else:
                    return get_symbol_box(val, scale)
            # Fallback
            return layout_ast(body_node, scale)
            
        body = layout_ast(body_node, scale)
        
        accent_char = ""
        if name == "\\vec": accent_char = "→"
        elif name == "\\hat": accent_char = "^"
        elif name == "\\dot": accent_char = "˙"
        elif name == "\\ddot": accent_char = "¨"
        elif name == "\\mathbf":
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

def create_word_box(word: str, font_size: float, scale: float) -> BoundingBox:
    char_width = font_size * 0.45
    parts = re.split(r'([()\[\]{}])', word)
    
    total_width = 0
    max_baseline = font_size
    max_descent = font_size * 0.3
    
    elements = []
    
    for part in parts:
        if not part: continue
        if part in '()[]{}':
            box = get_symbol_box(part, scale * 0.8)
            elements.append((box, total_width))
            total_width += box.width
            max_baseline = max(max_baseline, box.baseline)
            max_descent = max(max_descent, box.height - box.baseline)
        else:
            width = len(part) * char_width
            box = BoundingBox(width, font_size * 1.2, font_size)
            safe_val = remove_accents(part).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            svg = f'<text font-family="WaHandwriting-Regular" font-size="{font_size}" fill="#333">{safe_val}</text>'
            box.elements.append((0, font_size, svg))
            elements.append((box, total_width))
            total_width += width
            
    container = BoundingBox(total_width, max_baseline + max_descent, max_baseline)
    for box, x in elements:
        box.x = x
        box.y = max_baseline - box.baseline
        container.elements.append(box)
        
    return container

def layout_inline_blocks(content: list, scale: float) -> BoundingBox:
    font_size = 20 * scale
    char_width = font_size * 0.45  # Better estimate for text width
    
    container = BoundingBox(0, 0, 0)
    current_x = 0
    max_baseline = font_size
    max_descent = font_size * 0.3
    
    for item in content:
        if item["type"] == "text":
            val = item["value"]
            box = create_word_box(val, font_size, scale)
            box.x = current_x
            box.y = 0
            container.elements.append(box)
            current_x += box.width
            max_baseline = max(max_baseline, box.baseline)
            max_descent = max(max_descent, box.height - box.baseline)
            
        elif item["type"] == "inline_math":
            box = layout_ast(item["ast"], scale * 0.9)
            box.x = current_x
            container.elements.append(box)
            current_x += box.width
            max_baseline = max(max_baseline, box.baseline)
            max_descent = max(max_descent, box.height - box.baseline)
            
    container.width = current_x
    container.height = max_baseline + max_descent
    container.baseline = max_baseline
    
    # Adjust y positions based on final max_baseline
    for el in container.elements:
        if hasattr(el, 'baseline'):
            el.y = max_baseline - el.baseline
            
    return container

def layout_paragraph(content: list, max_width: float, scale: float) -> BoundingBox:
    font_size = 20 * scale
    char_width = font_size * 0.45
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
                
                # If a single word is wider than the max_width, we must split it
                if word_width > max_width:
                    chars_per_line = max(1, int(max_width / char_width))
                    for i in range(0, len(word), chars_per_line):
                        chunk = word[i:i+chars_per_line]
                        chunk_width = len(chunk) * char_width
                        if current_x + chunk_width > max_width and current_x > 0:
                            flush_line()
                        box = create_word_box(chunk, font_size, scale)
                        box.x = current_x
                        line_elements.append(box)
                        current_x += box.width
                    current_x += char_width # space after the whole word
                    continue

                if current_x + word_width > max_width and current_x > 0:
                    flush_line()
                
                box = create_word_box(word, font_size, scale)
                box.x = current_x
                line_elements.append(box)
                current_x += box.width + char_width
                
        elif item["type"] == "inline_math":
            box = layout_ast(item["ast"], scale * 0.9)
            if box.width > max_width:
                # Scale it down to fit
                scale_factor = max_width / box.width
                box = layout_ast(item["ast"], scale * 0.9 * scale_factor)
                
            if current_x + box.width > max_width and current_x > 0:
                flush_line()
            box.x = current_x
            line_elements.append(box)
            current_x += box.width + char_width
            max_baseline = max(max_baseline, box.baseline)
            max_descent = max(max_descent, box.height - box.baseline)
            
        elif item["type"] == "vspace":
            flush_line()
            box = layout_ast(item, scale)
            current_y += box.height
            
    flush_line()
    container.height = current_y
    return container

def layout_document(doc_ast: list, max_width: float = 800, scale: float = 1.0) -> list:
    PAGE_WIDTH = 800
    PAGE_HEIGHT = 1130
    MARGIN_TOP = 40
    MARGIN_BOTTOM = 40
    MARGIN_LEFT = 100
    MARGIN_RIGHT = 40
    USABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
    USABLE_HEIGHT = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM
    
    pages = []
    current_page_elements = []
    current_y = 0
    
    def finish_page():
        nonlocal current_page_elements, current_y, pages
        page_box = BoundingBox(PAGE_WIDTH, PAGE_HEIGHT, 0)
        page_box.is_page = True
        for el in current_page_elements:
            page_box.elements.append(el)
        pages.append(page_box)
        current_page_elements = []
        current_y = 0

    for block in doc_ast:
        if block["type"] == "newpage":
            finish_page()
            continue
        elif block["type"] == "vspace":
            box = layout_ast(block, scale)
            spacing = 0
        elif block["type"] == "paragraph":
            box = layout_paragraph(block["content"], USABLE_WIDTH, scale)
            spacing = 20 * scale
        elif block["type"] == "display_math":
            box = layout_ast(block["ast"], scale * 1.2)
            if box.width > USABLE_WIDTH:
                scale_factor = USABLE_WIDTH / box.width
                box = layout_ast(block["ast"], scale * 1.2 * scale_factor)
            box.x = (USABLE_WIDTH - box.width) / 2
            if box.x < 0: box.x = 0
            spacing = 30 * scale
        elif block["type"] == "header":
            box = layout_paragraph(block["content"], USABLE_WIDTH, scale * 1.2)
            spacing = 20 * scale
        else:
            continue
            
        if current_y + box.height > USABLE_HEIGHT and current_y > 0:
            finish_page()
            
        box.y = current_y + MARGIN_TOP
        box.x += MARGIN_LEFT
        current_page_elements.append(box)
        current_y += box.height + spacing
        
    if current_page_elements or not pages:
        finish_page()
        
    return pages
