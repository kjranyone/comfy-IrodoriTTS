from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_SCHEDULE_CONFIG


class IrodoriScheduleConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "ScheduleConfig"),
            display_name="IrodoriTTS Schedule Config",
            category=CATEGORY,
            inputs=[
                io.Combo.Input(
                    "schedule_mode",
                    options=["linear", "sway"],
                    default="linear",
                    tooltip="RFサンプリングの時刻スケジュールです。swayは少ないステップ数と相性が良いです。",
                ),
                io.Float.Input(
                    "sway_coeff",
                    default=-1.0,
                    min=-5.0,
                    max=5.0,
                    step=0.1,
                    tooltip="sway選択時のスケジュール係数です。",
                ),
            ],
            outputs=[
                IO_SCHEDULE_CONFIG.Output(display_name="irodori_schedule_config"),
            ],
        )

    @classmethod
    def execute(cls, schedule_mode: str, sway_coeff: float):
        return io.NodeOutput(
            {
                "t_schedule_mode": str(schedule_mode),
                "sway_coeff": float(sway_coeff),
            }
        )
