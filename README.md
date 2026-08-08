# DeepSeek-Powered Smart Voice Speaker

基于 DeepSeek / 讯飞 API 的智能语音音箱，支持 **macOS（Apple Silicon）、树莓派 5 / Jetson**。

> v3.0.0：新增 macOS 支持；唤醒词改为 sherpa-onnx 离线方案（无需账号/联网）；录音改为"等用户开口再开始"。

---

## 项目简介 | Introduction

本项目是一个使用 Python、DeepSeek 大模型与讯飞云 API 的智能语音对话音箱系统。
技术路线：**sherpa-onnx 离线唤醒词 → 讯飞流式 ASR → DeepSeek 多轮对话 → 讯飞流式 TTS**。
唤醒词全程本地运行，无需任何账号或网络；对话依赖 DeepSeek / 讯飞云 API。

## 主要功能 | Features

* **多轮对话**：DeepSeek 大模型，上下文保持自然
* **离线唤醒词**：sherpa-onnx（默认"小猪小猪"），无需账号、无需联网
* **讯飞 ASR + TTS**：中英混合识别，流式语音合成
* **智能录音**：等用户开口才开始录音，说完静音自动停止，不催促、不误判
* **结束词**：说"再见 / 拜拜 / 下次再说"结束对话
* **异常分级播报**：网络、录音、ASR、TTS 故障均有语音提示
* **播放与录音隔离**：音箱说话时不会录到自己

## 快速开始 | Quick Start

### macOS（Apple Silicon）

1. 前置条件：Python 3.12、USB 麦克风（如 ReSpeaker 4 Mic Array）、音箱（3.5mm 或 USB）
2. 克隆仓库并创建虚拟环境：

```bash
git clone https://github.com/ericick/open-voicebox-pi.git
cd open-voicebox-pi
python3 -m venv venv-mac
source venv-mac/bin/activate
pip install -r requirements.txt
```

> 注意：`requirements.txt` 将 sherpa-onnx 固定在 **1.12.40**。1.13.x 的 macOS 版本存在唤醒词检测失效问题，请勿升级。

3. 下载唤醒词模型（官方 k2-fsa 发布页）：

```bash
cd wakeword
curl -SL -O https://github.com/k2-fsa/sherpa-onnx/releases/download/kws-models/sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20.tar.bz2
tar xvf sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20.tar.bz2
rm sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20.tar.bz2
cd ..
```

> 国内网络可改用 ModelScope 镜像下载同名模型。

4. 配置 `config/config.yaml`：
   * `deepseek.api_key`：DeepSeek API Key；`api_url` 填 `https://api.deepseek.com`（不要带 `/chat/completions`）
   * `xunfei` / `xunfei_asr`：讯飞开放平台的 AppID、APIKey、APISecret
   * `audio_in.device` / `wakeword.audio_device_index`：你的麦克风设备名（可用 `python -c "import sounddevice; print(sounddevice.query_devices())"` 查看）
5. 启动：

```bash
./run.sh
```

> `run.sh` 只在音箱程序内部临时关闭系统代理（直连 DeepSeek / 讯飞），不影响系统和其他程序。若你的网络必须走代理，删掉 `run.sh` 里的 `unset` 行，改为 `pip install socksio` 即可。

### 树莓派 5 / Jetson / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# 下载唤醒词模型（同上，路径放到 wakeword/）
python main.py
```

播放器会自动按系统选择：macOS 用 `afplay`，Linux 用 `mpg123`。

## 唤醒词自定义 | Custom Wake Word

1. 在 `wakeword/keywords_raw.txt` 里写一行中文（如 `小猪小猪 @小猪小猪`）
2. 用 sherpa-onnx 自带工具转成拼音 token：

```bash
pip install click sentencepiece   # text2token 所需组件
venv-mac/bin/sherpa-onnx-cli text2token \
  --tokens wakeword/<模型目录>/tokens.txt \
  --tokens-type ppinyin \
  wakeword/keywords_raw.txt wakeword/keywords_custom.txt
```

3. 灵敏度调整：`config/config.yaml` 的 `wakeword.keywords_score`（越大越灵敏）、`wakeword.keywords_threshold`（越大越难触发）。

## 目录结构 | Directory Structure

```
├── main.py                      # 主业务入口
├── run.sh                       # macOS 启动脚本（临时关闭代理直连）
├── config/
│   ├── config.yaml              # 全局配置（含密钥，不入库）
│   └── config_example.yaml      # 配置示例
├── utils/                       # 配置加载、日志、初始化
├── asr/xunfei_asr.py            # 讯飞流式 ASR
├── tts/                         # 讯飞流式 TTS
├── dialogue/deepseek_adapter.py # DeepSeek 对话
├── wakeword/
│   ├── wakeword_detector.py     # sherpa-onnx 唤醒词检测
│   ├── keywords_custom.txt      # 唤醒词（拼音 token）
│   └── sherpa-onnx-kws-*/       # 唤醒词模型（自行下载，不入库）
├── endword/endword_detector.py  # 结束词检测
├── audio_in/recorder.py         # 录音（等用户开口）
└── audio_out/player.py          # 音频播放（macOS/Linux 自动适配）
```

## FAQ

**Q: 为什么用 run.sh？**
A: 你的系统设置了 SOCKS5 全局代理，而程序用的联网库需要额外组件才能走 SOCKS5。`run.sh` 让音箱程序直连（DeepSeek/讯飞均为国内服务），只影响本程序。

**Q: 唤醒词没反应？**
A: 确认模型已下载到 `wakeword/sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20`；确认 `config.yaml` 的 `wakeword.model_dir` 路径正确；调高 `keywords_score`。

**Q: 升级 sherpa-onnx 后唤醒词失灵？**
A: 1.13.x 的 macOS 版唤醒词功能有缺陷，请保持 `requirements.txt` 中的 `sherpa-onnx==1.12.40`。

## License

MIT License.
