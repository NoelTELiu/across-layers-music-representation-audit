# Inspecting and reproducing the work

This public copy presents the completed study and selected reusable implementation. The immutable full research archive is identified by release `v1.0-application-project`, commit `ea9390dc1ceb3f1d1f0c748a850012caa919c5aa`, in the original project repository. It contains the full analysis/orchestration code and detailed audit history. This public tree does not replace that execution environment or include an automatic full-study runner. Access to that full archive is required for end-to-end reproduction; its external availability is not assumed by this local review copy.

## Inspect without rerunning science

Read the [report](../RESEARCH_REPORT.pdf), [methods](METHODS.md), [saved results](../results/primary_result.json), [sample manifest](../results/sample_manifest.csv), and [dataset manifest](../results/dataset_manifest.csv). The dataset manifest's MIDI/audio/embedding paths identify files in the full research release; those large local assets are deliberately absent here. They are provenance references, not broken public links.

[provenance.json](../results/provenance.json) maps public assets to source-release files and SHA256 hashes, records evidence classes, and identifies editorial projections. To verify hashes, links, saved outputs and the formal metric from the bundled state-12 vectors, run `python scripts/verify_public_release.py --root .` from the repository root. This performs no inferential resampling or model inference.

The original engineering records documented separate-process rendering/inference reproduction; scientific records documented deterministic separate-process reproduction of saved outputs. The public build only checks saved values, file identity and presentation. It does not rerun those procedures or claim new validation of the model/runtime.

## Implementation and environment

The retained `src/` modules implement MIDI cropping, +2 transposition, rendering, MERT extraction, acquisition and basic distance/provenance helpers. The existing `tests/test_smoke.py` uses synthetic engineering fixtures, never the research sample. These fixtures require dependencies and a configured FluidSynth/TimGM6mb installation; they were not run while building this copy. Full formal sampling, all intervention orchestration and scientific analysis runners remain in the pinned source release.

[requirements.txt](../requirements.txt) transcribes the recorded Python 3.11.9 / CUDA 12.6 research environment including librosa 0.10.2.post1. Use a separate environment appropriate to that platform. The source/model/audio assets and FluidSynth 2.4.4 are external prerequisites, not installed by this document. No dependency installation or environment change was performed for this copy.

For portable helper use, set `TIMGM6MB_SF2` and, where library discovery needs it, `FLUIDSYNTH_DLL` to your own installation. Host-specific DLL guesses have been removed from this copy. `configs/smoke.json` is for the one-piece engineering fixtures, not a formal-sample selector; its default SoundFont path is a placeholder under ignored `assets/`. Never substitute its smoke workflow for the frozen formal sample.

The full source release contains official MAESTRO acquisition logic, source hashes, pinned model identity and exact recorded commands. Reproduce the frozen selected performances/segments using those records, without resampling identities. [Attribution](ATTRIBUTION.md) identifies external assets. Working-tree line endings can affect byte hashes; verify using the manifest for this copy. No dataset/model binaries, caches or credentials are distributed here.

The small `results/state12_vectors.csv` export contains only the 150 frozen primary state-12 pooled vectors needed to reproduce the formal metric. All-state embedding caches and repeat extractions are omitted. The verifier compares raw distances, between-piece denominators, normalized sensitivities and primary per-piece effects to the frozen 4A table without inferential resampling.

## Minimal CPU verification and tests

Verification requires only Python and NumPy; the recorded NumPy version is 1.26.4. The full requirements file describes the research runtime and is not required for inspection. With pytest also installed, run:

```sh
python -B -m pytest -q tests/test_scientific_metrics.py tests/test_public_bundle.py -p no:cacheprovider
```

The optional engineering smoke suite uses synthetic fixtures and additional MIDI/rendering dependencies. Its audio-rendering test requires an external SoundFont; it is not needed to verify the frozen study. No dataset/model downloads occur in the verification command. [Robustness outputs](ROBUSTNESS.md) are saved later exploratory diagnostics; the verifier checks their schema and hashes without rerunning tests of hypotheses.

The manifest covers public files and excludes itself. Newly initialized local Git metadata is intentionally outside the scientific package manifest. UTF-8 text is stored with LF line endings, enforced by .gitattributes. Do not silently refresh hashes after changing frozen data.
