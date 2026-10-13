# Across Layers: Auditing Symbolic and Acoustic Organization in a Pretrained Music Representation Model

**Po-Chen Liu**  
Department of Computer Science  
National Tsing Hua University  
Hsinchu, Taiwan  
noeltimliu.com

## Abstract

Pretrained music representation models encode multiple aspects of musical
signals, but a single notion of representation quality can obscure how
different properties vary across model depth.
This study audits MERT-v1-95M using two complementary views:
controlled musical interventions and representational similarity analysis
(RSA) on 30 deterministically selected MAESTRO v3 works.
The pre-specified state-12 primary endpoint was positive
($0.0799$, 95% bootstrap CI $[0.0057, 0.1630]$), but the paired
sign-flip test did not meet the conventional .05 threshold
($p=0.0596$); the primary result is therefore non-confirming.
Exploratory intervention profiles showed persistent sensitivity to the
piano-to-harpsichord substitution and generally increasing
pitch-class-versus-transposition separation toward later states, whereas
symbolic RSA reached its descriptive maximum at state 8.
Post-freeze robustness analyses further showed that threshold-based inference
depends on the normalization/reference definition and finite sample
composition.
Together, the results show that *layer characterization is
metric-dependent*: controlled intervention sensitivity and across-piece
representational alignment capture different properties of the same
representation hierarchy.

**Keywords:** music representation learning, MERT, representational similarity analysis,
layer-wise analysis, music information retrieval

## Introduction

Large pretrained music-audio models such as MERT [1] have
expanded the use of transferable representations in music information
retrieval, while benchmarks such as MARBLE [2] emphasize
that representation quality depends on the task used to evaluate it.
A similar issue arises within a single pretrained model: describing one layer
as “better” or “more musical” depends on what property is being measured.

A representation may respond strongly to a controlled change within a musical
passage while showing a different pattern when its geometry is compared across
different pieces.
This study therefore separates two questions.
First, how strongly do representations change under controlled musical
interventions?
Second, how closely does the geometry among original musical excerpts align
with explicit symbolic and acoustic descriptor spaces?

The goal is not to identify a universally optimal layer.
Instead, the study asks whether complementary audit measurements characterize
model depth in the same way and how strongly such conclusions depend on the
chosen measurement.

## Methods

### Sample

The formal sample consists of 30 unique works from MAESTRO v3, a paired
audio–MIDI piano dataset introduced by Hawthorne *et al.* [3].
The works come from distinct composition families.
One deterministic 20-second segment was selected per work using a
quality-controlled procedure independent of embeddings and scientific
outcomes.
The sample is reproducible but is not probability-representative of the full
corpus.

### Controlled Interventions

Each intervention starts independently from the same original crop.
Five conditions were retained:


1. Original;
2. Global transposition by $+2$ semitones;
3. Piano-to-harpsichord preset substitution;
4. Tempo increase from 120 to 150 BPM ($1.25\times$ faster);
5. Fixed octave-preserving pitch-class permutation.


The tempo condition retains its complete natural 16-second duration and
therefore changes both tempo and input duration.
The pitch-class intervention reassigns pitch classes while preserving timing,
note duration, velocity, octave register, and other non-pitch symbolic
attributes.
It should therefore be interpreted as an operational probe of selected pitch
relationships rather than a complete measure of symbolic musical structure.

The interventions were not calibrated to a common perceptual or acoustic
magnitude.
Accordingly, their absolute sensitivity values should not be interpreted as
directly matched effect sizes.

### Representation Extraction

MIDI was rendered using FluidSynth and the TimGM6mb SoundFont under a fixed
synthetic rendering configuration.
Audio was produced at 24 kHz and processed using the pinned MERT-v1-95M
model [1] without training or fine-tuning.

All 13 returned states were retained: the input representation preceding the
first transformer block and the outputs of the 12 transformer blocks.
Whole-clip temporal mean pooling produced one 768-dimensional vector per
state for each instance.
The resulting formal dataset contains 150 instances: 30 works $\times$ 5
conditions.

### Normalized Intervention Sensitivity

For work $i$, condition $c$, and state $l$, intervention distance is


$$
d(i,c,l)
=
1-\cos
\left(
\mathbf{z}_{i,\mathrm{orig},l},
\mathbf{z}_{i,c,l}
\right).
\tag{1}
$$


A same-state between-piece reference scale is defined as


$$
b(i,l)
=
\operatorname{median}_{j\neq i}
\left[
1-\cos
\left(
\mathbf{z}_{i,\mathrm{orig},l},
\mathbf{z}_{j,\mathrm{orig},l}
\right)
\right].
\tag{2}
$$


Normalized sensitivity is then


$$
s(i,c,l)
=
\frac{d(i,c,l)}{b(i,l)}.
\tag{3}
$$


This quantity is a reference-relative audit metric: it expresses the
within-piece intervention distance relative to the typical same-state
between-piece distance for that work.
It is not an absolute perceptual or information scale.

The pre-specified primary endpoint at state 12 was


