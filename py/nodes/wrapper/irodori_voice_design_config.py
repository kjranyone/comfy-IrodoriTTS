from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_VOICE_DESIGN_CONFIG


class IrodoriVoiceDesignConfig(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "VoiceDesignConfig"),
            display_name="IrodoriTTS VoiceDesign Config",
            category=CATEGORY,
            inputs=[
                io.String.Input(
                    "caption",
                    multiline=True,
                    tooltip="声質・話速・感情・話し方の説明文です。v4.1では参照音声と併用できます。v2 VoiceDesignモデルでは参照音声は無視されます。",
                ),
                io.Int.Input(
                    "max_caption_len",
                    default=0,
                    min=0,
                    max=4096,
                    tooltip="caption token長の上限です。0ならチェックポイント既定値を使います。",
                ),
            ],
            outputs=[
                IO_VOICE_DESIGN_CONFIG.Output(display_name="irodori_voice_design_config"),
            ],
        )

    @classmethod
    def execute(cls, caption: str, max_caption_len: int):
        return io.NodeOutput(
            {
                "caption": str(caption).strip() or None,
                "max_caption_len": None if max_caption_len <= 0 else int(max_caption_len),
            }
        )
