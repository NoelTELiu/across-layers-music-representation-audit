# Across Layers

## Auditing Symbolic and Acoustic Organization in a Pretrained Music Representation Model

Research report | Frozen study | Across Layers

## Question / Motivation

How do controlled musical changes and across-piece symbolic/acoustic organization appear across the depth of a pretrained music model? A model can respond strongly to a changed passage while organizing different passages in a way that aligns with musical descriptors. These are complementary questions, not interchangeable measures of musical understanding.

This project examines both using a frozen MERT-v1-95M model. Its central takeaway is **layer characterization is metric-dependent**: controlled intervention selectivity and across-piece representational alignment need not peak at the same layer. The result is a bounded characterization of one model and sample, not a recommendation of a universally best layer.

## Methods

**Sample and selection.** The formal dataset contains 30 unique MAESTRO v3 works from distinct composition families, selected through a deterministic, quality-controlled procedure. Identity and technical checks were completed before the sample was frozen; neither embeddings nor scientific outcomes influenced selection. This sample is not probability-representative of the corpus.

**Independent interventions.** One deterministic 20-second crop per work supplies every condition. Transposition adds two semitones without clipping or wrapping. Timbre changes the pinned TimGM6mb preset from Acoustic Grand Piano to Harpsichord while leaving MIDI identical. Tempo changes only the tempo meta-event to 1.25x speed; its complete 16-second clip is retained without padding or time stretching. A fixed pitch-class permutation changes pitch relationships within octave registers while preserving timing, velocities and other non-pitch content. It probes selected pitch structure, not the entirety of musical structure.

**Representation.** The same validated pipeline renders all conditions at 24 kHz and extracts a pinned, offline MERT model without training or fine-tuning. All 13 returned states are retained: the input to the first transformer block and the block outputs. Whole-clip mean pooling produces one 768-dimensional vector per state for each of the 150 original/intervention instances. Primary extractions alone are observations; repeat extractions document reproducibility.

**Two views of a layer.** Normalized sensitivity divides a within-piece original-to-intervention cosine distance by the median distance from that original to the other 29 originals at the same state. RSA separately asks whether pairs of original pieces have similar dissimilarity patterns in MERT and explicit symbolic/audio descriptors. One measures a response to intervention; the other measures alignment of across-piece geometry.

Sources: [frozen sample](results/sample_manifest.csv), [study design](docs/METHODS.md), [dataset manifest](results/dataset_manifest.csv), [protocol](docs/METHODS.md).

<!-- PAGEBREAK -->

## Results

### Primary endpoint: the specified test did not confirm the hypothesis

The pre-specified state-12 endpoint was pitch-class-permutation normalized sensitivity minus the mean sensitivity to transpose, timbre and tempo. Its across-piece estimate was **0.0799**, with percentile-bootstrap 95% CI **[0.0057, 0.1630]** and two-sided paired sign-flip **p = 0.0596**. The test did not meet .05. The positive interval is retained alongside that result; it neither replaces the specified test nor establishes primary confirmation. Non-confirmation also does not establish absence of an effect.

Primary inference used 10,000 paired piece-level bootstrap draws and 10,000 paired sign-flip permutations, each with its own seed-0 random generator. Pairing was preserved. No primary procedure was changed in response to its outcome.

### Secondary contrasts: the aggregate combines different responses

| State-12 contrast | Mean difference | Unadjusted 95% CI | Holm-adjusted p |
|---|---:|---|---:|
| PC - transpose | 0.1394 | [0.0895, 0.1914] | 0.00029997 |
| PC - timbre | -0.4362 | [-0.5622, -0.3030] | 0.00029997 |
| PC - tempo | 0.5365 | [0.4542, 0.6276] | 0.00029997 |

Positive values mean greater pitch-class-permutation sensitivity. All three secondary tests rejected their null hypotheses after Holm correction: pitch-class permutation exceeded transpose and tempo, while timbre exceeded pitch-class permutation. These planned contrasts do not replace the aggregate primary endpoint. Their exact paired bootstrap/sign-flip procedures were clarified after the primary analysis and after descriptive directions were inspected, but before secondary inference; they were not originally pre-specified.

![Figure 1: secondary state-12 contrasts](figures/figure1_final_layer_contrasts.png)

*Figure 1. Frozen mean paired contrasts and unadjusted percentile-bootstrap intervals. Multiplicity-controlled decisions use the separately reported Holm-adjusted sign-flip p-values. The figure is secondary evidence.*

Sources: [primary result](results/primary_result.json), [secondary summary](results/secondary_summary.csv). Values here are rounded transcriptions; the source files retain full precision.

<!-- PAGEBREAK -->

## Results: exploratory depth profiles

Timbre had the largest mean normalized sensitivity at every state. Its dominance attenuated substantially toward middle depth and then partly recovered. Pitch-class-minus-transposition separation grew overall with local reversals. The conditions therefore followed different trajectories; depth was not a single progression toward symbolic invariance.

![Figure 2: exploratory sensitivity profiles](figures/figure2_layer_profiles.png)

*Figure 2. (A) Mean normalized sensitivity for all four interventions. (B) Pitch-class-minus-comparator contrasts. Every state is shown without smoothing. Shading reproduces descriptive, unadjusted 95% bootstrap intervals; these are not simultaneous significance bands.*

