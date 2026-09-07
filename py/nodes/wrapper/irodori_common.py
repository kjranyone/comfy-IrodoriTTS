import json
from pathlib import Path

import folder_paths
import torch
from comfy_api.latest import io
from safetensors import safe_open

from ...modules.irodori_tts.inference_runtime import (
    list_available_runtime_devices,
    list_available_runtime_precisions,
)
from ...node_utils import node_category

PACKAGE_NAME = "IrodoriTTS"
CATEGORY = node_category(PACKAGE_NAME)

IO_MODEL_CONFIG = io.Custom("IRODORI_MODEL_CONFIG")
IO_LORA_STACK = io.Custom("IRODORI_LORA_STACK")
IO_REF_CONFIG = io.Custom("IRODORI_REF_CONFIG")
IO_VOICE_DESIGN_CONFIG = io.Custom("IRODORI_VOICE_DESIGN_CONFIG")
IO_CFG_CONFIG = io.Custom("IRODORI_CFG_CONFIG")
IO_DURATION_CONFIG = io.Custom("IRODORI_DURATION_CONFIG")
IO_RESCALE_CONFIG = io.Custom("IRODORI_RESCALE_CONFIG")
IO_SCHEDULE_CONFIG = io.Custom("IRODORI_SCHEDULE_CONFIG")
IO_TRIM_TAIL_CONFIG = io.Custom("IRODORI_TRIM_TAIL_CONFIG")


def runtime_devices() -> list[str]:
    return list_available_runtime_devices()


def runtime_precisions(device: str = "cuda") -> list[str]:
    try:
        return list_available_runtime_precisions(device)
    except Exception:
        return ["fp32", "bf16"]


def positive_or_none(value):
    """Map non-positive widget values (used as "auto/off") to None."""
    return None if value is None or value <= 0 else value


def checkpoint_path(model_name: str) -> str:
    resolved = folder_paths.get_full_path("checkpoints", model_name)
    return resolved if resolved else model_name


def read_latent_dim(checkpoint: str) -> int:
    """Read latent_dim from a checkpoint's embedded model config."""
    path = Path(checkpoint)
    if path.suffix.lower() == ".safetensors":
        with safe_open(str(path), framework="pt", device="cpu") as handle:
            metadata = handle.metadata() or {}
        raw = metadata.get("config_json")
        if raw is None:
            raise ValueError(f"checkpoint metadata has no config_json: {path}")
        config = json.loads(raw)
    else:
        payload = torch.load(path, map_location="cpu", weights_only=True)
        config = payload.get("model_config") if isinstance(payload, dict) else None

    if not isinstance(config, dict) or "latent_dim" not in config:
        raise ValueError(f"checkpoint model_config has no latent_dim: {path}")
    return int(config["latent_dim"])


def codec_repo_for(latent_dim: int) -> str:
    if int(latent_dim) == 32:
        return "Aratako/Semantic-DACVAE-Japanese-32dim"
    if int(latent_dim) == 128:
        return "facebook/dacvae-watermarked"
    raise ValueError(f"unsupported checkpoint latent_dim={latent_dim}")
