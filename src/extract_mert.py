"""Pinned MERT-only evaluation, all returned states, whole-clip mean pooling."""

import importlib.metadata
import json
import os
from pathlib import Path

import numpy as np
import soundfile as sf

from .common import ROOT, fingerprint, sha256, write_json
from .runtime_metrics import measure_forward

# Keep model code/weight caches inside the ignored repository cache.
os.environ.setdefault("HF_HOME", str(ROOT / ".cache/huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache/matplotlib"))

from huggingface_hub import HfApi, snapshot_download
import torch
from transformers import AutoModel, Wav2Vec2FeatureExtractor


def resolve_model(config):
    path = ROOT / "results/model_manifest.json"
    prior = json.loads(path.read_text()) if path.exists() else None
    revision = (
        config["model_revision"]
        or (prior["revision"] if prior else HfApi().model_info(config["model_id"]).sha)
    )
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Model revision must resolve to immutable 40-character SHA")

    snapshot = Path(
        snapshot_download(
            config["model_id"],
            revision=revision,
            allow_patterns=[
                "*.json",
                "*.py",
                "model.safetensors",
                "pytorch_model.bin",
                "README.md",
                "LICENSE*",
            ],
        )
    )

    manifest = {
        "model_id": config["model_id"],
        "revision": revision,
        "code_revision": revision,
        "files": {
            p.name: sha256(p)
            for p in sorted(snapshot.iterdir())
            if p.is_file()
        },
    }
    write_json(path, manifest)
    return snapshot, manifest


