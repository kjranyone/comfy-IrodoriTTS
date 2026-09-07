from pathlib import Path

import folder_paths
from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_LORA_STACK

_ADAPTER_STATE_FILES = ("adapter_model.safetensors", "adapter_model.bin")


def _scan_adapter_dirs() -> list[str]:
    found: set[str] = set()
    for base in folder_paths.get_folder_paths("loras"):
        base_path = Path(base)
        if not base_path.is_dir():
            continue
        for config_path in base_path.rglob("adapter_config.json"):
            adapter_dir = config_path.parent
            if any((adapter_dir / name).is_file() for name in _ADAPTER_STATE_FILES):
                found.add(adapter_dir.relative_to(base_path).as_posix())
    return sorted(found)


def _resolve_adapter_dir(name: str) -> str | None:
    if not name or name == "None":
        return None
    for base in folder_paths.get_folder_paths("loras"):
        candidate = Path(base) / name
        if (candidate / "adapter_config.json").is_file():
            return str(candidate.resolve())
    raise FileNotFoundError(f"IrodoriTTS LoRA adapter directory not found under models/loras: {name}")


class IrodoriLoRAStack(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "LoRAStack"),
            display_name="IrodoriTTS LoRA Stack",
            category=CATEGORY,
            inputs=[
                IO_LORA_STACK.Input(
                    "prev",
                    optional=True,
                    tooltip="前段のLoRA Stackを接続します。複数アダプタを積む場合に使用します。",
                ),
                io.Combo.Input(
                    "lora",
                    options=["None"] + _scan_adapter_dirs(),
                    tooltip="models/loras内のLoRAアダプタディレクトリ(adapter_config.jsonを含むフォルダ)を選択します。",
                ),
                io.Float.Input(
                    "strength",
                    min=-10.0,
                    max=10.0,
                    step=0.01,
                    default=1.0,
                    tooltip="アダプタの適用強度です。1.0が標準、0.0で無効相当です。",
                ),
            ],
            outputs=[
                IO_LORA_STACK.Output(display_name="irodori_lora_stack"),
            ],
        )

    @classmethod
    def execute(
        cls,
        lora: str,
        strength: float,
        prev: list | None = None,
    ):
        stack = list(prev or [])
        path = _resolve_adapter_dir(lora)
        if path:
            stack.append({"path": path, "strength": float(strength), "name": Path(path).name})
        return io.NodeOutput(stack)
