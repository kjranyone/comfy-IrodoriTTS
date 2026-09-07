from __future__ import annotations

import time
from pathlib import Path

from huggingface_hub import hf_hub_download, list_repo_files

# Tokenizer vocab/config files that may appear at a Hugging Face repo root.
_TOKENIZER_FILENAMES = frozenset(
    {
        "added_tokens.json",
        "config.json",
        "merges.txt",
        "sentencepiece.bpe.model",
        "special_tokens_map.json",
        "spiece.model",
        "tokenizer.json",
        "tokenizer.model",
        "tokenizer_config.json",
        "vocab.json",
        "vocab.txt",
    }
)

_TOKENIZER_MODEL_FILES = (
    "sentencepiece.bpe.model",
    "spiece.model",
    "tokenizer.json",
    "tokenizer.model",
    "vocab.json",
    "vocab.txt",
)


def _log(message: str) -> None:
    print(f"[hf-assets] {message}", flush=True)


def fetch_file(repo_id: str, filename: str, target_dir: str | Path) -> Path:
    """Download a single repo file into target_dir (skips when already present)."""
    target = Path(target_dir)
    destination = target / filename
    if destination.is_file():
        return destination

    target.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    _log(f"downloading {repo_id}/{filename} -> {target}")
    hf_hub_download(
        repo_id=repo_id,
        filename=filename,
        local_dir=str(target),
    )
    if not destination.is_file():
        raise FileNotFoundError(f"download did not produce {destination}")
    _log(f"downloaded {repo_id}/{filename} in {time.perf_counter() - started:.1f}s")
    return destination


def looks_like_tokenizer_dir(path: Path) -> bool:
    has_model_file = any((path / name).is_file() for name in _TOKENIZER_MODEL_FILES)
    return has_model_file and (path / "tokenizer_config.json").is_file()


def fetch_tokenizer_dir(repo_id: str, base_dir: str | Path) -> Path:
    """Download the root tokenizer files of repo_id into base_dir/<repo_id>."""
    root = Path(base_dir) / repo_id.replace("/", "_")
    if looks_like_tokenizer_dir(root):
        return root

    filenames = [
        name
        for name in list_repo_files(repo_id)
        if "/" not in name and name in _TOKENIZER_FILENAMES
    ]
    if not filenames:
        raise RuntimeError(f"no tokenizer files found in Hugging Face repo: {repo_id}")

    for filename in filenames:
        fetch_file(repo_id, filename, root)
    return root
