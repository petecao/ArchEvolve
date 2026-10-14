"""Tests for check_verdicts.py: the spike's verdict reading (map 13 item 7, design S7).

Run: python -m pytest -p no:cacheprovider test_check_verdicts.py
"""
from check_verdicts import problems


def goal(name, verdict="valid", passed=True, smoke=False):
    return {"goal": name, "property": name, "verdict": verdict, "passed": passed,
            "smoke": smoke, "provers": [{"prover": "Alt-Ergo:2.6.4", "time": 0.1, "success": 1}]}


VALID_TEXT = "[  Valid  ] Lemma 'A'\n"


def test_proof_stage_accepts_all_valid_goals_and_passed_smoke_tests():
    goals = [goal("typed_real_lemma_A"),
             goal("typed_real_f_wp_smoke_dead_loop_s1", verdict="unknown", passed=True, smoke=True)]
    assert problems("proof", goals, VALID_TEXT, expected_lemmas=["A"]) == []


def test_proof_stage_rejects_a_goal_that_is_not_valid():
    goals = [goal("typed_real_lemma_A", verdict="timeout", passed=False)]
    assert problems("proof", goals, VALID_TEXT, expected_lemmas=["A"]) != []


def test_proof_stage_rejects_a_failed_smoke_test_even_though_its_verdict_is_valid():
    # A smoke goal WP proves Valid signals dead code: passed is False.
    goals = [goal("typed_real_lemma_A"),
             goal("typed_real_f_wp_smoke_dead_code_s2", verdict="valid", passed=False, smoke=True)]
    assert problems("proof", goals, VALID_TEXT, expected_lemmas=["A"]) != []


def test_proof_stage_rejects_extern_and_partial_properties_in_the_text_report():
    goals = [goal("typed_real_lemma_A")]
    assert problems("proof", goals, VALID_TEXT + "[ Extern  ] Axiom 'X'\n", ["A"]) != []
    assert problems("proof", goals, VALID_TEXT + "[ Partial ] Lemma 'B'\n", ["A"]) != []


def test_proof_stage_rejects_a_missing_lemma_goal():
    goals = [goal("typed_real_lemma_A")]
    assert problems("proof", goals, VALID_TEXT, expected_lemmas=["A", "B"]) != []


def test_negative_stage_needs_an_unproven_goal_and_no_refutation():
    proven = [goal("typed_real_f_ensures_UNIT")]
    unproven = [goal("typed_real_f_ensures_UNIT", verdict="timeout", passed=False)]
    refuted = [goal("typed_real_f_ensures_UNIT", verdict="invalid", passed=False)]
    assert problems("negative", proven, "", []) != []
    assert problems("negative", unproven, "", []) == []
    assert problems("negative", refuted, "", []) != []


def test_negative_stage_can_require_named_goals_to_stay_unproven():
    goals = [goal("typed_real_lemma_FALSE_FROM_LEMMAS", verdict="timeout", passed=False),
             goal("typed_real_false_from_context_ensures_FALSE_FROM_CONTEXT")]
    assert problems("negative", goals, "", [],
                    must_fail=["FALSE_FROM_LEMMAS", "FALSE_FROM_CONTEXT"]) != []
