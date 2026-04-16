import re
from latex_parser import parse_latex_math

def parse_inline(text: str):
    """Parses a line of text containing inline math \\( ... \\) or $ ... $ and bold text \\textbf{...}"""
    parts = []
    # Clean up \displaystyle as it's a layout hint we handle automatically
    text = text.replace(r'\displaystyle', '')
    
    # Also handle \item
    text = text.replace(r'\item', '• ')
    
    # Match \( ... \) or $ ... $ or \textbf{...} or \verb|...| or \text{...} or \intertext{...} or \vspace{...}
    pattern = r'\\\((.*?)\\\)|\$([^$]+)\$|\\textbf\{(.*?)\}|\\verb\|(.*?)\||\\(?:text|textit|mathrm|intertext)\{(.*?)\}|\\vspace\*?\{(.*?)\}'
    last_idx = 0
    for m in re.finditer(pattern, text, re.DOTALL):
        if m.start() > last_idx:
            parts.append({"type": "text", "value": text[last_idx:m.start()]})
            
        if m.group(1) is not None:
            try:
                parts.append({"type": "inline_math", "ast": parse_latex_math(m.group(1).strip())})
            except Exception as e:
                parts.append({"type": "text", "value": f"\\({m.group(1)}\\)"})
        elif m.group(2) is not None:
            try:
                parts.append({"type": "inline_math", "ast": parse_latex_math(m.group(2).strip())})
            except Exception as e:
                parts.append({"type": "text", "value": f"${m.group(2)}$"})
        elif m.group(3) is not None:
            parts.append({"type": "text", "value": m.group(3), "bold": True})
        elif m.group(4) is not None:
            parts.append({"type": "text", "value": m.group(4), "bold": False})
        elif m.group(5) is not None:
            parts.append({"type": "text", "value": m.group(5), "bold": False})
        elif m.group(6) is not None:
            try:
                parts.append({"type": "vspace", "amount": parse_latex_math(m.group(6))})
            except:
                parts.append({"type": "vspace", "amount": {"type": "text_mode", "text": m.group(6)}})
            
        last_idx = m.end()
        
    if last_idx < len(text):
        parts.append({"type": "text", "value": text[last_idx:]})
        
    return parts

def parse_document(text: str):
    """Parses a full academic document with paragraphs, headers, and display math."""
    blocks = []
    
    # 1. Extract display math \[ ... \] to protect it from paragraph splitting
    display_math_pattern = r'\\\[(.*?)\\\]'
    placeholders = {}
    counter = 0
    
    def repl(m):
        nonlocal counter
        key = f"__DISPLAY_MATH_{counter}__"
        placeholders[key] = m.group(1).strip()
        counter += 1
        return f"\n\n{key}\n\n"
        
    text = re.sub(display_math_pattern, repl, text, flags=re.DOTALL)
    
    # Also extract $$ ... $$
    display_math_pattern2 = r'\$\$(.*?)\$\$'
    def repl2(m):
        nonlocal counter
        key = f"__DISPLAY_MATH_{counter}__"
        placeholders[key] = m.group(1).strip()
        counter += 1
        return f"\n\n{key}\n\n"
        
    text = re.sub(display_math_pattern2, repl2, text, flags=re.DOTALL)
    
    # Extract \begin{align*} ... \end{align*}
    align_pattern = r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}'
    def repl3(m):
        nonlocal counter
        key = f"__DISPLAY_MATH_{counter}__"
        # We need to parse the align environment itself, so we wrap it back
        placeholders[key] = f"\\begin{{align*}}{m.group(1)}\\end{{align*}}"
        counter += 1
        return f"\n\n{key}\n\n"
        
    text = re.sub(align_pattern, repl3, text, flags=re.DOTALL)
    
    # Extract \newpage and \newage
    newpage_pattern = r'\\new(p)?age'
    def repl_newpage(m):
        nonlocal counter
        key = f"__NEWPAGE_{counter}__"
        placeholders[key] = "newpage"
        counter += 1
        return f"\n\n{key}\n\n"
        
    text = re.sub(newpage_pattern, repl_newpage, text)
    
    # Clean up itemize environments in text
    text = text.replace(r'\begin{itemize}', '')
    text = text.replace(r'\end{itemize}', '')
    
    # Strip comments
    text = re.sub(r'%.*', '', text)
    
    # Strip preamble commands without arguments
    preamble_commands = [
        r'\\documentclass\[.*?\]\{.*?\}',
        r'\\documentclass\{.*?\}',
        r'\\usepackage\[.*?\]\{.*?\}',
        r'\\usepackage\{.*?\}',
        r'\\begin\{document\}',
        r'\\end\{document\}',
        r'\\maketitle',
        r'\\tableofcontents'
    ]
    for cmd in preamble_commands:
        text = re.sub(cmd, '', text, flags=re.DOTALL)
        
    # Strip commands with arguments that might have nested braces
    for cmd in ['\\title', '\\author', '\\date']:
        while cmd in text:
            start_idx = text.find(cmd)
            brace_idx = text.find('{', start_idx)
            if brace_idx == -1:
                text = text.replace(cmd, '', 1)
                continue
            
            brace_count = 1
            end_idx = brace_idx + 1
            while end_idx < len(text) and brace_count > 0:
                if text[end_idx] == '{':
                    brace_count += 1
                elif text[end_idx] == '}':
                    brace_count -= 1
                end_idx += 1
                
            if brace_count == 0:
                text = text[:start_idx] + text[end_idx:]
            else:
                text = text.replace(cmd, '', 1)
    
    # 2. Split into paragraphs
    raw_paragraphs = re.split(r'\n\s*\n', text.strip())
    
    for para in raw_paragraphs:
        para = para.strip()
        if not para: continue
        
        # Restore display math and newpage
        if para in placeholders:
            if placeholders[para] == "newpage":
                blocks.append({"type": "newpage"})
            else:
                try:
                    blocks.append({
                        "type": "display_math", 
                        "ast": parse_latex_math(placeholders[para])
                    })
                except Exception as e:
                    val = placeholders[para]
                    if val.startswith("\\begin"):
                        blocks.append({"type": "paragraph", "content": [{"type": "text", "value": val}]})
                    else:
                        blocks.append({"type": "paragraph", "content": [{"type": "text", "value": f"\\[{val}\\]"}]})
            continue
            
        # Check for headers like \subsection*{...}
        m = re.match(r'\\(sub)?section\*?\{(.*)\}', para, re.DOTALL)
        if m:
            level = 2 if m.group(1) else 1
            content = parse_inline(m.group(2))
            blocks.append({"type": "header", "level": level, "content": content})
            continue
            
        # Check for vspace
        m = re.match(r'\\vspace\*?\{(.*)\}', para, re.DOTALL)
        if m:
            try:
                blocks.append({"type": "vspace", "amount": parse_latex_math(m.group(1))})
            except:
                blocks.append({"type": "vspace", "amount": {"type": "text_mode", "text": m.group(1)}})
            continue
            
        # Standard paragraph
        blocks.append({"type": "paragraph", "content": parse_inline(para)})
        
    return blocks
