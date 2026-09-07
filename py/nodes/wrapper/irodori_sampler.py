import sys

import comfy.utils
import torch
from comfy_api.latest import io

from ...modules.irodori_tts.inference_runtime import (
    RuntimeKey,
    SamplingRequest,
    clear_cached_runtime,
    get_cached_runtime,
    offload_cached_runtime,
)
from ...node_utils import node_id
from .irodori_common import (
    CATEGORY,
    IO_CFG_CONFIG,
    IO_DURATION_CONFIG,
    IO_LORA_STACK,
    IO_MODEL_CONFIG,
    IO_REF_CONFIG,
    IO_RESCALE_CONFIG,
    IO_SCHEDULE_CONFIG,
    IO_TRIM_TAIL_CONFIG,
    IO_VOICE_DESIGN_CONFIG,
    positive_or_none,
)


def _build_runtime_key(model_config: dict) -> RuntimeKey:
    return RuntimeKey(
        checkpoint=str(model_config["checkpoint"]),
        model_device=str(model_config.get("model_device", "cuda")),
        codec_repo=str(model_config["codec_repo"]),
        model_precision=str(model_config.get("model_precision", "fp32")),
        codec_device=str(model_config.get("codec_device", "cpu")),
        codec_precision=str(model_config.get("codec_precision", "fp32")),
        enable_watermark=bool(model_config.get("enable_watermark", False)),
        silentcipher_watermark_enabled=bool(
            model_config.get("silentcipher_watermark_enabled", False)
        ),
        compile_model=bool(model_config.get("compile_model", False)),
        compile_dynamic=bool(model_config.get("compile_dynamic", False)),
    )


def _resolve_cfg_override(cfg: dict, guidance_mode: str, scale_text: float):
    override = cfg.get("cfg_scale_override", None)
    if override is None and guidance_mode.strip().lower() == "joint":
        override = scale_text
    return override


