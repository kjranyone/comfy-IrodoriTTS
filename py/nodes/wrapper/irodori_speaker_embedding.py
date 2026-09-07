from pathlib import Path

import folder_paths
from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_REF_CONFIG


def _scan_embedding_files() -> list[str]:
    found: set[str] = set()
    for base in folder_paths.get_folder_paths("embeddings"):
        base_path = Path(base)
        if not base_path.is_dir():
            continue
        for path in base_path.rglob("*.speaker.safetensors"):
            found.add(path.relative_to(base_path).as_posix())
    return sorted(found)


def _resolve_embedding_path(name: str) -> str | None:
    if not name or name == "None":
        return None
    for base in folder_paths.get_folder_paths("embeddings"):
        candidate = Path(base) / name
        if candidate.is_file():
            return str(candidate.resolve())
    raise FileNotFoundError(f"speaker embedding not found under models/embeddings: {name}")


class IrodoriSpeakerEmbedding(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "SpeakerEmbedding"),
            display_name="IrodoriTTS Speaker Embedding",
            category=CATEGORY,
            inputs=[
                io.Combo.Input(
                    "speaker_embedding",
                    options=["None"] + _scan_embedding_files(),
                    tooltip="Speaker Inversion学習で作成した*.speaker.safetensorsをmodels/embeddingsから選択します。",
                ),
                io.Combo.Input(
                    "speaker_uncond_mode",
                    options=["mask", "noise"],
                    default="mask",
                    tooltip="CFGの無条件話者埋め込みの作り方です。maskはゼロ埋め(省VRAM)、noiseは参照埋め込みと同分散のノイズで置き換えます。",
                ),
            ],
            outputs=[
                IO_REF_CONFIG.Output(display_name="irodori_ref_config"),
            ],
        )

    @classmethod
    def execute(cls, speaker_embedding: str, speaker_uncond_mode: str):
        return io.NodeOutput(
            {
                "ref_wavs": [],
                "ref_embed": _resolve_embedding_path(speaker_embedding),
                "no_ref": False,
                "speaker_uncond_mode": str(speaker_uncond_mode),
            }
        )
