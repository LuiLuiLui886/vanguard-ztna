#!/usr/bin/env python3
"""Build a source archive from an explicit allowlist, excluding private lab state."""

import hashlib
import os
import re
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOP_LEVEL = (
    "AGENTS.md", "VANGUARD_CONTEXT.md", "LANJUTKAN_PROYEK.md", "README.md", "pyproject.toml", ".gitignore",
    "CODEX_VANGUARD_MASTER_PROMPT.md",
)
DIRECTORIES = ("vanguard", "tests", "scripts", "deploy", "docs")
SUFFIXES = {".py", ".md", ".html", ".css", ".xml", ".sh", ".ps1", ".txt", ".example", ".service", ".bat", ".json", ".lock"}


def main():
    version = re.search(r'^version = "([0-9]+\.[0-9]+\.[0-9]+)"$',
                        (ROOT / "pyproject.toml").read_text(), re.MULTILINE).group(1)
    files = [ROOT / name for name in TOP_LEVEL]
    files.append(ROOT / "deploy/inventory.example.json")
    files.append(ROOT / "deploy/resource-policy.example.json")
    files.append(ROOT / ".github/workflows/ci.yml")
    for directory in DIRECTORIES:
        files.extend(p for p in (ROOT / directory).rglob("*")
                     if p.is_file() and not p.is_symlink() and p.suffix in SUFFIXES
                     and (p.suffix not in {".json", ".lock"} or directory == "deploy")
                     and not any(part.startswith(".") or part == "__pycache__"
                                 for part in p.relative_to(ROOT).parts))
    files = sorted(set(files))
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    archive = output / f"vanguard-{version}.tar.gz"
    # Existing release evidence must be preserved, even when a rebuild is requested.
    if archive.exists():
        raise FileExistsError(f"Release already exists: {archive}")
    with tempfile.TemporaryDirectory(prefix=".source-build-", dir=output) as temporary:
        pending = Path(temporary) / archive.name
        with tarfile.open(pending, "w:gz") as bundle:
            for path in sorted(files):
                bundle.add(path, arcname=str(path.relative_to(ROOT)), recursive=False)
        with pending.open("rb") as stream:
            os.fsync(stream.fileno())
        # Atomic publication without overwriting an existing release.
        os.link(pending, archive)
    artifacts = sorted([*output.glob("*.tar.gz"), *output.glob("*.whl")])
    sums = []
    for path in artifacts:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        sums.append(f"{digest}  {path.relative_to(ROOT)}\n")
    with tempfile.NamedTemporaryFile(mode="w", dir=output, delete=False) as stream:
        pending_sums = Path(stream.name)
        stream.write("".join(sums))
        stream.flush()
        os.fsync(stream.fileno())
    try:
        pending_sums.replace(output / "SHA256SUMS")
    finally:
        pending_sums.unlink(missing_ok=True)
    print(f"Created {archive.relative_to(ROOT)} with {len(files)} source/documentation files")
    print("Updated dist/SHA256SUMS")


if __name__ == "__main__":
    main()