class IrodoriTTSSampler(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "Sampler"),
            display_name="IrodoriTTS Sampler",
            category=CATEGORY,
            inputs=[
                IO_MODEL_CONFIG.Input(
                    "model_config",
                    display_name="irodori_model_config",
                    tooltip="IrodoriTTS Model Loaderの出力を接続します。",
                ),
                io.String.Input(
                    "text",
                    multiline=True,
                    tooltip="読み上げるテキストです。絵文字注釈や改行を含められます。",
                ),
                io.Int.Input(
                    "seed",
                    default=0,
                    min=0,
                    max=sys.maxsize,
                    tooltip="生成シードです。同じ値で同じ結果を再現します。",
                ),
                io.Float.Input(
                    "seconds",
                    default=0.0,
                    min=0.0,
                    max=120.0,
                    step=0.5,
                    tooltip="生成する音声長です。0なら自動秒数推定(推定器のないモデルは30秒)。",
                ),
                io.Int.Input(
                    "num_steps",
                    default=40,
                    min=1,
                    max=120,
                    tooltip="サンプリングステップ数です。",
                ),
                IO_LORA_STACK.Input(
                    "lora_stack",
                    optional=True,
                    tooltip="IrodoriTTS LoRA Stackの出力です。未接続ならLoRAなしで生成します。",
                ),
                IO_REF_CONFIG.Input(
                    "ref_config",
                    optional=True,
                    tooltip="参照音声または話者埋め込みの設定です。未接続なら参照なしで生成します。",
                ),
                IO_VOICE_DESIGN_CONFIG.Input(
                    "voice_design_config",
                    optional=True,
                    tooltip="キャプション設定です。v4.1では参照音声と併用できます。",
                ),
                IO_CFG_CONFIG.Input(
                    "cfg_config",
                    optional=True,
                    tooltip="CFGの詳細設定です。未接続なら標準値を使用します。",
                ),
                IO_DURATION_CONFIG.Input(
                    "duration_config",
                    optional=True,
                    tooltip="自動秒数推定の詳細設定です。未接続なら標準値を使用します。",
                ),
                IO_RESCALE_CONFIG.Input(
                    "rescale_config",
                    optional=True,
                    tooltip="rescaleやspeaker K/V補正の設定です。未接続なら無効です。",
                ),
                IO_SCHEDULE_CONFIG.Input(
                    "schedule_config",
                    optional=True,
                    tooltip="RFサンプリングの時刻スケジュール設定です。未接続ならlinearを使用します。",
                ),
                io.Int.Input(
                    "batch_size",
                    default=1,
                    min=1,
                    max=16,
                    tooltip="同一条件で同時生成する候補数です。AUDIOのbatchに格納します。",
                ),
                io.Combo.Input(
                    "decode_mode",
                    options=["sequential", "batch"],
                    default="sequential",
                    tooltip="codecデコード方式です。batchは速い場合がありますがVRAMを多く使います。",
                ),
                io.Boolean.Input(
                    "context_kv_cache",
                    default=True,
                    tooltip="コンテキストK/Vキャッシュを使用します。通常は有効です。",
                ),
                io.Int.Input(
                    "max_text_len",
                    default=0,
                    min=0,
                    max=4096,
                    tooltip="テキストtoken長の上限です。0ならチェックポイント既定値を使います。",
                ),
                io.Boolean.Input(
                    "trim_tail",
                    default=True,
                    tooltip="末尾の無音や平坦化した部分を推定して切り詰めます。",
                ),
                IO_TRIM_TAIL_CONFIG.Input(
                    "trim_tail_config",
                    optional=True,
                    tooltip="末尾切り詰め判定の詳細設定です。未接続なら標準値を使用します。",
                ),
            ],
            outputs=[
                io.Audio.Output(display_name="audio"),
            ],
        )

    @classmethod
    def execute(
        cls,
        model_config: dict,
        text: str,
        seed: int,
        seconds: float,
        num_steps: int,
        batch_size: int,
        decode_mode: str,
        context_kv_cache: bool,
        max_text_len: int,
        trim_tail: bool,
        lora_stack: list | None = None,
        ref_config: dict | None = None,
        voice_design_config: dict | None = None,
        cfg_config: dict | None = None,
        duration_config: dict | None = None,
        rescale_config: dict | None = None,
        schedule_config: dict | None = None,
        trim_tail_config: dict | None = None,
    ):
        ref = dict(ref_config or {})
        caption_cfg = dict(voice_design_config or {})
        cfg = dict(cfg_config or {})
        duration = dict(duration_config or {})
        rescale = dict(rescale_config or {})
        schedule = dict(schedule_config or {})
        tail = dict(trim_tail_config or {})

        ref_wavs = [str(p) for p in ref.get("ref_wavs") or [] if str(p).strip()]
        ref_latents = [str(p) for p in ref.get("ref_latents") or [] if str(p).strip()]
        ref_embed = ref.get("ref_embed", None)

        guidance_mode = str(cfg.get("cfg_guidance_mode", "independent"))
        scale_text = float(cfg.get("cfg_scale_text", 3.0))
        scale_speaker = float(cfg.get("cfg_scale_speaker", 5.0))
        scale_caption = float(
            cfg.get("cfg_scale_caption", caption_cfg.get("cfg_scale_caption", 3.0))
        )

        adapters = [
            (str(entry["path"]), float(entry.get("strength", 1.0)))
            for entry in (lora_stack or [])
            if entry.get("path")
        ]

        request = SamplingRequest(
            text=str(text),
            caption=caption_cfg.get("caption", None),
            ref_wavs=ref_wavs,
            ref_latents=ref_latents,
            ref_embed=ref_embed,
            no_ref=bool(ref.get("no_ref", not (ref_wavs or ref_latents or ref_embed))),
            ref_normalize_db=ref.get("ref_normalize_db", None),
            ref_ensure_max=bool(ref.get("ref_ensure_max", True)),
            num_candidates=int(batch_size),
            decode_mode=str(decode_mode),
            seconds=positive_or_none(float(seconds)),
            duration_scale=float(duration.get("duration_scale", 1.0)),
            min_seconds=float(duration.get("min_seconds", 0.5)),
            max_seconds=float(duration.get("max_seconds", 30.0)),
            max_ref_seconds=positive_or_none(float(ref.get("max_ref_seconds") or 0.0)),
            max_text_len=positive_or_none(int(max_text_len)),
            max_caption_len=caption_cfg.get("max_caption_len", None),
            num_steps=int(num_steps),
            cfg_scale_text=scale_text,
            cfg_scale_caption=scale_caption,
            cfg_scale_speaker=scale_speaker,
            cfg_guidance_mode=guidance_mode,
            cfg_scale=_resolve_cfg_override(cfg, guidance_mode, scale_text),
            cfg_min_t=float(cfg.get("cfg_min_t", 0.5)),
            cfg_max_t=float(cfg.get("cfg_max_t", 1.0)),
            truncation_factor=rescale.get("truncation_factor", None),
            rescale_k=rescale.get("rescale_k", None),
            rescale_sigma=rescale.get("rescale_sigma", None),
            context_kv_cache=bool(context_kv_cache),
            speaker_kv_scale=rescale.get("speaker_kv_scale", None),
            speaker_kv_min_t=rescale.get("speaker_kv_min_t", 0.9),
            speaker_kv_max_layers=rescale.get("speaker_kv_max_layers", None),
            speaker_uncond_mode=str(ref.get("speaker_uncond_mode", "mask")),
            seed=int(seed),
            t_schedule_mode=str(schedule.get("t_schedule_mode", "linear")),
            sway_coeff=float(schedule.get("sway_coeff", -1.0)),
            trim_tail=bool(trim_tail),
            tail_window_size=int(tail.get("tail_window_size", 20)),
            tail_std_threshold=float(tail.get("tail_std_threshold", 0.05)),
            tail_mean_threshold=float(tail.get("tail_mean_threshold", 0.1)),
            lora_adapters=tuple(adapters),
        )

        runtime, _ = get_cached_runtime(_build_runtime_key(model_config))

        progress = comfy.utils.ProgressBar(int(num_steps))
        policy = str(model_config.get("runtime_cache_policy", "offload_after_use"))
        try:
            result = runtime.synthesize(
                request,
                log_fn=print,
                progress_callback=lambda current, total: progress.update_absolute(
                    int(current), int(total)
                ),
            )
        finally:
            if policy == "unload_after_use":
                clear_cached_runtime()
            elif policy == "offload_after_use":
                offload_cached_runtime()
            elif policy != "keep_gpu":
                print(f"[IrodoriTTS] unknown runtime_cache_policy={policy!r}; keeping runtime on GPU.")

        # Pad candidates to equal length so they stack into one AUDIO batch.
        audios = result.audios or [result.audio]
        longest = max(int(audio.shape[-1]) for audio in audios)
        batch = []
        for audio in audios:
            if audio.dim() != 2:
                raise ValueError(
                    f"expected generated audio shape [channels, samples], got {tuple(audio.shape)}"
                )
            if int(audio.shape[-1]) < longest:
                audio = torch.nn.functional.pad(audio, (0, longest - int(audio.shape[-1])))
            batch.append(audio)

        waveform = torch.stack(batch, dim=0)
        return io.NodeOutput({"waveform": waveform, "sample_rate": result.sample_rate})
