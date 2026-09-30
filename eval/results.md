# Card generation benchmark

On 2026-09-30, `python3 eval/run_benchmark.py` generated 152 cards from the
3,248-word Chapter IV of *A Civic Biology, Presented in Problems*. The input was
split into 21 chunks, and the run requested eight cards per chunk. The model was
`qwen3:4b` through Ollama with thinking disabled on a MacBook Air M5 with 24 GB
unified memory. Generation took 775.5 seconds and returned no chunk errors.

The exact substring check matched the source quote for 142 of 152 cards, a rate
of 93.4 percent. This check measures whether the quoted text appears in the
input chunk. It does not measure whether the question and answer are factually
correct.

The first 40 cards were hand-rated against the source chapter using the
rubric in [rubric.md](rubric.md). 37 were accurate, 1 was inaccurate (it
merged two unrelated lines from a lab-activity list into one false pairing),
and 2 were unusable (one malformed card included the model's own aside
instead of an answer, one cloze card left its answer word visible outside
the blank). That puts factual accuracy at 37/40, or 92.5 percent. The full
per-card ratings and reasons are in [rated_cards.md](rated_cards.md).

The raw output and summary are in [generated_cards.json](generated_cards.json).
The input is [chapter.txt](chapter.txt), from Project Gutenberg ebook 39969.
