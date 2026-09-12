import json
from document_parser import parse_document

latex = r"""
\begin{document}
Test start.
\begin{align*}
a^2 + b^2 = c^2
\end{align*}
Test end.
\end{document}
"""

try:
    blocks = parse_document(latex)
    print("Blocks parsed successfully")
    for b in blocks:
        print(f"Type: {b['type']}")
except Exception as e:
    print(f"Error: {e}")
