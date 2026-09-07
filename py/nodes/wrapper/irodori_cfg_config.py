from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_CFG_CONFIG, positive_or_none


class IrodoriCFGConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "CFGConfig"),
            display_name="IrodoriTTS CFG Config",
            category=CATEGORY,
            inputs=[
                io.Combo.Input(
                    "cfg_guidance_mode",
                    options=["independent", "joint", "alternating"],
                    default="independent",
                    tooltip="CFGの条件合成方式です。通常はindependentを使用します。",
                ),
                io.Float.Input(
                    "cfg_scale_text",
                    default=3.0,
                    min=0.0,
                    max=10.0,
                    step=0.1,
                    tooltip="テキスト条件のCFG強度です。上げるほどテキスト追従が強くなります。",
                ),
                io.Float.Input(
                    "cfg_scale_speaker",
                    default=5.0,
                    min=0.0,
                    max=10.0,
                    step=0.1,
                    tooltip="参照話者条件のCFG強度です。上げるほど話者性が強くなります。",
                ),
                io.Float.Input(
                    "cfg_scale_caption",
                    default=3.0,
                    min=0.0,
                    max=10.0,
                    step=0.1,
                    tooltip="キャプション条件のCFG強度です。上げるほどキャプション追従が強くなります。",
                ),
                io.Float.Input(
                    "cfg_scale_override",
                    default=0.0,
                    min=0.0,
                    max=10.0,
                    step=0.1,
                    tooltip="全条件に共通のCFG強度です。0なら個別scaleを使用し、jointではcfg_scale_textを共通強度とみなします。",
                ),
                io.Float.Input(
                    "cfg_min_t",
                    default=0.5,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    tooltip="CFGを適用する拡散時刻の下限です。",
                ),
                io.Float.Input(
                    "cfg_max_t",
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    step=0.05,
                    tooltip="CFGを適用する拡散時刻の上限です。",
                ),
            ],
            outputs=[
                IO_CFG_CONFIG.Output(display_name="irodori_cfg_config"),
            ],
        )

    @classmethod
    def execute(
        cls,
        cfg_guidance_mode: str,
        cfg_scale_text: float,
        cfg_scale_speaker: float,
        cfg_scale_caption: float,
        cfg_scale_override: float,
        cfg_min_t: float,
        cfg_max_t: float,
    ):
        mode = str(cfg_guidance_mode)
        common = positive_or_none(float(cfg_scale_override))
        if common is None and mode.strip().lower() == "joint":
            common = float(cfg_scale_text)

        return io.NodeOutput(
            {
                "cfg_guidance_mode": mode,
                "cfg_scale_text": float(cfg_scale_text),
                "cfg_scale_speaker": float(cfg_scale_speaker),
                "cfg_scale_caption": float(cfg_scale_caption),
                "cfg_scale_override": common,
                "cfg_min_t": float(cfg_min_t),
                "cfg_max_t": float(cfg_max_t),
            }
        )
