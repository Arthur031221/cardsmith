# Hand-rating rubric for generated flashcards

Used to rate the cards produced by `eval/run_benchmark.py` from
`eval/chapter.txt`. Each card is read against the source chapter and given
one of three labels.

## Labels

**Accurate**
The fact tested by the card (the answer for a basic card, the hidden term
for a cloze card) matches what the source chapter actually says. The
question is unambiguous and has one defensible answer from the chapter.
Minor rewording of the source is fine. This is the only label that counts
toward the accuracy score.

**Inaccurate**
The card states something the chapter does not say, reverses a
relationship (cause and effect swapped, subject and object swapped),
invents a number or name not in the text, or answers a different question
than the one it asks.

**Unusable**
The card is not inaccurate but is not a fair test either: the question is
trivially answerable without reading the chapter (circular, or the answer
is inside the question), the question is ambiguous enough that a careful
reader could give two different but reasonable answers, or the card is
malformed (empty front, empty back, or a cloze with no hidden span).

## Scoring

```
accuracy = accurate_count / total_rated
```

`grounded` (whether the model's source_quote is an exact substring of its
source chunk, computed automatically by cardsmith) is reported separately
from hand-rated accuracy. A card can be accurate with a paraphrased quote
(grounded = false) and a card can be inaccurate despite a verbatim quote
(grounded = true, if the card's question or answer misreads a true
quote). The two numbers measure different things: grounded is a mechanical
provenance check, accuracy is a judgment call about the card's content.

## Method

1. Run `python3 eval/run_benchmark.py` against a local Ollama server with
   qwen3:4b pulled. This writes `eval/generated_cards.json`.
2. Take the first 40 cards in generation order (or all of them if fewer
   than 40 were generated).
3. For each card, read its `source_location` and `source_quote`, find that
   part of `eval/chapter.txt`, and read the surrounding paragraph.
4. Assign one label per card using the definitions above. Record the label
   and a one-line reason in `eval/rated_cards.md`.
5. Compute the accuracy score and write it, with the date, model, and rater,
   into `eval/results.md`.