These profiles are **EXPLORATORY**. One shared set of 10,000 piece-level bootstrap index samples preserved pairing across states, conditions and contrasts. No layer-wise p-values were computed and no layer was designated first significant or preferred. Implementation/reporting details were fixed before states 0-11 results were inspected. The exploratory profile does not extend the state-12 primary test to every state.

Sources: [all-state summaries](results/layer_profiles.csv), [exploratory specification](docs/METHODS.md), [frozen figure captions](figures/CAPTIONS.md).

<!-- PAGEBREAK -->

## Results: representational alignment

RSA used the original pieces only. It compared MERT's cosine-distance geometry at each state with two reference geometries: equal-weight symbolic histogram blocks for pitch class, onset position, note duration and pitch height; and log-mel audio summaries of temporal means and standard deviations. Spearman correlations measure agreement between the pairwise dissimilarity patterns. The descriptors are explicit references, not ground truth for all musical structure or acoustics.

![Figure 3: secondary/exploratory RSA profiles](figures/figure3_rsa_profiles.png)

*Figure 3. Frozen symbolic and audio RSA coefficients across all states. All 26 individual descriptor-association tests passed the specified BH-FDR procedure at q=.05. This does not test differences between the two descriptors or between layers.*

Both associations were positive throughout. Symbolic alignment had its descriptive maximum at state 8 (rho = 0.6565), then was 0.6052 at state 12. Audio alignment was early-high, middle-low and late-recovering: rho = 0.7172, 0.6261 and 0.6824 at states 2, 7 and 12. RSA is **SECONDARY / EXPLORATORY**; its implementation was clarified after the intervention analyses and before RSA results. No test establishes state 8 as best, symbolic superiority over audio, or a statistically preferred layer.

## Interpretation

The interventions and RSA characterize different aspects of the same representations. Pitch-class-versus-transposition separation grows overall toward later states, whereas symbolic RSA has a middle/later descriptive peak. **Layer characterization is metric-dependent:** controlled intervention selectivity and across-piece representational alignment need not peak at the same layer. This distinction does not override the non-confirming primary test.

The study supports a traceable account of sensitivity and alignment within its frozen setting. It does not support a simple "deeper = more symbolic" hierarchy, a downstream layer-selection rule, or a causal division into symbolic and acoustic mechanisms.

Sources: [RSA results](results/rsa_results.csv), [implementation clarification](results/rsa_specification.json), [existing synthesis](docs/SUPPLEMENTARY.md).

<!-- PAGEBREAK -->

## Limitations

**Scope.** A deterministic sample of classical piano works, one segment per work, one model and one rendering setup cannot establish generalization to other repertoires, passages, models or natural recordings. Identity auditing and reproducible selection improve traceability, not representativeness.

**What the interventions measure.** The four changes do not exhaust musical structure and are not matched for perceptual or acoustic magnitude. The pitch-class control preserves rhythm and other non-pitch content. The timbre preset changes acoustic properties together. The tempo condition also changes duration; this study does not isolate tempo from that duration difference. Whole-clip mean pooling compresses temporal structure, so the reported geometry is a property of that readout as well as the model.

**Evidence chronology.** Primary, secondary, exploratory and post-hoc evidence have different roles. The secondary inference was clarified after descriptive inspection; layer profiles have descriptive intervals only; RSA implementation was fixed after earlier analyses but before RSA results. These later details must not be described as originally pre-specified. The primary interval/test difference remains visible, with no favorable procedure substituted.

**Post-hoc supplement.** A descriptor-overlap follow-up was proposed after RSA results were inspected. Both partial associations remained positive across states under the specified rank-based control. This is descriptive only: it controls the specified descriptor geometry, not all acoustics or all symbolic information. Signed in-sample variance components are not causal attribution. [Figure 4](figures/figure4_posthoc_overlap.pdf) and the [post-hoc report](docs/SUPPLEMENTARY.md) remain technical supplementary material, not main-facing evidence. No p-values or confidence intervals were computed for this follow-up.

## Reproducibility

The [frozen output manifest](results/provenance.json) hash-pins the completed scientific artifacts. The [exact results table](results/provenance.json) retains links to authoritative fields and source hashes. Figures are reused from the frozen presentation assets.

The [frozen analysis plan](docs/METHODS.md), [rendering and analysis methods](docs/METHODS.md), [dataset inventory](results/dataset_manifest.csv) and [reproducibility guide](docs/REPRODUCIBILITY.md) preserve methods and provenance. The [reproduction record](docs/REPRODUCIBILITY.md) and existing analysis reproducibility records document separate-process checks; repeat embeddings are validation artifacts, never extra observations. [Runtime provenance](docs/REPRODUCIBILITY.md) and the [verified environment](requirements.txt) remain available for technical reproduction.

Large local caches are not bundled with the report. Independent reproduction requires the recorded acquisition provenance, paths and commands. This editorial presentation adds no analysis or execution.

Further [methods](docs/METHODS.md), [supplementary context](docs/SUPPLEMENTARY.md) and [attribution](docs/ATTRIBUTION.md) are available for technical readers. Scientific analysis is complete; this public copy changes presentation only.
