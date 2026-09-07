from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_DURATION_CONFIG


class IrodoriDurationConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "DurationConfig"),
            display_name="IrodoriTTS Duration Config",
            category=CATEGORY,
            inputs=[
                io.Float.Input(
                    "duration_scale",
                    default=1.0,
                    min=0.1,
                    max=3.0,
                    step=0.01,
                    tooltip="自動推定された秒数の倍率です。1.0より大きいと長く、小さいと短くなります。",
                ),
                io.Float.Input(
                    "min_seconds",
                    default=0.5,
                    min=0.1,
                    max=120.0,
                    step=0.1,
                    tooltip="自動推定で許可する最短秒数です。",
                ),
                io.Float.Input(
                    "max_seconds",
                    default=30.0,
                    min=0.1,
                    max=120.0,
                    step=0.5,
                    tooltip="自動推定で許可する最長秒数です。secondsを手動指定した場合もこの範囲に丸めます。",
                ),
            ],
            outputs=[
                IO_DURATION_CONFIG.Output(display_name="irodori_duration_config"),
            ],
        )

    @classmethod
    def execute(cls, duration_scale: float, min_seconds: float, max_seconds: float):
        return io.NodeOutput(
            {
                "duration_scale": float(duration_scale),
                "min_seconds": float(min_seconds),
                "max_seconds": float(max_seconds),
            }
        )
