# Post-freeze robustness

**POST-FREEZE / POST-HOC / EXPLORATORY.** These completed follow-ups were specified after the frozen scientific release. They do not replace or retroactively confirm the original hypothesis.

The original normalized state-12 primary remains authoritative: mean **0.0798888902**, percentile 95% CI **[0.00565131, 0.16302220]**, two-sided sign-flip **p = 0.05959404**; **PRIMARY NON-CONFIRMING**.

## Alternative raw-distance readout

For the same 30 pieces, raw PC-permutation cosine distance minus the mean raw transpose, timbre and tempo distances had mean **0.0074698741**, median **0.0061077690**, and 19 positive / 11 negative / 0 zero effects. Its percentile 95% CI was **[0.00150841, 0.01440650]**, with two-sided sign-flip **p = 0.02539746**. This later alternative scale is not confirmation of the normalized primary.

The completed calculation used 10,000 paired piece-level percentile-bootstrap resamples and 10,000 two-sided mean-statistic sign flips, independent NumPy default_rng/PCG64 seed-0 generators, and Monte-Carlo p = (1 + extreme count)/10001.

## Leave-one-piece-out stability

Each of 30 omissions retained 29 pieces, using the already-frozen normalized effects and **fixed original denominators**, without recomputing the reference pool. Each omission used a fresh seed-0 sign-flip generator with 10,000 permutations; no bootstrap was used. Mean effects ranged **0.05224810–0.09035176** and p-values **0.029897–0.114089** (median p **0.06549345**). These are stability diagnostics, not 30 confirmatory tests or an exclusion rule.

## Normalization decomposition and scope

[Normalization decomposition](../results/robustness/normalization_decomposition.csv) retains means and medians for all 13 states: four raw condition distances, the between-piece denominator, and four normalized sensitivities. It adds no layer-wise hypothesis tests or preferred-state rule.

Threshold crossing depends on normalization/reference choice and finite sample composition. Normalized sensitivity is a reference-relative audit metric, not an absolute perceptual scale. These diagnostics do not remove the unmatched intervention magnitudes, tempo-duration confound, synthetic rendering or N=30 limitations.

Inspect the [exact summary](../results/robustness/summary.json), [raw piece-level results](../results/robustness/raw_per_piece.csv), and [leave-one-out records](../results/robustness/leave_one_out.csv). Their scientific source records are identified in [provenance](../results/provenance.json). Verification checks saved numerical values and the original metric; it does not repeat inferential resampling.
