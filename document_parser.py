import re
from latex_parser import parse_latex_math, SYMBOL_COMMANDS

def parse_inline(text: str, bold: bool = False, italic: bool = False):
    """Parses a line of text containing inline math \\( ... \\) or $ ... $ and bold text \\textbf{...}"""
    parts = []
    # Clean up \displaystyle as it's a layout hint we handle automatically
    text = text.replace(r'\displaystyle', '')
    
    last_idx = 0
    i = 0
    while i < len(text):
        # Check for \(
        if text.startswith('\\(', i):
            if i > last_idx:
                parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
            
            start_idx = i + 2
            brace_count = 1
            j = start_idx
            while j < len(text) - 1:
                if text.startswith('\\(', j):
                    brace_count += 1
                    j += 2
                elif text.startswith('\\)', j):
                    brace_count -= 1
                    if brace_count == 0:
                        break
                    j += 2
                else:
                    j += 1
            
            if j < len(text) - 1 and text.startswith('\\)', j):
                content = text[start_idx:j]
                try:
                    parts.append({"type": "inline_math", "ast": parse_latex_math(content.strip()), "bold": bold})
                except Exception:
                    parts.append({"type": "text", "value": "\\({}\\)".format(content), "bold": bold, "italic": italic})
                i = j + 2
                last_idx = i
                continue
            else:
                parts.append({"type": "text", "value": "\\(", "bold": bold, "italic": italic})
                i += 2
                last_idx = i
                continue
        
        # Check for $
        elif text[i] == '$' and (i == 0 or text[i-1] != '\\'):
            if i > last_idx:
                parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
            
            start_idx = i + 1
            j = start_idx
            while j < len(text):
                if text[j] == '$' and text[j-1] != '\\':
                    break
                j += 1
            
            if j < len(text) and text[j] == '$':
                content = text[start_idx:j]
                try:
                    parts.append({"type": "inline_math", "ast": parse_latex_math(content.strip()), "bold": bold})
                except Exception:
                    parts.append({"type": "text", "value": f"${content}$", "bold": bold, "italic": italic})
                i = j + 1
                last_idx = i
                continue
            else:
                parts.append({"type": "text", "value": "$", "bold": bold, "italic": italic})
                i += 1
                last_idx = i
                continue
        
        # Check for formatting or spacing commands
        m = re.match(r'\\(textbf|textit|mathrm|text|intertext|large|small|normalsize|verb|centering|quad|qquad)\s*([{|])?', text[i:])
        if not m:
            # Check for naked math commands like \mu, \alpha, \Rightarrow, etc.
            m = re.match(r'\\[a-zA-Z]+', text[i:])
            if m and m.group(0) in SYMBOL_COMMANDS:
                if i > last_idx:
                    parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
                
                cmd = m.group(0)[1:]
                if cmd in ('quad', 'qquad'):
                    parts.append({"type": "text", "value": "    " if cmd == 'quad' else "        "})
                else:
                    try:
                        parts.append({"type": "inline_math", "ast": parse_latex_math(m.group(0)), "bold": bold})
                    except:
                        parts.append({"type": "text", "value": m.group(0)})
                
                i += m.end()
                last_idx = i
                continue
                
            # Also check for formatting with trailing space which was already there
            m = re.match(r'\\(large|small|normalsize|centering|Large|LARGE|huge|HUGE|tiny|scriptsize|footnotesize)\s+', text[i:])
            if m:
                if i > last_idx:
                    parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
                i += m.end()
                last_idx = i
                continue
                
            # Handle naked groups { ... }
            if text[i] == '{' and (i == 0 or text[i-1] != '\\'):
                if i > last_idx:
                    parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
                
                start_content_idx = i + 1
                brace_count = 1
                j = start_content_idx
                while j < len(text) and brace_count > 0:
                    if text[j] == '{' and text[max(0, j-1)] != '\\':
                        brace_count += 1
                    elif text[j] == '}' and text[max(0, j-1)] != '\\':
                        brace_count -= 1
                    if brace_count > 0: j += 1
                
                if j < len(text) and brace_count == 0:
                    content = text[start_content_idx:j]
                    parts.extend(parse_inline(content, bold=bold, italic=italic))
                    i = j + 1
                    last_idx = i
                    continue

        if m and m.group(0).startswith('\\'):
            cmd = m.group(1)
            start_char = m.group(2)
            end_char = '}' if start_char == '{' else '|'
            
            if i > last_idx:
                parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
            
            start_content_idx = i + m.end()
            brace_count = 1 if start_char == '{' else 0
            j = start_content_idx
            
            if start_char == '{':
                while j < len(text) and brace_count > 0:
                    if text[j] == '{' and text[max(0, j-1)] != '\\':
                        brace_count += 1
                    elif text[j] == '}' and text[max(0, j-1)] != '\\':
                        brace_count -= 1
                    if brace_count > 0: j += 1
            else:
                while j < len(text) and text[j] != end_char:
                    j += 1
            
            if j < len(text) and (brace_count == 0 if start_char == '{' else text[j] == end_char):
                content = text[start_content_idx:j]
                new_bold = bold or (cmd == 'textbf')
                new_italic = italic or (cmd == 'textit')
                
                if cmd == 'verb':
                    parts.append({"type": "text", "value": content, "bold": False, "italic": False, "font": "monospace"})
                else:
                    parts.extend(parse_inline(content, bold=new_bold, italic=new_italic))
                
                i = j + 1
                last_idx = i
                continue

        # Check for \vspace
        m = re.match(r'\\vspace\*?\{(.*?)\}', text[i:])
        if m:
            if i > last_idx:
                parts.append({"type": "text", "value": text[last_idx:i], "bold": bold, "italic": italic})
            try:
                parts.append({"type": "vspace", "amount": parse_latex_math(m.group(1))})
            except:
                parts.append({"type": "vspace", "amount": {"type": "text_mode", "text": m.group(1)}})
            i += m.end()
            last_idx = i
            continue

        i += 1
        
    if last_idx < len(text):
        parts.append({"type": "text", "value": text[last_idx:], "bold": bold, "italic": italic})
        
    return parts

