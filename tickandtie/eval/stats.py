"""Small statistics helpers for reporting evaluation results."""
from math import sqrt


def wilson(successes, n, z=1.96):
    """95% Wilson score interval for a proportion; well behaved for small samples and 0 or n successes."""
    if n == 0:
        return (0.0, 1.0)
    p = successes / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return (max(0.0, centre - half), min(1.0, centre + half))