from backend import render_expression
from latex_parser import parse_latex_math
from layout_engine import layout_ast, set_custom_symbols


def test_custom_symbol_uses_tight_metrics():
    set_custom_symbols([
        {
            "latex": "\\alpha",
            "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 28" width="8" height="28"><path d="M 4 2 L 4 26" stroke="#111827" stroke-width="3" fill="none"/></svg>',
            "width": 8,
            "height": 28,
            "baseline": 22,
        }
    ])

    custom_box = layout_ast(parse_latex_math(r"\alpha x"))
    set_custom_symbols([])
    fallback_box = layout_ast(parse_latex_math(r"\alpha x"))

    assert custom_box.width < fallback_box.width
    assert custom_box.width < 25
    assert custom_box.baseline == 22


def test_math_environments_render_without_errors():
    samples = [
        r"\begin{cases} x^2 & x>0 \\ 0 & x=0 \end{cases}",
        r"\begin{pmatrix} a & b \\ c & d \end{pmatrix}",
        r"\begin{bmatrix} a & b \\ c & d \end{bmatrix}",
        r"\begin{array}{cc} a & b \\ c & d \end{array}",
        r"\begin{align*} a &= b \\ c &= d \end{align*}",
        r"\forall x \in \mathbb{R}, x \neq \emptyset \Rightarrow x \geq 0",
    ]

    for sample in samples:
        result = render_expression(sample, "LaTeX", "Medium", 1, "SVG")
        assert result["status"] == "ok", sample
        assert result["svg_pages"]
        assert result["svg_content"].startswith("<svg")


def test_document_lists_and_tabular_render_without_errors():
    document = r"""
    \section{Checklist}
    \begin{itemize}
    \item first item with \( \alpha + \beta \)
    \item second item
    \end{itemize}

    \begin{enumerate}
    \item one
    \item two
    \end{enumerate}

    \begin{tabular}{cc}
    a & b \\
    c & d
    \end{tabular}
    """

    result = render_expression(document, "LaTeX", "Medium", 1, "SVG")
    assert result["status"] == "ok"
    assert result["svg_pages"]
