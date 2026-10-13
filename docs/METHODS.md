# Methods and evidence boundaries

The formal study uses 30 unique MAESTRO v3 musical units from distinct composition families, with at most three accepted pieces per mandatory creator (including substantive arrangers). Selection was deterministic and quality-controlled, independent of embeddings and outcomes, and not probability-representative. The frozen [sample manifest](../results/sample_manifest.csv) records the selected performance, segment coordinates, identities and hashes.

Candidate identities were audited sequentially in ascending SHA256 order of `MRA-2026-formal-audit-queue|` plus proposed-group identifier. Within each resolved exact unit, performances were ordered by SHA256 of `MRA-2026-performance-order|` plus MIDI filename. Aliases/families were checked across the pool; ambiguous candidates were skipped. Source-specific technical failures permitted retry; infrastructure errors did not. Full adjudication records remain in the immutable source release linked in [reproducibility](REPRODUCIBILITY.md).

## Segments and interventions

The deterministic segment method starts at 20% of metadata duration and shifts forward by one second until a 20-second window has at least 20 positive-velocity note onsets across ten one-second bins. Cropping reconstructs active notes and sustain/controller state. Selected coordinates were frozen before analysis.

Each condition starts independently from the original crop: +2 semitones without clipping/wrapping; identical MIDI with TimGM6mb bank 0/program 6 Harpsichord instead of bank 0/program 0 Acoustic Grand Piano; tempo-only change from 500,000 to 400,000 microseconds/beat; and fixed pitch-class mapping `[9,2,7,4,5,11,0,3,6,10,8,1]`. The pitch mapping retains octave register, ticks, velocities, durations and non-pitch content. Tempo retains the complete natural 16-second clip; the other conditions are 20 seconds. These are operational manipulations, not matched perceptual changes or exhaustive definitions of musical structure.

## Rendering and representation

FluidSynth 2.4.4 uses 24 kHz mono float audio, gain 0.2, one synth core, stereo mean, no reverb/chorus, output loudness normalization or release tail. The pinned TimGM6mb SHA256 is `c5378b62028c920cb11e4803327983fee2f2cdff5dc89c708e39da417e51c854`.

MERT-v1-95M revision `12af15fef9d0ac838c3f475bfbbf26d2060dd4f5` runs offline in CUDA float32 evaluation mode, deterministic algorithms, seed 0, two Torch threads and CUBLAS workspace `:4096:8`. CQT is disabled; the pinned feature extractor performs no resampling/chunking. All 13 states are whole-clip mean-pooled to [13,768]. Primary extractions alone are observations; repeats document reproducibility.

## Measurement and inference

At each state, normalized sensitivity divides original-to-condition cosine distance by the median original-to-other-original distance across the other 29 pieces. No epsilon, vector repair or clipping is applied. Finite positive vector norms and denominators are required.

**PRIMARY:** state 12 only; PC sensitivity minus the mean of transpose, timbre and tempo sensitivities. The mean piece-level effect uses 10,000 paired percentile-bootstrap resamples and 10,000 two-sided sign-flip permutations, separate seed-0 PCG64 generators. Monte-Carlo p is (1 + extreme count)/10001. The specified test is non-confirming; its positive percentile interval is retained separately.

**SECONDARY:** three state-12 PC-minus-comparator contrasts, Holm correction across the three sign-flip p-values, unadjusted bootstrap intervals. Contrasts were planned; exact inference was clarified after primary/descriptive inspection and before secondary inference, not originally pre-specified.

**EXPLORATORY:** all-state profiles share one set of 10,000 seed-0 paired bootstrap indices; descriptive intervals only, no layer-wise p-values or preferred-state rule. Implementation was fixed before states 0–11 results.

**SECONDARY / EXPLORATORY RSA:** original pieces only, cosine RDMs, Spearman upper-triangle association, 10,000 piece-label permutations and BH-FDR q=.05 across 26 tests. Symbolic blocks are pitch class, normalized onset position, note duration and pitch height, independently L1-normalized and equally weighted. Audio uses 64-bin log-mel temporal mean and standard deviation. Exact numerical bins, preprocessing and inference settings are preserved in [RSA specification](../results/rsa_specification.json). Implementation was clarified after intervention analyses but before RSA results.

**POST-HOC EXPLORATORY:** descriptor overlap and partial rank-based associations were proposed after RSA inspection and specified before execution. The [post-hoc specification](../results/posthoc_specification.json) preserves residualization and signed variance-partition definitions. No significance inference or causal interpretation applies.

## Metric implementation and later robustness

The formal reported metric is the no-clipping [scientific_metrics.py](../src/scientific_metrics.py). [distances.py](../src/distances.py) is a historical engineering helper retained for smoke-test compatibility; its clipping behavior is not the scientific definition. Later [robustness diagnostics](ROBUSTNESS.md) are POST-FREEZE / POST-HOC / EXPLORATORY and do not change that definition or the original primary conclusion.