def parse_document(text: str):
    """Parses a full academic document with paragraphs, headers, and display math."""
    blocks = []
    
    # Strip comments and preamble first so tree building only processes active document body
    text = re.sub(r'%.*', '', text)
    doc_start = text.find(r'\begin{document}')
    if doc_start != -1:
        text = text[doc_start + len(r'\begin{document}'):]
    
    # End of document
    doc_end = text.find(r'\end{document}')
    if doc_end != -1:
        text = text[:doc_end]

    # Common commands to strip (standalone ones)
    for cmd in [r'\\documentclass(\[.*?\])?\{.*?\}', r'\\usepackage(\[.*?\])?\{.*?\}',
                r'\\maketitle', r'\\tableofcontents', r'\\geometry\{.*?\}',
                r'\\centering']:
        text = re.sub(cmd, '', text)

    # 1. Extract protected blocks: display math, align, environments, newpage
    placeholders = {}
    counter = 0
    
    def add_placeholder(val, type_hint="math"):
        nonlocal counter
        key = f"__BLOCK_{counter}__"
        placeholders[key] = (val, type_hint)
        counter += 1
        return f"\n\n{key}\n\n"

    # Replace newpage early as a standalone command
    text = re.sub(r'\\new(p)?age', lambda m: add_placeholder("newpage", "newpage"), text)

    # Find all open/close math markers and environments sequentially to build a nesting tree
    pattern = re.compile(
        r'\\begin\s*\{\s*([a-zA-Z]+\*?)\s*\}|'
        r'\\end\s*\{\s*([a-zA-Z]+\*?)\s*\}|'
        r'\\\[|'
        r'\\\]|'
        r'\$\$'
    )
    
    tokens = []
    for m in pattern.finditer(text):
        pos = m.start()
        end_pos = m.end()
        if m.group(1):
            tokens.append({"type": "begin", "name": m.group(1).strip(), "pos": pos, "end_pos": end_pos})
        elif m.group(2):
            tokens.append({"type": "end", "name": m.group(2).strip(), "pos": pos, "end_pos": end_pos})
        elif m.group(0) == '\\[':
            tokens.append({"type": "begin_bracket", "pos": pos, "end_pos": end_pos})
        elif m.group(0) == '\\]':
            tokens.append({"type": "end_bracket", "pos": pos, "end_pos": end_pos})
        elif m.group(0) == '$$':
            tokens.append({"type": "dollar_dollar", "pos": pos, "end_pos": end_pos})
            
    root_nodes = []
    stack = []
    
    for tok in tokens:
        if tok["type"] == "begin":
            node = {
                "type": "env",
                "name": tok["name"],
                "start_tok": tok,
                "end_tok": None,
                "children": []
            }
            if stack:
                stack[-1]["children"].append(node)
            else:
                root_nodes.append(node)
            stack.append(node)
            
        elif tok["type"] == "begin_bracket":
            node = {
                "type": "math_bracket",
                "start_tok": tok,
                "end_tok": None,
                "children": []
            }
            if stack:
                stack[-1]["children"].append(node)
            else:
                root_nodes.append(node)
            stack.append(node)
            
        elif tok["type"] == "dollar_dollar":
            if stack and stack[-1]["type"] == "math_dollar":
                closed = stack.pop()
                closed["end_tok"] = tok
            else:
                node = {
                    "type": "math_dollar",
                    "start_tok": tok,
                    "end_tok": None,
                    "children": []
                }
                if stack:
                    stack[-1]["children"].append(node)
                else:
                    root_nodes.append(node)
                stack.append(node)
                
        elif tok["type"] == "end":
            match_idx = -1
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx]["type"] == "env" and stack[idx]["name"] == tok["name"]:
                    match_idx = idx
                    break
            
            if match_idx != -1:
                while len(stack) > match_idx:
                    closed = stack.pop()
                    if len(stack) == match_idx:
                        closed["end_tok"] = tok
                        
        elif tok["type"] == "end_bracket":
            match_idx = -1
            for idx in range(len(stack) - 1, -1, -1):
                if stack[idx]["type"] == "math_bracket":
                    match_idx = idx
                    break
            
            if match_idx != -1:
                while len(stack) > match_idx:
                    closed = stack.pop()
                    if len(stack) == match_idx:
                        closed["end_tok"] = tok

    # Recursively replace nested blocks with placeholders
    def replace_subnodes_with_placeholders(sub_text, nodes, offset=0):
        chunks = []
        last_idx = 0
        
        for node in nodes:
            if not node["end_tok"]:
                continue
                
            start_pos_in_text = node["start_tok"]["pos"] - offset
            end_pos_in_text = node["end_tok"]["end_pos"] - offset
            
            if start_pos_in_text > last_idx:
                chunks.append(sub_text[last_idx:start_pos_in_text])
                
            inner_start = node["start_tok"]["end_pos"] - offset
            inner_end = node["end_tok"]["pos"] - offset
            inner_text = sub_text[inner_start:inner_end]
            
            resolved_inner = replace_subnodes_with_placeholders(
                inner_text, 
                node["children"], 
                offset + inner_start
            )
            
            val = resolved_inner.strip()
            hint = "math"
            
            if node["type"] == "env":
                name = node["name"]
                if name in ('align', 'align*', 'alignat', 'alignat*', 'flalign', 'flalign*', 'gather', 'gather*', 'gathered', 'equation', 'equation*', 'multline', 'multline*', 'aligned', 'alignedat', 'split', 'math', 'cases', 'dcases', 'rcases', 'matrix', 'pmatrix', 'bmatrix', 'Bmatrix', 'vmatrix', 'Vmatrix', 'smallmatrix', 'array', 'tabular', 'tabular*'):
                    val = f"\\begin{{{name}}}{resolved_inner}\\end{{{name}}}"
                    hint = name
                elif name == 'center':
                    hint = "center"
                elif name in ('itemize', 'enumerate', 'description'):
                    hint = name
                else:
                    val = f"\\begin{{{name}}}{resolved_inner}\\end{{{name}}}"
                    hint = name
            elif node["type"] in ("math_bracket", "math_dollar"):
                hint = "math"
                
            placeholder_key = add_placeholder(val, hint)
            chunks.append(placeholder_key)
            
            last_idx = end_pos_in_text
            
        if last_idx < len(sub_text):
            chunks.append(sub_text[last_idx:])
            
        return "".join(chunks)

    text = replace_subnodes_with_placeholders(text, root_nodes, 0)

    # 2. Split into paragraphs
    raw_paragraphs = re.split(r'\n\s*\n', text.strip())
    
    def resolve_placeholders_in_text(text_val, placeholders_dict, bullet=None):
        """Resolves placeholders inside a string and returns a list of blocks."""
        if "__BLOCK_" not in text_val:
            content = parse_inline(text_val)
            if bullet:
                content = [{"type": "text", "value": bullet}] + content
            return [{"type": "paragraph", "content": content}]
        
        # Split by placeholders
        parts = re.split(r'(__BLOCK_\d+__)', text_val)
        res_blocks = []
        first_text_para = True
        
        for p in parts:
            if not p: continue
            if p in placeholders_dict:
                val, hint = placeholders_dict[p]
                if hint == "newpage":
                    res_blocks.append({"type": "newpage"})
                elif hint in ("itemize", "enumerate", "description"):
                    # Recursive item handling
                    items_text = re.split(r'\\item', val)
                    item_count = 0
                    for item in items_text:
                        item = item.strip()
                        if not item: continue
                        item_count += 1
                        if hint == "itemize":
                            sub_bullet = "• "
                        elif hint == "description":
                            label_match = re.match(r'\[([^\]]+)\]\s*(.*)', item, flags=re.DOTALL)
                            if label_match:
                                label, item = label_match.group(1), label_match.group(2)
                                sub_bullet = f"{label}: "
                            else:
                                sub_bullet = "- "
                        else:
                            sub_bullet = f"{item_count}. "
                        res_blocks.extend(resolve_placeholders_in_text(item, placeholders_dict, sub_bullet))
                elif hint == "center":
                    res_blocks.append({"type": "paragraph", "alignment": "center", "content": parse_inline(val)})
                else:
                    # Math block
                    # Need to resolve any placeholders inside the math content before parsing
                    resolved_val = val
                    if "__BLOCK_" in resolved_val:
                        # Simple replacement to restore LaTeX for the math parser
                        for key, (sub_val, sub_hint) in placeholders_dict.items():
                            if key in resolved_val:
                                resolved_val = resolved_val.replace(key, sub_val)
                    
                    try:
                        res_blocks.append({"type": "display_math", "ast": parse_latex_math(resolved_val)})
                    except Exception:
                        res_blocks.append({"type": "paragraph", "content": [{"type": "text", "value": resolved_val}]})
            else:
                # Text segment
                seg_content = parse_inline(p)
                if first_text_para and bullet:
                    seg_content = [{"type": "text", "value": bullet}] + seg_content
                    first_text_para = False
                
                if seg_content:
                    res_blocks.append({"type": "paragraph", "content": seg_content})
        
        # If we had a bullet but no text segments (only blocks), we should probably 
        # have attached the bullet to something. But usually there's text.
        return res_blocks

    for para in raw_paragraphs:
        para = para.strip()
        if not para: continue
        
        # Check for headers or paragraphs with titles
        if any(para.startswith(h) for h in ['\\section', '\\subsection', '\\subsubsection', '\\paragraph']):
            # Robust extraction of the first braced argument
            cmd_match = re.match(r'\\(sub)*section\*?|\\paragraph\*?', para)
            if cmd_match:
                cmd = cmd_match.group(0)
                brace_idx = para.find('{')
                if brace_idx != -1:
                    brace_count = 1
                    j = brace_idx + 1
                    while j < len(para) and brace_count > 0:
                        if para[j] == '{' and (j == 0 or para[j-1] != '\\'): brace_count += 1
                        elif para[j] == '}' and (j == 0 or para[j-1] != '\\'): brace_count -= 1
                        j += 1
                    
                    if brace_count == 0:
                        title_content = para[brace_idx+1:j-1]
                        body_content = para[j:].strip()
                        
                        if cmd.startswith('\\paragraph'):
                            content = parse_inline(title_content, bold=False)
                            if body_content:
                                content.append({"type": "text", "value": " "})
                                content.extend(parse_inline(body_content))
                            blocks.append({"type": "paragraph", "content": content})
                            continue
                        else:
                            if 'subsubsection' in cmd: level = 3
                            elif 'subsection' in cmd: level = 2
                            else: level = 1
                            blocks.append({"type": "header", "level": level, "content": parse_inline(title_content)})
                            if body_content:
                                blocks.extend(resolve_placeholders_in_text(body_content, placeholders))
                            continue

        blocks.extend(resolve_placeholders_in_text(para, placeholders))
        
    return blocks
