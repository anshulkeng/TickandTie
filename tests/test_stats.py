"""Unit tests for the confidence interval used in the write-up."""
from tickandtie.eval.stats import wilson


def test_wilson_interval_for_half():
    low, high = wilson(5, 10)
    assert abs(low - 0.237) < 0.001 and abs(high - 0.763) < 0.001


def test_wilson_interval_never_leaves_zero_to_one():
    assert wilson(0, 10)[0] == 0.0 and abs(wilson(0, 10)[1] - 0.278) < 0.001
    assert wilson(10, 10)[1] == 1.0