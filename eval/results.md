# Card generation benchmark

On 2026-09-30, `python3 eval/run_benchmark.py` generated 152 cards from the
3,248-word Chapter IV of *A Civic Biology, Presented in Problems*. The input was
split into 21 chunks, and the run requested eight cards per chunk. The model was
`qwen3:4b` through Ollama with thinking disabled on a MacBook Air M5 with 24 GB
unified memory. Generation took 775.5 seconds and returned no chunk errors.

The exact substring check matched the source quote for 142 of 152 cards, a rate
of 93.4 percent. This check measures whether the quoted text appears in the
input chunk. It does not measure whether the question and answer are factually
correct. The 40-card hand rating described in [rubric.md](rubric.md) has not yet
been completed, so no factual accuracy score is reported.

The raw output and summary are in [generated_cards.json](generated_cards.json).
The input is [chapter.txt](chapter.txt), from Project Gutenberg ebook 39969.