$$
s_{\mathrm{PC}}
-
\frac{
s_{\mathrm{transpose}}
+
s_{\mathrm{harpsichord}}
+
s_{\mathrm{tempo}}
}{3}.
\tag{4}
$$


### Representational Similarity Analysis

Representational similarity analysis (RSA) characterizes a representation by
the pairwise dissimilarity structure induced over a common stimulus
set [4, 5].
RSA used only the 30 original clips.
At each state, a MERT cosine-distance representational dissimilarity matrix
(RDM) was compared with two reference RDMs.

The symbolic descriptor contained normalized histogram blocks representing
pitch class, onset position, note duration, and pitch height.
The acoustic descriptor used log-mel temporal means and standard deviations.
Spearman correlation between RDM upper triangles quantified alignment between
MERT geometry and each descriptor geometry.

## Results

### Primary Endpoint

The state-12 primary estimate was $0.0799$, with a percentile-bootstrap 95%
confidence interval of $[0.0057, 0.1630]$.
The two-sided paired sign-flip test produced $p=0.0596$.
The pre-specified test therefore did not meet the conventional .05 threshold,
and the primary result is classified as non-confirming.

The positive percentile-bootstrap interval does not override this decision.
The bootstrap interval and sign-flip test are distinct inferential procedures
and are not inversion-equivalent; consequently, their threshold decisions
need not coincide exactly in a finite sample.

### Secondary State-12 Contrasts

Table 1 summarizes the three state-12 secondary contrasts,
and Fig. 1 visualizes the paired differences.
All three secondary null hypotheses were rejected after Holm adjustment.
Pitch-class permutation produced greater normalized sensitivity than
transposition and tempo, whereas the piano-to-harpsichord substitution
produced greater sensitivity than pitch-class permutation.
These contrasts do not replace the aggregate primary endpoint.

The exact secondary inferential procedure was fixed after descriptive
directions had been inspected and before the secondary inferential
computation.


**Table 1. Secondary contrasts at state 12.**

| Contrast | Mean | 95% CI | Holm $p$ |
| — | — | — | — |
| PC–Transpose | 0.1394 | [0.0895, 0.1914] | 0.00029997 |
| PC–Harpsichord | -0.4362 | [-0.5622, -0.3030] | 0.00029997 |
| PC–Tempo | 0.5365 | [0.4542, 0.6276] | 0.00029997 |



![Figure 1](figures/figure1_final_layer_contrasts.png)

*Figure 1. State-12 secondary contrasts. Error bars show unadjusted percentile-bootstrap intervals. Multiplicity-controlled decisions use Holm-adjusted sign-flip tests.*


### Layer-Wise Intervention Profiles

The piano-to-harpsichord substitution produced the largest mean normalized
sensitivity at every state.
Its magnitude decreased substantially toward middle depth but remained
prominent at later states.
Pitch-class-minus-transposition separation generally increased with depth,
although the trajectory contained local reversals.

The exploratory profiles in Fig. 2 therefore do not support
a simple monotonic “deeper means more symbolic” interpretation.
No layer-wise inferential procedure was used to select an optimal state.


![Figure 2](figures/figure2_layer_profiles.png)

*Figure 2. Exploratory normalized-sensitivity profiles across all returned states. Intervals are descriptive and are not simultaneous layer-wise significance intervals.*


### Representational Similarity

Both symbolic and acoustic descriptor geometries showed positive alignment
with MERT geometry across all states.
Symbolic RSA reached its descriptive maximum at state 8
($\rho=0.6565$) and decreased to $0.6052$ at state 12.
The acoustic profile was high at early states, lower around middle depth, and
recovered later; selected coefficients were $0.7172$ at state 2, $0.6261$ at
state 7, and $0.6824$ at state 12.
Figure 3 shows the two depth profiles.

These tests evaluate association between MERT geometry and each descriptor
geometry.
They do not test whether symbolic alignment is statistically stronger than
acoustic alignment, nor whether state 8 is statistically superior to other
states.


![Figure 3](figures/figure3_rsa_profiles.png)

*Figure 3. Symbolic and acoustic RSA coefficients across model depth. The symbolic maximum at state 8 is descriptive rather than a statistically selected optimum.*


### Post-Freeze Robustness Audit

After the scientific analysis had been frozen, additional robustness analyses
were conducted and explicitly classified as post-freeze, post-hoc, and
exploratory.
The original normalized primary was first reproduced exactly before any
alternative readout was examined.

Using raw cosine distances without the piece-specific normalization in
Eq. (3), the state-12 contrast had mean $0.00747$,
95% bootstrap CI $[0.00151, 0.01441]$, and a two-sided sign-flip
$p=0.0254$.
This alternative result does not retroactively confirm or replace the
pre-specified normalized primary.

Leave-one-piece-out analyses retained a positive estimate under all 30
single-piece omissions, with estimates ranging from $0.05225$ to $0.09035$.
The corresponding sign-flip $p$-values ranged from $0.02990$ to $0.11409$,
with median $p=0.06549$.
Thus, the estimated direction was more stable than the conventional
threshold-based inferential decision.

