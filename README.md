# comfy-IrodoriTTS

ComfyUIで[Irodori-TTS](https://github.com/Aratako/Irodori-TTS)による日本語音声合成を行うカスタムノードです。

[Irodori-TTS v4.1](https://huggingface.co/Aratako/Irodori-TTS-v4.1-Small)のコードベースに対応し、v2/v3系チェックポイントも引き続き使用できます。Flow Matching (Rectified Flow DiT) によるテキストからの音声生成に加えて、参照音声・キャプション・話者埋め込み・LoRAによる表現制御をノードグラフ上で組み合わせられます。

## 主な機能

- Irodori-TTS v4.1 / v3 / v2チェックポイントの読み込み(torchao量子化版にも対応)
- テキスト読み上げ音声の生成(自動秒数推定、手動秒数指定)
- 参照音声による話者クローン(音声・動画ファイルに対応、複数クリップの連結)
- キャプションによる声質・感情・話し方の指定(v4.1では参照音声と同時に使用可能)
- Speaker Inversion話者埋め込み(`*.speaker.safetensors`)による話者固定
- テキスト埋め込み絵文字による表現制御(45種のパレットUI同梱)
- PEFT LoRAアダプタの適用(複数スタック・強度調整)
- CFG / Duration / Rescale / Schedule / Trim Tail / speaker K/V補正の詳細設定

## インストール

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/kjranyone/comfy-IrodoriTTS.git
cd ..
pip install -r custom_nodes/comfy-IrodoriTTS/requirements.txt
```

ComfyUIを再起動すると、カテゴリ `kjranyone/IrodoriTTS` にノードが追加されます。

## モデルの配置

チェックポイントを`models/checkpoints`に配置します。v4.1はHugging Faceのリポジトリ内容をそのまま置くのが確実です(`model.safetensors`と同階層の`tokenizer/`を合わせて配置すると、tokenizerの追加ダウンロードが不要になります)。

```text
ComfyUI/models/checkpoints/Irodori-TTS-v4.1-Small/model.safetensors
ComfyUI/models/checkpoints/Irodori-TTS-v4.1-Small/tokenizer/
```

対応チェックポイント:

- [Aratako/Irodori-TTS-v4.1-Small](https://huggingface.co/Aratako/Irodori-TTS-v4.1-Small)
- [Aratako/Irodori-TTS-v4.1-Small-Quantized](https://huggingface.co/Aratako/Irodori-TTS-v4.1-Small-Quantized)(量子化版。`int8-weight-only`等のサブフォルダを配置。`pip install torchao`が必要)
- [phasefield-audio/Irodori-TTS-v4.1-Anime](https://huggingface.co/phasefield-audio/Irodori-TTS-v4.1-Anime)(v4.1-Smallのアニメ調ファインチューン。量子化サブフォルダ同梱。本体と独立にアノテーションされた学習データのため、caption・絵文字の挙動が本家と異なる場合があります)
- [Aratako/Irodori-TTS-500M-v3](https://huggingface.co/Aratako/Irodori-TTS-500M-v3)
- [Aratako/Irodori-TTS-500M-v2](https://huggingface.co/Aratako/Irodori-TTS-500M-v2) / [v2-VoiceDesign](https://huggingface.co/Aratako/Irodori-TTS-500M-v2-VoiceDesign)

チェックポイントの`latent_dim`に応じてcodecが自動選択されます(`32`なら`Aratako/Semantic-DACVAE-Japanese-32dim`、`128`なら`facebook/dacvae-watermarked`)。codecとtokenizerは初回ロード時にHugging Faceから自動ダウンロードされ、ノード内の`data`ディレクトリに保存されます。

## 使い方

### 基本

最小構成は `IrodoriTTS Model Loader` → `IrodoriTTS Sampler` の2ノードです。`text`に読み上げる文章を入力し、`num_steps`でステップ数、`seed`で乱数シードを指定します。`seconds = 0`で自動秒数推定(v4.1/v3。v1/v2は30秒固定)。

### 参照音声(話者クローン)

`IrodoriTTS Reference Audio`を`Sampler / ref_config`に接続します。音声に加えて動画ファイルも指定でき、動画はffmpegで音声を抽出します。

`prev`に前段の`Reference Audio`を接続すると、複数クリップを接続順に連結できます。v4.1では同一話者の短いクリップを複数組み合わせる使い方が推奨されています(合計約30秒で効果の大半が得られます)。`max_ref_seconds = 0`でチェックポイント既定の上限(v4.1は120秒)になります。

`ref_normalize_db`で参照音声のラウドネス正規化ターゲットを調整できます(規定-16dB、`0`で無効)。事前計算済みの参照潜在(`.pt`)を使う場合は`ref_latent`から選択できます(音声ファイルとの併用は不可)。

### キャプション(VoiceDesign)

`IrodoriTTS VoiceDesign Config`を`Sampler / voice_design_config`に接続します。`caption`に声質・話速・感情・話し方を文章で記述します。

v4.1ではキャプションと参照音声を同時に接続でき、話者を参照音声、話し方・感情をキャプションで制御できます。v2 VoiceDesignモデルはキャプションのみで動作し、参照音声は無視されます。

### 話者埋め込み(Speaker Inversion)

`IrodoriTTS Speaker Embedding`を`Sampler / ref_config`に接続します。Speaker Inversion学習で作成した`*.speaker.safetensors`を`models/embeddings`に配置して選択すると、参照音声の代わりに話者埋め込みで話者を固定できます。参照音声との併用はできません。

### LoRA

LoRAアダプタディレクトリ(`adapter_config.json`と`adapter_model.safetensors`を含むフォルダ)を`models/loras`に配置し、`IrodoriTTS LoRA Stack`から選択します。`prev`チェーンで複数LoRAを積み、`strength`で強度を調整できます。

### 絵文字による表現制御

v4.1ではテキスト中に絵文字注釈を埋め込むことで、抑揚や非言語発話(笑い、吐息、間など)を制御できます。

```text
あははっ🤭、それ本当に言ってるの？…😮‍💨まぁ、君らしいけどね。
```

画面右下の😀ボタンで絵文字パレット(45種)を開けます。テキスト欄にカーソルを合わせて絵文字をクリックすると、カーソル位置に挿入されます。

対応絵文字(45種):

| 絵文字 | 効果 | 補足 |
|---|---|---|
| 👂 | 囁き | 耳元の音 |
| 😮‍💨 | 吐息 | 溜息、寝息 |
| ⏸️ | 間 | 沈黙 |
| 🤭 | 笑い | くすくす、含み笑い |
| 🥵 | 喘ぎ | うめき声、唸り声 |
| 📢 | エコー | リバーブ |
| 😏 | からかう | 甘えるように |
| 🥺 | 震え声 | 自信なさげに |
| 🌬️ | 息切れ | 荒い息遣い、呼吸音 |
| 😮 | 息をのむ | Gasp |
| 👅 | 舐める音 | 咀嚼音、水音 |
| 💋 | リップノイズ | Lip smack |
| 🫶 | 優しく | Tenderly |
| 😭 | 泣き声 | 嗚咽、悲しみ |
| 😱 | 悲鳴 | 叫び、絶叫 |
| 😪 | 眠そう | 気だるげに |
| 😴 | 寝言 | いびき |
| ⏩ | 早口 | 一気に、急いで |
| 📞 | 電話越し | スピーカー越し |
| 🐢 | ゆっくり | Slowly |
| 🥤 | 飲み込む | 唾を飲む音 |
| 🤧 | 咳・鼻 | 咳き込み、鼻すすり |
| 😒 | 舌打ち | Tutting |
| 😰 | 慌てる | 動揺、緊張、どもり |
| 😆 | 喜び | 嬉しそうに |
| 💥 | 勢いよく | 力強い勢い |
| 😠 | 怒り | 不満げ、拗ねる |
| 😲 | 驚き | 感嘆 |
| 🥱 | あくび | Yawn |
| 😖 | 苦しげ | Agonizingly |
| 😟 | 心配 | 不安そうに |
| 🫣 | 照れ | 恥ずかしそうに |
| 🙄 | 呆れ | Exasperatedly |
| 😊 | 楽しげ | 嬉しそうに |
| 😎 | 得意げ | 自信ありげに |
| 👌 | 相槌 | 頷く音 |
| 🙏 | 懇願 | お願いするように |
| 🥴 | 酔う | Drunkenly |
| 🎵 | 鼻歌 | Humming |
| 🤐 | 口を塞ぐ | Muffled |
| 😌 | 安堵 | 満足げに |
| 🤔 | 疑問 | Questioning |
| 💪 | 力強く | 力を込めて |
| 👃 | 嗅ぐ音 | 匂いを嗅ぐ音 |
| 📖 | 朗読 | ナレーション |

### ウォーターマーク

`Model Loader`の`enable_silentcipher`で、生成音声へのSilentCipherウォーターマークを有効化できます(別途`pip install silentcipher`が必要)。codec(DACVAE)内蔵のウォーターマークは`enable_watermark`で制御します。どちらも規定では無効です。

## ノード一覧

| ノード | 役割 |
|---|---|
| `IrodoriTTS Model Loader` | チェックポイントと実行デバイス・精度・キャッシュ方針の選択 |
| `IrodoriTTS Sampler` | テキストから音声を生成(`AUDIO`出力) |
| `IrodoriTTS Reference Audio` | 参照音声の指定(チェーンで複数連結) |
| `IrodoriTTS Speaker Embedding` | Speaker Inversion話者埋め込みの指定 |
| `IrodoriTTS VoiceDesign Config` | キャプション(声質・話し方)の指定 |
| `IrodoriTTS LoRA Stack` | LoRAアダプタの選択とスタック |
| `IrodoriTTS CFG Config` | 条件ごとのCFG強度・適用時刻・ガイダンス方式 |
| `IrodoriTTS Duration Config` | 自動秒数推定の倍率・上限・下限 |
| `IrodoriTTS Rescale Config` | truncation・rescale・speaker K/V補正 |
| `IrodoriTTS Schedule Config` | linear / swayサンプリングスケジュール |
| `IrodoriTTS Trim Tail Config` | 末尾無音判定のしきい値 |

各入力の詳細は[docs/parameters.md](docs/parameters.md)を参照してください。

## 生成設定の目安

- `num_steps = 40`から始め、`seconds = 0`(自動推定)を試します。
- swayサンプリング(`Schedule Config`)では`num_steps = 6`程度でも生成できます(`sway_coeff = -1.0`)。
- 音声の末尾が長く残る場合は`trim_tail`を有効にします。
- VRAMが厳しい場合は`codec_device = cpu`、`decode_mode = sequential`、`batch_size = 1`を試します。
- 参照音声の影響が弱い場合は`cfg_scale_speaker`を、テキスト追従が弱い場合は`cfg_scale_text`を少し上げます(上げすぎると音質が崩れることがあります)。
- 量子化チェックポイント(`int8-weight-only`等)でVRAM使用量を削減できます。

## トラブルシューティング

- **モデルが一覧に表示されない**: `models/checkpoints`への配置とComfyUIの再起動を確認してください。
- **動画から参照音声を使えない**: `imageio-ffmpeg`をインストールするか、システムに`ffmpeg`を用意してください。
- **v4.1ロード時にtransformers関連のエラー**: `requirements.txt`の再インストールを確認してください(v4.1は`transformers>=5.12`が必要です)。
- **量子化チェックポイントでエラー**: `pip install torchao`が必要です。
- **メモリ不足**: `batch_size = 1`、`decode_mode = sequential`、`codec_device = cpu`、短い`seconds`、低い`num_steps`の順に試してください。

## クレジット・ライセンス

- [Aratako/Irodori-TTS](https://github.com/Aratako/Irodori-TTS) — 本体アーキテクチャ・学習・推論コード (MIT)
- [iron-mukakin/Emoji-TTS](https://github.com/iron-mukakin/Emoji-TTS) — 派生元のフォーク実装
- [facebookresearch/dacvae](https://github.com/facebookresearch/dacvae) — 音響VAE
- 各モデルウェイトのライセンスはそれぞれのモデルカードを確認してください。

このノードのライセンスは[LICENSE](LICENSE)(MIT)です。
