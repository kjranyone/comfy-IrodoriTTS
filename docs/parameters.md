# comfy-IrodoriTTS Parameters

この文書は、comfy-IrodoriTTSで提供される各ノード入力の説明です。

Irodori-TTS本体のCLI引数とは名前や分割単位が異なります。ComfyUIでは、基本生成に必要な入力を`IrodoriTTS Sampler`に置き、詳細設定は用途ごとのConfigノードとして接続します。

## 基本方針

- `IrodoriTTS Model Loader`でモデルと実行デバイスを選びます。
- `IrodoriTTS Sampler`でテキスト、秒数、ステップ数、seedを指定して生成します。
- 参照音声、話者埋め込み、キャプション、LoRA、各種Configは必要な場合だけ追加します。
- Configノードを接続しない場合は、Sampler内部の標準値が使われます。

## IrodoriTTS Model Loader

IrodoriTTSのチェックポイントと実行設定をまとめ、`irodori_model_config`を出力します。

| Input | Default | 説明 |
| --- | --- | --- |
| `model` | checkpoint一覧 | 使用するIrodoriTTSチェックポイントです。ComfyUIの`models/checkpoints`に配置したファイルから選びます。 |
| `model_device` | 環境依存 | TTSモデルを実行するデバイスです。通常は`cuda`を使用します。 |
| `model_precision` | 環境依存 | TTSモデルの計算精度です。GPUでは`bf16`、互換性重視では`fp32`を選びます。 |
| `codec_device` | 環境依存 | codecを実行するデバイスです。VRAMを節約したい場合は`cpu`を選びます。 |
| `codec_precision` | 環境依存 | codecの計算精度です。互換性重視では`fp32`を選びます。 |
| `enable_watermark` | `False` | codec側のウォーターマーク処理を有効化します。通常は無効のままで構いません。 |
| `enable_silentcipher` | `False` | SilentCipherによる音声ウォーターマークを有効化します。別途`pip install silentcipher`が必要です。 |
| `compile_model` | `False` | `torch.compile`でTTSモデルをコンパイルします。初回生成は遅くなりますが、環境によっては以後の生成が速くなります。 |
| `compile_dynamic` | `False` | `torch.compile`のdynamicモードを使います。入力長が変わる運用で試すための設定です。 |
| `runtime_cache_policy` | `offload_after_use` | 生成後のruntime保持方針です。`offload_after_use`はキャッシュを残してCPUへ退避、`keep_gpu`はGPU上に保持、`unload_after_use`は生成後に完全破棄します。 |

チェックポイントの`latent_dim`に応じて、使用するcodecは内部で自動選択されます。

## IrodoriTTS Sampler

テキストから音声を生成し、ComfyUI標準の`AUDIO`を出力します。

### Required Inputs

| Input | Default | 説明 |
| --- | --- | --- |
| `model_config` | - | `IrodoriTTS Model Loader`の出力を接続します。 |
| `text` | - | 読み上げるテキストです。絵文字注釈(v4.1)や改行を含めた長文も指定できます。 |
| `seed` | `0` | 生成シードです。同じ条件で別候補を生成したい場合は値を変えます。 |
| `seconds` | `0.0` | 生成する音声長です。`0`を指定すると自動秒数推定を使います(v4.1/v3)。v1/v2モデルや推定器がない場合、`0`は30秒にフォールバックします。 |
| `num_steps` | `40` | サンプリングステップ数です。大きいほど時間がかかりますが、品質や安定性が変わる場合があります。 |

### Optional Config Inputs

