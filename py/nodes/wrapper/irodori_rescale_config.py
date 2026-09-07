from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_RESCALE_CONFIG, positive_or_none


class IrodoriRescaleConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "RescaleConfig"),
            display_name="IrodoriTTS Rescale Config",
            category=CATEGORY,
            inputs=[
                io.Float.Input(
                    "truncation_factor",
                    default=0.0,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    tooltip="潜在の振れ幅を抑える係数です。0なら無効です。",
                ),
                io.Float.Input(
                    "rescale_k",
                    default=0.0,
                    min=0.0,
                    max=10.0,
                    step=0.1,
                    tooltip="rescale補正の強さです。0なら無効です。使用時はrescale_sigmaも指定します。",
                ),
                io.Float.Input(
                    "rescale_sigma",
                    default=0.0,
                    min=0.0,
                    max=3.0,
                    step=0.01,
                    tooltip="rescale補正のsigmaです。0なら無効です。使用時はrescale_kも指定します。",
                ),
                io.Float.Input(
                    "speaker_kv_scale",
                    default=0.0,
                    min=0.0,
                    max=5.0,
                    step=0.05,
                    tooltip="話者条件K/Vの強調倍率です。0なら無効です。",
                ),
                io.Float.Input(
                    "speaker_kv_min_t",
                    default=0.9,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    tooltip="speaker K/V補正を適用し始める拡散時刻です。",
                ),
                io.Int.Input(
                    "speaker_kv_max_layers",
                    default=-1,
                    min=-1,
                    max=64,
                    step=1,
                    tooltip="speaker K/V補正を適用する最大レイヤー数です。-1なら全レイヤーです。",
                ),
            ],
            outputs=[
                IO_RESCALE_CONFIG.Output(display_name="irodori_rescale_config"),
            ],
        )

    @classmethod
    def execute(
        cls,
        truncation_factor: float,
        rescale_k: float,
        rescale_sigma: float,
        speaker_kv_scale: float,
        speaker_kv_min_t: float,
        speaker_kv_max_layers: int,
    ):
        return io.NodeOutput(
            {
                "truncation_factor": positive_or_none(float(truncation_factor)),
                "rescale_k": positive_or_none(float(rescale_k)),
                "rescale_sigma": positive_or_none(float(rescale_sigma)),
                "speaker_kv_scale": positive_or_none(float(speaker_kv_scale)),
                "speaker_kv_min_t": float(speaker_kv_min_t),
                "speaker_kv_max_layers": (
                    None if int(speaker_kv_max_layers) < 0 else int(speaker_kv_max_layers)
                ),
            }
        )
