from latex_parser import parse_latex_math
import json

test_cases = [
    r"\lim_{n\to\infty} \frac{b_{n+1}}{b_n} = \lim_{n\to\infty} \frac{(n+1)^2 r^{n+1}}{n^2 r^n} = \lim_{n\to\infty} \frac{(n+1)^2}{n^2} \cdot r.",
    r"\lim_{n\to\infty} \frac{b_{n+1}}{b_n} = \lim_{n\to\infty} \left( \frac{(n+1)^2}{n^2} \cdot r \right) = r \cdot \lim_{n\to\infty} \frac{(n+1)^2}{n^2} = r \cdot \lim_{n\to\infty} \left(1 + \frac{1}{n}\right)^2.",
    r"\lim_{n\to\infty} \left(1 + \frac{1}{n}\right)^2 = \left( \lim_{n\to\infty} \left(1 + \frac{1}{n}\right) \right)^2 = \left( \lim_{n\to\infty} 1 + \lim_{n\to\infty} \frac{1}{n} \right)^2 = (1 + 0)^2 = 1."
]

for i, tc in enumerate(test_cases):
    print(f"Testing case {i+1}...")
    try:
        ast = parse_latex_math(tc)
        print(f"Case {i+1} parsed successfully.")
    except Exception as e:
        print(f"Case {i+1} failed with error: {e}")