| Input | 接続するノード | 説明 |
| --- | --- | --- |
| `lora_stack` | `IrodoriTTS LoRA Stack` | IrodoriTTS向けLoRAアダプタを適用します。 |
| `ref_config` | `IrodoriTTS Reference Audio` / `IrodoriTTS Speaker Embedding` | 参照音声または話者埋め込みによる話者・雰囲気の指定を行います。 |
| `voice_design_config` | `IrodoriTTS VoiceDesign Config` | 声質・話し方キャプションを指定します。v4.1では参照音声と併用できます。 |
| `cfg_config` | `IrodoriTTS CFG Config` | テキスト、話者、キャプション条件のCFG強度と適用時刻を指定します。 |
| `duration_config` | `IrodoriTTS Duration Config` | 自動秒数推定を補正します。Samplerの`seconds = 0`時に意味があります。 |
| `rescale_config` | `IrodoriTTS Rescale Config` | 潜在の振れ幅やspeaker K/V補正を指定します。 |
| `schedule_config` | `IrodoriTTS Schedule Config` | RFサンプリングの時刻スケジュールを指定します。 |
| `trim_tail_config` | `IrodoriTTS Trim Tail Config` | 末尾切り詰め判定のしきい値を指定します。Samplerの`trim_tail`が有効なときに使われます。 |

### Other Inputs

| Input | Default | 説明 |
| --- | --- | --- |
| `batch_size` | `1` | 同一条件で生成する候補数です。大きくするとVRAM使用量が増えます。 |
| `decode_mode` | `sequential` | codecデコード方式です。`sequential`は省VRAM、`batch`は一括デコードです。 |
| `context_kv_cache` | `True` | コンテキストK/Vキャッシュを使います。通常は有効のままで構いません。 |
| `max_text_len` | `0` | テキストtoken長の上限です。`0`の場合はチェックポイント側の標準値を使います。 |
| `trim_tail` | `True` | 末尾の無音や平坦化した部分を切り詰めます。詳細判定は`trim_tail_config`で調整できます。 |

## IrodoriTTS Reference Audio

参照音声設定を作成し、Samplerの`ref_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `prev` | 未接続 | 前段の`IrodoriTTS Reference Audio`出力です。接続すると参照を接続順に連結します(v4.1向け)。 |
| `audio` | input一覧 | ComfyUIの`input`フォルダ内の音声または動画ファイルです。 |
| `ref_latent` | `None` | 事前計算済みの参照潜在(`.pt`)をinputフォルダから選択します。音声ファイルとは併用できません。 |
| `ref_normalize_db` | `-16.0` | 参照音声のラウドネス正規化ターゲット(dB)です。`0`で無効になります。無効時はピーク安全性のためのスケールダウンのみ行われます。 |
| `max_ref_seconds` | `0.0` | 参照として使う最大秒数です。`0`ならチェックポイント既定値(v4.1では120秒)を使います。 |

動画ファイルを指定した場合は、ffmpegで音声を抽出します。`imageio-ffmpeg`またはシステムの`ffmpeg`が必要です。

## IrodoriTTS Speaker Embedding

Speaker Inversionで学習した話者埋め込み設定を作成し、Samplerの`ref_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `speaker_embedding` | `None` | `models/embeddings`に配置した`*.speaker.safetensors`を選びます。参照音声の代わりに話者を指定します。 |
| `speaker_uncond_mode` | `mask` | CFGの無条件話者埋め込みの作り方です。`mask`はゼロ埋め(省VRAM)、`noise`は参照埋め込みと同分散のノイズで置き換えます。 |

参照音声(`IrodoriTTS Reference Audio`)との併用はできません。

## IrodoriTTS VoiceDesign Config

