from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_TRIM_TAIL_CONFIG


class IrodoriTrimTailConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "TrimTailConfig"),
            display_name="IrodoriTTS Trim Tail Config",
            category=CATEGORY,
            inputs=[
                io.Int.Input(
                    "tail_window_size",
                    default=20,
                    min=1,
                    max=200,
                    step=1,
                    tooltip="末尾判定に使う潜在窓サイズです。",
                ),
                io.Float.Input(
                    "tail_std_threshold",
                    default=0.05,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    tooltip="末尾判定の標準偏差しきい値です。",
                ),
                io.Float.Input(
                    "tail_mean_threshold",
                    default=0.1,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                    tooltip="末尾判定の平均値しきい値です。",
                ),
            ],
            outputs=[
                IO_TRIM_TAIL_CONFIG.Output(display_name="irodori_trim_tail_config"),
            ],
        )

    @classmethod
    def execute(cls, tail_window_size: int, tail_std_threshold: float, tail_mean_threshold: float):
        return io.NodeOutput(
            {
                "tail_window_size": int(tail_window_size),
                "tail_std_threshold": float(tail_std_threshold),
                "tail_mean_threshold": float(tail_mean_threshold),
            }
        )
