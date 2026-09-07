import folder_paths
from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import (
    CATEGORY,
    IO_MODEL_CONFIG,
    checkpoint_path,
    codec_repo_for,
    read_latent_dim,
    runtime_devices,
    runtime_precisions,
)


def _clamp_precision_to_device(precision: str, device: str, label: str) -> str:
    if str(device).strip().lower().startswith("cuda"):
        return str(precision)
    if str(precision).strip().lower() != "fp32":
        print(
            f"[IrodoriTTS] {label}_precision={precision!r} is not available on {device!r}; using fp32.",
            flush=True,
        )
        return "fp32"
    return str(precision)


class IrodoriModelLoader(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "ModelLoader"),
            display_name="IrodoriTTS Model Loader",
            category=CATEGORY,
            inputs=[
                io.Combo.Input(
                    "model",
                    options=folder_paths.get_filename_list("checkpoints"),
                    tooltip="models/checkpointsに配置したIrodoriTTSチェックポイントを選択します。",
                ),
                io.Combo.Input(
                    "model_device",
                    options=runtime_devices(),
                    tooltip="TTSモデルを実行するデバイスです。",
                ),
                io.Combo.Input(
                    "model_precision",
                    options=runtime_precisions(),
                    tooltip="TTSモデルの計算精度です。cudaではbf16でVRAMを節約できます。",
                ),
                io.Combo.Input(
                    "codec_device",
                    options=runtime_devices(),
                    tooltip="DACVAE codecを実行するデバイスです。cpuも選べます。",
                ),
                io.Combo.Input(
                    "codec_precision",
                    options=runtime_precisions(),
                    tooltip="DACVAE codecの計算精度です。cpuではfp32を使用してください。",
                ),
                io.Boolean.Input(
                    "enable_watermark",
                    default=False,
                    tooltip="codec側のウォーターマーク処理を有効にします。通常は無効です。",
                ),
                io.Boolean.Input(
                    "enable_silentcipher",
                    default=False,
                    tooltip="SilentCipherによる音声ウォーターマークを有効にします。pip install silentcipherが必要です。",
                ),
                io.Boolean.Input(
                    "compile_model",
                    default=False,
                    tooltip="torch.compileで推論を高速化します。初回生成が遅くなります。",
                ),
                io.Boolean.Input(
                    "compile_dynamic",
                    default=False,
                    tooltip="torch.compileのdynamicモードです。通常は無効です。",
                ),
                io.Combo.Input(
                    "runtime_cache_policy",
                    options=["offload_after_use", "keep_gpu", "unload_after_use"],
                    default="offload_after_use",
                    tooltip="生成後のモデル保持方針。offload_after_useはCPU退避、keep_gpuはGPU保持、unload_after_useは破棄します。",
                ),
            ],
            outputs=[
                IO_MODEL_CONFIG.Output(display_name="irodori_model_config"),
            ],
        )

    @classmethod
    def execute(
        cls,
        model: str,
        model_device: str,
        model_precision: str,
        codec_device: str,
        codec_precision: str,
        enable_watermark: bool,
        enable_silentcipher: bool,
        compile_model: bool,
        compile_dynamic: bool,
        runtime_cache_policy: str,
    ):
        resolved = checkpoint_path(model)
        latent_dim = read_latent_dim(resolved)
        return io.NodeOutput(
            {
                "checkpoint": resolved,
                "codec_repo": codec_repo_for(latent_dim),
                "model_device": model_device,
                "model_precision": _clamp_precision_to_device(model_precision, model_device, "model"),
                "codec_device": codec_device,
                "codec_precision": _clamp_precision_to_device(codec_precision, codec_device, "codec"),
                "enable_watermark": bool(enable_watermark),
                "silentcipher_watermark_enabled": bool(enable_silentcipher),
                "compile_model": bool(compile_model),
                "compile_dynamic": bool(compile_dynamic),
                "runtime_cache_policy": str(runtime_cache_policy),
            }
        )