キャプション設定を作成し、Samplerの`voice_design_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `caption` | - | 声質・話し方・感情などの説明文です。v4.1では参照音声と併用できます。v2 VoiceDesignモデルではキャプションのみが使われます。 |
| `max_caption_len` | `0` | キャプションtoken長の上限です。`0`ならチェックポイント既定値を使います。 |

キャプション条件の強度は`IrodoriTTS CFG Config`の`cfg_scale_caption`で調整します。

## IrodoriTTS LoRA Stack

IrodoriTTS向けLoRAアダプタをスタックし、Samplerの`lora_stack`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `prev` | 未接続 | 前段の`IrodoriTTS LoRA Stack`出力です。複数LoRAを使う場合に接続します。 |
| `lora` | `None` | 追加するLoRAアダプタです。`models/loras`内の`adapter_config.json`を含むフォルダから選びます。 |
| `strength` | `1.0` | LoRAの適用強度です。`1.0`が標準、`0.0`は実質無効です。 |

## IrodoriTTS CFG Config

CFGの詳細設定を作成し、Samplerの`cfg_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `cfg_guidance_mode` | `independent` | CFGの条件合成方式です。`independent`、`joint`、`alternating`から選びます。 |
| `cfg_scale_text` | `3.0` | 読み上げテキスト条件のCFG強度です。大きいほどテキスト追従が強くなります。 |
| `cfg_scale_speaker` | `5.0` | 参照話者条件のCFG強度です。大きいほど参照音声の話者性が強くなります。 |
| `cfg_scale_caption` | `3.0` | キャプション条件のCFG強度です。大きいほどキャプションへの追従が強くなります。 |
| `cfg_scale_override` | `0.0` | 全CFG条件に共通の強度を指定します。`0`なら個別scaleを使用し、`joint`では`cfg_scale_text`を共通強度として使用します。 |
| `cfg_min_t` | `0.5` | CFGを適用する拡散時刻の下限です。 |
| `cfg_max_t` | `1.0` | CFGを適用する拡散時刻の上限です。 |

`cfg_guidance_mode = joint`では有効なCFG条件の強度が同一である必要があります。まずは未接続の標準値で試し、必要に応じて調整してください。

## IrodoriTTS Duration Config

自動秒数推定を補正し、Samplerの`duration_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `duration_scale` | `1.0` | 自動推定された秒数の倍率です。`1.0`より大きいと長く、小さいと短くなります。 |
| `min_seconds` | `0.5` | 自動推定で許可する最短秒数です。 |
| `max_seconds` | `30.0` | 自動推定で許可する最長秒数です。`seconds`を手動指定した場合もこの範囲に丸めます。 |

Samplerの`seconds`が`0`のときに自動推定が有効になります。

## IrodoriTTS Rescale Config

潜在の振れ幅や話者条件を補正する詳細設定を作成し、Samplerの`rescale_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `truncation_factor` | `0` | 潜在の振れ幅を抑える係数です。`0`以下で無効になります。 |
| `rescale_k` | `0` | Rescale補正の強さです。`rescale_sigma`とセットで指定します。 |
| `rescale_sigma` | `0` | Rescale補正のsigmaです。`rescale_k`とセットで指定します。 |
| `speaker_kv_scale` | `0` | 話者条件K/Vの強調倍率です。`0`以下で無効になります。 |
| `speaker_kv_min_t` | `0.9` | speaker K/V補正を適用し始める拡散時刻です。 |
| `speaker_kv_max_layers` | `-1` | speaker K/V補正を適用する最大レイヤー数です。`-1`なら全レイヤーが対象になります。 |

## IrodoriTTS Schedule Config

RFサンプリングの時刻スケジュール設定を作成し、Samplerの`schedule_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `schedule_mode` | `linear` | `linear`または`sway`を選びます。 |
| `sway_coeff` | `-1.0` | `sway`時のスケジュール係数です。 |

未接続時は`linear`で生成します。`sway`は少ないステップ数での生成と相性が良いです。

## IrodoriTTS Trim Tail Config

末尾切り詰め判定の詳細設定を作成し、Samplerの`trim_tail_config`へ接続します。

| Input | Default | 説明 |
| --- | --- | --- |
| `tail_window_size` | `20` | 末尾判定に使う潜在窓サイズです。 |
| `tail_std_threshold` | `0.05` | 標準偏差しきい値です。 |
| `tail_mean_threshold` | `0.1` | 平均値しきい値です。 |

Samplerの`trim_tail`が有効なときに使用されます。
