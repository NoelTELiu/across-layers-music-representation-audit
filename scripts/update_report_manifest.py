"""Register a completed report replacement; refuse unrelated package changes.

Run only after compiling and reviewing RESEARCH_REPORT.pdf:
    python scripts/update_report_manifest.py --root .
No scientific computation or result-table changes are permitted.
"""
import argparse
import hashlib
import json
from pathlib import Path

ALLOWED = {"RESEARCH_REPORT.tex", "RESEARCH_REPORT.md", "RESEARCH_REPORT.pdf",
           ".gitignore", "scripts/update_report_manifest.py"}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def encoded(obj):
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()

def update(root):
    manifest_path = root / "MANIFEST.json"
    provenance_path = root / "results/provenance.json"
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    old = {r["path"]: r for r in manifest["files"]}
    for name in sorted(ALLOWED):
        if not (root / name).is_file():
            raise ValueError("Required completed-report file missing: " + name)
    if not (root / "RESEARCH_REPORT.pdf").read_bytes().startswith(b"%PDF-"):
        raise ValueError("Report is not a PDF")
    actual = {f.relative_to(root).as_posix() for f in root.rglob("*")
              if f.is_file() and ".git" not in f.relative_to(root).parts}
    if actual != set(old) | ALLOWED | {"MANIFEST.json"}:
        raise ValueError("Unexpected added or missing public files")
    for name, record in old.items():
        path = root / name
        if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Unsafe path: " + name)
        if name not in ALLOWED and (sha(path) != record["sha256"] or path.stat().st_size != record["bytes"]):
            raise ValueError("Unrelated frozen/public artifact changed: " + name)
    changed = sorted(name for name in ALLOWED if name not in old or sha(root/name) != old[name]["sha256"])
    if not changed:
        return {"status": "UNCHANGED"}
    provenance = json.loads(provenance_path.read_bytes())
    replaced = {"RESEARCH_REPORT.md", "RESEARCH_REPORT.pdf"}
    historical = [o for o in manifest["origins"] if o["public_path"] in replaced]
    manifest["origins"] = [o for o in manifest["origins"] if o["public_path"] not in replaced]
    tex_hash = sha(root / "RESEARCH_REPORT.tex")
    for name in sorted(replaced | {"RESEARCH_REPORT.tex"}):
        manifest["origins"].append({"source_path": "RESEARCH_REPORT.tex", "source_sha256": tex_hash,
            "public_path": name, "public_sha256": sha(root/name),
            "projection": "User-supplied revised report; Markdown transcription or compiled PDF; frozen scientific tables unchanged"})
    # Existing non-report origins retain their historical source attribution.
    for origin in manifest["origins"]:
        if origin["public_path"] in ALLOWED:
            origin["public_sha256"] = sha(root / origin["public_path"])
    amendment = {"kind": "user_supplied_report_replacement", "changed_paths": changed,
        "previous_manifest_sha256": hashlib.sha256(original_manifest).hexdigest(),
        "previous_report_origins": historical,
        "latex_source_sha256": tex_hash,
        "frozen_nonreport_files_verified": True,
        "scientific_results_recomputed": False}
    provenance.setdefault("presentation_amendments", []).append(amendment)
    provenance["source_mappings"] = manifest["origins"]
    # Prepare both serializations before writing; no manual hash replacements.
    provenance_bytes = encoded(provenance)
    records = []
    for name in sorted(set(old) | ALLOWED):
        raw = provenance_bytes if name == "results/provenance.json" else (root/name).read_bytes()
        records.append({"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    manifest["files"] = records
    manifest_bytes = encoded(manifest)
    provenance_path.write_bytes(provenance_bytes)
    manifest_path.write_bytes(manifest_bytes)
    return {"status": "UPDATED", "changed_paths": changed}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(update(args.root.resolve()), sort_keys=True))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, "STOP: " + str(error) + "\n")
