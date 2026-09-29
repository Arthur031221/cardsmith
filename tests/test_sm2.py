import pytest

from cardsmith.sm2 import DEFAULT_EASE_FACTOR, MIN_EASE_FACTOR, SM2State, review


def test_first_good_review_sets_interval_to_one_day():
    state = SM2State()
    new = review(state, quality=4)
    assert new.repetition == 1
    assert new.interval_days == 1


def test_second_good_review_sets_interval_to_six_days():
    state = review(SM2State(), quality=4)
    new = review(state, quality=4)
    assert new.repetition == 2
    assert new.interval_days == 6


def test_third_good_review_multiplies_by_ease_factor():
    state = SM2State()
    state = review(state, quality=4)
    state = review(state, quality=4)
    new = review(state, quality=4)
    assert new.repetition == 3
    assert new.interval_days == round(6 * state.ease_factor)


def test_low_quality_resets_repetition_and_interval():
    state = SM2State(repetition=3, ease_factor=2.6, interval_days=30)
    new = review(state, quality=1)
    assert new.repetition == 0
    assert new.interval_days == 1


def test_ease_factor_never_drops_below_minimum():
    state = SM2State(ease_factor=MIN_EASE_FACTOR)
    for _ in range(10):
        state = review(state, quality=0)
    assert state.ease_factor >= MIN_EASE_FACTOR


def test_perfect_recall_increases_ease_factor():
    state = review(SM2State(), quality=5)
    assert state.ease_factor > DEFAULT_EASE_FACTOR


def test_quality_out_of_range_raises():
    with pytest.raises(ValueError):
        review(SM2State(), quality=6)
    with pytest.raises(ValueError):
        review(SM2State(), quality=-1)