class MERTExtractor:
    def __init__(self, config):
        self.config = config

        requested_device = os.environ.get("MERT_DEVICE", "cpu").lower()

        if requested_device == "cuda":
            if not torch.cuda.is_available():
                raise RuntimeError(
                    "MERT_DEVICE=cuda was requested but CUDA is unavailable"
                )
            self.device = torch.device("cuda")
        elif requested_device == "cpu":
            self.device = torch.device("cpu")
        else:
            raise ValueError(f"Unsupported MERT_DEVICE: {requested_device}")

        torch.manual_seed(config["seed"])
        np.random.seed(config["seed"])

        if self.device.type == "cuda":
            torch.cuda.manual_seed_all(config["seed"])

        torch.set_num_threads(config["torch_threads"])
        torch.use_deterministic_algorithms(True)

        self.snapshot, self.model_manifest = resolve_model(config)

        self.processor = Wav2Vec2FeatureExtractor.from_pretrained(
            self.snapshot,
            local_files_only=True,
        )

        # MERT's official checkpoint uses custom modeling code; exact code is hashed.
        self.model, self.loading_info = AutoModel.from_pretrained(
            self.snapshot,
            trust_remote_code=True,
            local_files_only=True,
            output_loading_info=True,
        )

        if any(self.loading_info.values()):
            raise RuntimeError(
                f"Pretrained loading diagnostics are not empty: {self.loading_info}"
            )

        self.model = self.model.to(self.device).float().eval()

        for parameter in self.model.parameters():
            parameter.requires_grad_(False)

        if self.processor.sampling_rate != config["sample_rate"]:
            raise RuntimeError(
                "Renderer and required model sample rates do not match"
            )

        if self.model.config.num_hidden_layers != 12:
            raise RuntimeError("Unexpected MERT-v1-95M configuration")

        self.versions = {
            p: importlib.metadata.version(p)
            for p in (
                "torch",
                "transformers",
                "numpy",
                "huggingface-hub",
                "soundfile",
            )
        }

    def extract(self, wav_path, variant, force=False):
        waveform, sr = sf.read(
            wav_path,
            dtype="float32",
            always_2d=False,
        )

        if waveform.ndim != 1 or sr != self.processor.sampling_rate:
            raise ValueError(
                "Require mono waveform at model sample rate, without implicit resampling"
            )

        if len(waveform) != round(self.config["segment_duration_s"] * sr):
            raise ValueError("Unexpected clip duration")

        provenance = {
            "audio_sha256": sha256(wav_path),
            "model": self.model_manifest,
            "preprocessor": self.processor.to_dict(),
            "versions": self.versions,
            "pooling": (
                "arithmetic mean over all time frames, "
                "separately for each returned state"
            ),
            "device": str(self.device),
            "dtype": "float32",
            "seed": self.config["seed"],
            "torch_threads": self.config["torch_threads"],
            "sample_rate": sr,
            "samples": len(waveform),
            "extraction_code_sha256": sha256(__file__),
        }

        key = fingerprint(provenance)
        cache = ROOT / "embeddings" / f"{variant}-{key}.npz"
        metadata = cache.with_suffix(".json")

        if not force and cache.exists() and metadata.exists():
            record = json.loads(metadata.read_text())

            if (
                record["provenance"] != provenance
                or record["cache_sha256"] != sha256(cache)
            ):
                raise RuntimeError(
                    "Embedding cache provenance or hash mismatch"
                )

            with np.load(cache, allow_pickle=False) as data:
                pooled = data["pooled"].copy()

            if (
                pooled.shape != tuple(record["pooled_shape"])
                or not np.isfinite(pooled).all()
            ):
                raise RuntimeError("Invalid cached embeddings")

            return pooled, record, True

        inputs = self.processor(
            waveform,
            sampling_rate=sr,
            return_tensors="pt",
            padding=False,
        )

        inputs = {
            key: value.to(self.device) if torch.is_tensor(value) else value
            for key, value in inputs.items()
        }

        block_inputs = []
        block_outputs = []

        hooks = [
            self.model.encoder.layers[0].register_forward_pre_hook(
                lambda module, args: block_inputs.append(args[0])
            )
        ]

        hooks.extend(
            layer.register_forward_hook(
                lambda module, args, output: block_outputs.append(output[0])
            )
            for layer in self.model.encoder.layers
        )

        try:
            with torch.inference_mode(), measure_forward(self.device) as performance:
                outputs = self.model(
                    **inputs,
                    output_hidden_states=True,
                    return_dict=True,
                )
        finally:
            for hook in hooks:
                hook.remove()

        with torch.inference_mode():
            states = outputs.hidden_states

            if len(states) != 13 or len(block_outputs) != 12:
                raise RuntimeError(
                    "Unexpected returned-state count; inspect indexing before proceeding"
                )

            if len(block_inputs) != 1 or not torch.equal(
                states[0],
                block_inputs[0],
            ):
                raise RuntimeError(
                    "State 0 does not match the input to Transformer block 1"
                )

            if not all(
                torch.equal(state, output)
                for state, output in zip(states[1:], block_outputs)
            ):
                raise RuntimeError(
                    "Returned states do not match Transformer block outputs"
                )

            if not torch.equal(states[-1], outputs.last_hidden_state):
                raise RuntimeError(
                    "Final returned state does not match last_hidden_state"
                )

            shapes = [list(state.shape) for state in states]

            if any(
                shape != [1, shapes[0][1], 768]
                for shape in shapes
            ):
                raise RuntimeError(
                    f"Unexpected hidden-state shapes: {shapes}"
                )

            pooled = torch.stack(
                [state[0].mean(dim=0) for state in states]
            ).cpu().numpy()

        if pooled.shape != (13, 768):
            raise RuntimeError(
                f"Unexpected pooled shape: {pooled.shape}"
            )

        if (
            not np.isfinite(pooled).all()
            or np.any(np.linalg.norm(pooled, axis=1) == 0)
        ):
            raise RuntimeError(
                "Nonfinite or zero-norm embeddings"
            )

        labels = [
            "encoder_input_before_transformer_blocks"
        ] + [
            f"transformer_block_{i}_output"
            for i in range(1, len(states))
        ]

        temp = cache.with_suffix(".npz.tmp")

        with temp.open("wb") as stream:
            np.savez_compressed(
                stream,
                pooled=pooled,
                state_index=np.arange(len(states)),
            )

        temp.replace(cache)

        record = {
            "variant": variant,
            "provenance": provenance,
            "cache_key": key,
            "cache_path": str(cache.relative_to(ROOT)),
            "cache_sha256": sha256(cache),
            "state_labels": labels,
            "hidden_state_shapes": shapes,
            "pooled_shape": list(pooled.shape),
            "performance": performance,
            "loading_info": self.loading_info,
            "state_semantics_verified_by_hooks": True,
            "state_0_semantics": (
                "block 1 input after feature projection, "
                "positional-convolution addition, encoder layer normalization "
                "and dropout (identity in eval)"
            ),
        }

        write_json(metadata, record)

        return pooled, record, False
