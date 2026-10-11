"""Unit tests for reciprocal rank fusion. No model or index needed."""
from tickandtie.index.hybrid import reciprocal_rank_fusion


def test_ids_found_by_both_methods_rank_first():
    fused = reciprocal_rank_fusion([["a", "b", "c"], ["c", "d", "a"]])
    assert fused[:2] == ["a", "c"]
    assert set(fused) == {"a", "b", "c", "d"}


def test_rank_one_in_a_single_list_loses_to_good_ranks_in_both():
    fused = reciprocal_rank_fusion([["x", "y"], ["z", "y"]])
    assert fused[0] == "y"


def test_ties_are_broken_by_id_so_results_are_stable():
    assert reciprocal_rank_fusion([["b"], ["a"]]) == ["a", "b"]


def test_empty_rankings_give_an_empty_result():
    assert reciprocal_rank_fusion([[], []]) == []