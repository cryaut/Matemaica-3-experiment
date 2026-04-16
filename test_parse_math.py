from latex_parser import parse_latex_math
import json

text = r"""\begin{align*}
\lim_{n\to\infty} \left| \frac{a_{n+1}}{a_n} \right| &= \lim_{n\to\infty} \left| \frac{x^{2(n+1)-1}}{2(n+1)-1} \cdot \frac{2n-1}{x^{2n-1}} \right| \\
&= \lim_{n\to\infty} |x|^2 \cdot \frac{2n-1}{2n+1} = |x|^2 \cdot \lim_{n\to\infty} \frac{2n-1}{2n+1} = |x|^2.
\end{align*}"""

ast = parse_latex_math(text)
print(json.dumps(ast, indent=2))
