import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import folder_paths
from comfy_api.latest import io

from ...node_utils import node_id
from .irodori_common import CATEGORY, IO_REF_CONFIG, positive_or_none

VIDEO_SUFFIXES = {
    ".3gp", ".avi", ".flv", ".m4v", ".mkv", ".mov", ".mp4",
    ".mpeg", ".mpg", ".webm", ".wmv",
}


def _is_video(path: str | os.PathLike[str]) -> bool:
    return Path(path).suffix.lower() in VIDEO_SUFFIXES


def _file_digest(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def _extract_audio_track(video_path: str) -> str:
    """Extract a mono 16-bit PCM wav from a video file, cached by content hash."""
    ffmpeg = _find_ffmpeg()
    if ffmpeg is None:
        raise RuntimeError(
            "video reference requires imageio-ffmpeg or a system ffmpeg; "
            "install requirements.txt or use an audio file"
        )

    out_dir = Path(folder_paths.get_temp_directory()) / "irodori_tts" / "reference_audio"
    out_dir.mkdir(parents=True, exist_ok=True)
    wav_path = out_dir / f"{_file_digest(video_path)}.wav"
    if wav_path.exists():
        return str(wav_path)

    partial = wav_path.with_suffix(".partial.wav")
    result = subprocess.run(
        [
            ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-i", video_path, "-vn", "-ac", "1", "-c:a", "pcm_s16le", str(partial),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip()
        raise RuntimeError(f"ffmpeg failed to extract audio from {video_path}: {detail or 'unknown error'}")

    partial.replace(wav_path)
    print(f"[IrodoriTTS] extracted reference audio: {video_path} -> {wav_path}", flush=True)
    return str(wav_path)


def _input_audio_files() -> list[str]:
    input_dir = folder_paths.get_input_directory()
    files = folder_paths.filter_files_content_types(os.listdir(input_dir), ["audio", "video"])
    return sorted(files)


def _input_latent_files() -> list[str]:
    input_dir = Path(folder_paths.get_input_directory())
    return sorted(
        path.name for path in input_dir.iterdir() if path.is_file() and path.suffix == ".pt"
    )


class IrodoriReferenceAudio(io.ComfyNode):
    @classmethod
    def define_schema(cls):
        return io.Schema(
            node_id=node_id("IrodoriTTS", "ReferenceAudio"),
            display_name="IrodoriTTS Reference Audio",
            category=CATEGORY,
            inputs=[
                IO_REF_CONFIG.Input(
                    "prev",
                    optional=True,
                    tooltip="前段のIrodoriTTS Reference Audioを接続すると、参照を接続順に連結します(v4.1向け)。",
                ),
                io.Combo.Input(
                    "audio",
                    options=_input_audio_files(),
                    upload=io.UploadType.audio,
                    tooltip="話者参照に使う音声ファイルをinputフォルダから選択します。",
                ),
                io.Combo.Input(
                    "ref_latent",
                    options=["None"] + _input_latent_files(),
                    tooltip="事前計算済みの参照潜在(.pt)をinputフォルダから選択します。音声ファイルとの併用はできません。",
                ),
                io.Float.Input(
                    "ref_normalize_db",
                    default=-16.0,
                    min=-60.0,
                    max=0.0,
                    step=1.0,
                    tooltip="参照音声のラウドネス正規化ターゲット(dB)です。0なら無効にします。",
                ),
                io.Float.Input(
                    "max_ref_seconds",
                    default=0.0,
                    min=0.0,
                    max=120.0,
                    step=1.0,
                    tooltip="参照として使う最大秒数です。0ならチェックポイント既定値(v4.1は120秒)を使います。",
                ),
                io.Custom("AUDIO_UI").Input("audioUI", optional=True),
                io.Custom("AUDIOUPLOAD").Input("upload", optional=True),
            ],
            outputs=[
                IO_REF_CONFIG.Output(display_name="irodori_ref_config"),
            ],
        )

    @classmethod
    def execute(
        cls,
        audio: str,
        ref_latent: str,
        ref_normalize_db: float,
        max_ref_seconds: float,
        prev: dict | None = None,
        audioUI=None,
        upload=None,
    ):
        prev = dict(prev or {})

        if ref_latent and ref_latent != "None":
            latent_path = str(Path(folder_paths.get_input_directory()) / ref_latent)
            latents = [str(p) for p in prev.get("ref_latents") or []]
            latents.append(latent_path)
            return io.NodeOutput(
                {
                    "ref_wavs": list(prev.get("ref_wavs") or []),
                    "ref_latents": latents,
                    "no_ref": False,
                    "ref_normalize_db": float(ref_normalize_db) if ref_normalize_db < 0 else None,
                    "ref_ensure_max": True,
                    "max_ref_seconds": positive_or_none(float(max_ref_seconds)),
                }
            )

        path = folder_paths.get_annotated_filepath(audio)
        if _is_video(path):
            path = _extract_audio_track(path)

        clips = [str(p) for p in prev.get("ref_wavs") or []]
        clips.append(str(path))

        return io.NodeOutput(
            {
                "ref_wavs": clips,
                "ref_latents": list(prev.get("ref_latents") or []),
                "no_ref": False,
                "ref_normalize_db": float(ref_normalize_db) if ref_normalize_db < 0 else None,
                "ref_ensure_max": True,
                "max_ref_seconds": positive_or_none(float(max_ref_seconds)),
            }
        )

    @classmethod
    def fingerprint_inputs(cls, **kwargs):
        path = folder_paths.get_annotated_filepath(kwargs.get("audio"))
        return _file_digest(path)

    @classmethod
    def validate_inputs(cls, **kwargs):
        audio = kwargs.get("audio")
        if not folder_paths.exists_annotated_filepath(audio):
            return f"audio file not found in input directory: {audio}"
        path = folder_paths.get_annotated_filepath(audio)
        if _is_video(path) and _find_ffmpeg() is None:
            return "video reference requires imageio-ffmpeg or a system ffmpeg; use an audio file instead"
        return True
