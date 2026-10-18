# Inspecting and reproducing the work

This repository contains a curated reproducible subset of the completed research: saved scientific results, figures, verification vectors and useful pipeline components. Git maintains repository history; ordinary documentation and report edits do not require file-hash synchronization.

## Inspect the frozen study

Read the [report](../RESEARCH_REPORT.pdf), [methods](METHODS.md), [primary result](../results/primary_result.json), [formal sample](../results/sample_manifest.csv), and [instance provenance](../results/dataset_manifest.csv). The MIDI/audio/embedding paths in the scientific records identify external research assets, not files distributed here. The compact [scientific provenance](../results/provenance.json) identifies the source commits, model revision, result sources and authoritative primary result.

The PDF is maintained manually through Overleaf. [RESEARCH_REPORT.tex](../RESEARCH_REPORT.tex) is its source snapshot; [Markdown](../RESEARCH_REPORT.md) provides GitHub reading. Local LaTeX compilation is not a validation prerequisite.

## Default CPU validation

Use Python with NumPy and pytest; the recorded research NumPy version is 1.26.4. No GPU, model download, MAESTRO corpus, SoundFont, LaTeX or network access is required:

```sh
python scripts/verify_results.py
python -m pytest -q
```

The verifier checks 30 pieces, 150 ordered instances, scientific table schemas, primary-only state-12 vector mappings and exact agreement of raw distances, denominators, normalized sensitivities and piece-level effects with saved primary values. It checks the original primary estimate, CI and sign-flip p, and the later robustness evidence classification. It performs no inferential resampling or model inference and does not inspect README, PDF or other documentation bytes.

[results/state12_vectors.csv](../results/state12_vectors.csv) contains the 150 primary state-12 pooled vectors required for this check. All-state embeddings and repeat extractions are omitted. The original primary remains **PRIMARY NON-CONFIRMING**. [Robustness diagnostics](ROBUSTNESS.md) remain **POST-FREEZE / POST-HOC / EXPLORATORY** and do not confirm or replace it.

## Optional engineering fixtures

[tests/optional/test_smoke.py](../tests/optional/test_smoke.py) uses synthetic fixtures and is excluded from default pytest discovery. Its MIDI tests require Mido; the rendering test additionally requires FluidSynth and a configured TimGM6mb SoundFont. To run that suite in a suitably configured environment:

```sh
python -m pytest -q tests/optional/test_smoke.py
```

The retained source modules cover acquisition, cropping, transposition, rendering and MERT extraction. The smoke configuration is an engineering fixture, not the formal scientific sample. Never replace the frozen selected performances or segment coordinates with its selection workflow.

## Full re-inference

Full data/model re-inference requires external MAESTRO data, the pinned MERT model and the FluidSynth/TimGM6mb rendering dependencies. [requirements.txt](../requirements.txt) records the Python 3.11.9 / CUDA 12.6 research environment, including librosa 0.10.2.post1; it is not the minimal CPU validation dependency list. Set `TIMGM6MB_SF2` and, if needed, `FLUIDSYNTH_DLL` for your own installation. See [methods](METHODS.md), [model identity](../results/model_manifest.json) and [attribution](ATTRIBUTION.md).

The full execution history and orchestration remain in the original research archive identified in scientific provenance, including release `v1.0-application-project`. Access to that archive is needed for end-to-end reproduction and is not assumed here. Original engineering records documented separate-process rendering/inference reproduction; scientific records documented deterministic saved-output reproduction. The CPU checks here do not newly validate that runtime. Dataset/model binaries, source audio, caches and credentials are not distributed.
