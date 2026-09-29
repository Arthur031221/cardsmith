"""SM-2 spaced repetition scheduler.

The classic algorithm from SuperMemo 2 (Wozniak, 1987). A review grades
recall quality from 0 (total blackout) to 5 (perfect recall). Quality below
3 resets the card to the start of the learning sequence.
"""

from __future__ import annotations

from dataclasses import dataclass

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5


@dataclass(frozen=True)
class SM2State:
    repetition: int = 0
    ease_factor: float = DEFAULT_EASE_FACTOR
    interval_days: int = 0


def review(state: SM2State, quality: int) -> SM2State:
    """Apply one review of the given quality (0 to 5) and return the new state."""
    if not 0 <= quality <= 5:
        raise ValueError(f"quality must be 0 to 5, got {quality}")

    ease_factor = state.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease_factor = max(ease_factor, MIN_EASE_FACTOR)

    if quality < 3:
        return SM2State(repetition=0, ease_factor=ease_factor, interval_days=1)

    repetition = state.repetition + 1
    if repetition == 1:
        interval_days = 1
    elif repetition == 2:
        interval_days = 6
    else:
        interval_days = round(state.interval_days * ease_factor)
    return SM2State(
        repetition=repetition, ease_factor=ease_factor, interval_days=max(interval_days, 1)
    )