Descriptive decomposition across all 13 states further separated raw
within-piece intervention distances, the between-piece reference denominator,
and the resulting normalized sensitivities.
No additional layer-wise significance tests were conducted.

## Discussion

The intervention and RSA analyses provide different descriptive views of the
same representation hierarchy.
Under controlled intervention, pitch-class-versus-transposition separation
generally becomes larger toward later states.
Across-piece symbolic alignment, however, reaches its descriptive maximum at
an earlier state.
The two audit views therefore exhibit different depth profiles rather than
identifying a common universally prominent layer.

The central interpretation is that *layer characterization is
metric-dependent*.
A layer that displays stronger selectivity under a controlled intervention
need not be the layer whose across-piece geometry is most strongly aligned
with an explicit symbolic descriptor.
The results therefore do not support a single acoustic-to-symbolic hierarchy
or a universal downstream layer-selection rule.

The post-freeze robustness audit adds a second form of measurement dependence.
The sign of the primary contrast was comparatively stable, but crossing the
conventional .05 threshold depended on the normalization/reference definition
and on which individual work was omitted.
Accordingly, normalized sensitivity is best interpreted as a conditional
reference-relative audit metric rather than an absolute measure of
representation quality.

## Limitations

The conclusions are bounded to one pretrained model, one deterministic
30-work sample, one segment per work, and one synthetic rendering
configuration.

The interventions are not matched for perceptual or acoustic magnitude.
The piano-to-harpsichord substitution changes multiple acoustic properties
simultaneously, and the tempo manipulation is confounded with clip duration.
The fixed pitch-class permutation changes several aspects of pitch structure
at once and should not be interpreted as a pure manipulation of symbolic
organization.

Because all conditions were rendered using one FluidSynth/TimGM6mb pipeline,
the observed sensitivity profiles may not generalize directly to natural
recordings, alternative synthesizers, or other instrument renderings.

Whole-clip temporal mean pooling removes temporal detail and therefore makes
the reported geometry dependent on the selected readout.
Finally, symbolic and acoustic descriptors are explicit reference spaces, not
complete definitions of symbolic musical structure or acoustics.
Their RDMs are not independent conceptual axes, and RSA association does not
establish causal separation between symbolic and acoustic mechanisms.

## Reproducibility

The primary, secondary, layer-wise, and RSA analyses were frozen before
preparation of the public report.
The later robustness audit is retained separately and labeled
post-freeze, post-hoc, and exploratory.

The public repository provides methods, frozen result summaries, figures,
robustness outputs, reusable analysis code, attribution, and reproducibility
documentation.
A CPU-only verifier reconstructs the formal state-12 scientific metric from
the bundled verification vectors and checks exact agreement with the frozen
primary outputs.

Large source audio, model caches, intermediate embeddings, and other local
research artifacts are intentionally excluded from the public repository.
Full model re-inference therefore requires the external dataset, model, and
rendering dependencies described in the reproducibility documentation.

## Conclusion

This audit shows that conclusions about representation depth depend on how the
representation is interrogated.
Controlled intervention sensitivity and across-piece representational
alignment reveal distinct descriptive depth profiles in MERT-v1-95M, while
post-freeze robustness analyses show that inferential threshold crossing can
also depend on the selected normalization and finite sample composition.

Rather than identifying a single “best” layer, the results motivate a
measurement-aware interpretation of pretrained music representations and a
clear distinction between descriptive representation profiles and
confirmatory statistical claims.


## References


[1]
Y. Li *et al.*, “MERT: Acoustic Music Understanding Model with
Large-Scale Self-supervised Training,” in *Proc. Int. Conf. Learn.
Representations (ICLR)*, 2024.


[2]
R. Yuan *et al.*, “MARBLE: Music Audio Representation Benchmark for
Universal Evaluation,” in *Advances in Neural Information Processing
Systems*, vol. 36, pp. 39626–39647, 2023.


[3]
C. Hawthorne, A. Stasyuk, A. Roberts, I. Simon, C.-Z. A. Huang,
S. Dieleman, E. Elsen, J. Engel, and D. Eck,
“Enabling Factorized Piano Music Modeling and Generation with the MAESTRO
Dataset,” in *Proc. Int. Conf. Learn. Representations (ICLR)*, 2019.


[4]
N. Kriegeskorte, M. Mur, and P. A. Bandettini,
“Representational similarity analysis—connecting the branches of systems
neuroscience,” *Frontiers in Systems Neuroscience*, vol. 2, Art. no. 4,
2008, doi: 10.3389/neuro.06.004.2008.


[5]
H. Nili, C. Wingfield, A. Walther, L. Su, W. Marslen-Wilson, and
N. Kriegeskorte, “A Toolbox for Representational Similarity Analysis,”
*PLoS Computational Biology*, vol. 10, no. 4, Art. no. e1003553, 2014,
doi: 10.1371/journal.pcbi.1003553.
