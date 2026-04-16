import re

text = r"""\[
\begin{align*}
\lim_{n\to\infty} \left| \frac{a_{n+1}}{a_n} \right| &= \lim_{n\to\infty} \left| \frac{x^{2(n+1)-1}}{2(n+1)-1} \cdot \frac{2n-1}{x^{2n-1}} \right| \\
&= \lim_{n\to\infty} |x|^2 \cdot \frac{2n-1}{2n+1} = |x|^2 \cdot \lim_{n\to\infty} \frac{2n-1}{2n+1} = |x|^2.
\end{align*}
\]"""

display_math_pattern = r'\\\[(.*?)\\\]'
matches = re.findall(display_math_pattern, text, flags=re.DOTALL)
print(f"Matches: {len(matches)}")
if matches:
    print(matches[0])
