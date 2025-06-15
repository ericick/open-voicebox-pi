# zh-ai-speaker

A robust, modular, open-source Chinese smart voice assistant for Raspberry Pi, with enhanced exception handling and auto-retry for all network and I/O modules.

一个健壮、模块化、开源的树莓派中文智能语音助手，所有网络和音频模块都具备异常捕获和自动重试机制，支持云端ASR/TTS、热词和灵活拓展。

---

## Features | 功能特性

* **Local wake-word detection** (Porcupine, custom keywords e.g. “小猪小猪”)
* **Cloud ASR** (iFlytek, supports hotwords, with auto-retry and error handling)
* **Flexible AI dialogue** (DeepSeek API, with auto-retry and fallback)
* **Cloud TTS** (iFlytek, fast, natural, robust to errors)
* **Modular adapters** (easy to replace or expand)
* **Endword detection** (“再见”等自动结束对话)
* **全流程异常捕获与自动重试，故障自动降级**
* **本地唤醒词、热词支持，结构清晰可维护**

---

## Hardware Requirements | 硬件需求

* Raspberry Pi 4/5 (推荐8G内存)
* USB microphone array (建议：ReSpeaker USB Mic Array)
* Speaker (3.5mm/USB/HDMI output)
* MicroSD card (32G及以上)
* (可选) 外接电源，散热风扇

---

## Software Stack | 软件环境

* Python 3.9+
* requirements.txt 依赖全部
* Porcupine SDK (wake word)
* iFlytek ASR & TTS API
* DeepSeek API

---

## Project Structure | 项目结构

```
zh-ai-speaker/
├── main.py
├── config/
│   └── config.yaml
├── wakeword/
│   ├── porcupine_adapter.py    # Porcupine热词唤醒适配器
│   ├── __init__.py
├── audio_in/
│   ├── recorder.py             # 录音采集与静音检测
│   ├── __init__.py
├── asr/
│   ├── xunfei_asr.py           # 讯飞ASR适配（热词/异常重试）
│   ├── __init__.py
├── dialogue/
│   ├── deepseek_adapter.py     # DeepSeek对话接口（异常重试）
│   ├── __init__.py
├── tts/
│   ├── xunfei_adapter.py       # 讯飞TTS适配（异常重试）
│   ├── __init__.py
├── audio_out/
│   ├── player.py               # 播放音频文件，异常处理
│   ├── __init__.py
├── endword/
│   ├── endword_detector.py     # 结束词检测（正则/扩展）
│   ├── __init__.py
├── utils/
│   ├── logger.py               # 全局日志
│   ├── config_loader.py        # 配置加载
│   ├── retry_utils.py          # 通用重试装饰器
│   ├── __init__.py
├── requirements.txt
├── README.md
└── ...
```

---

## Quick Start | 快速上手

### 1. Clone the repository | 克隆代码

```bash
git clone https://github.com/yourusername/zh-ai-speaker.git
cd zh-ai-speaker
```

### 2. Install dependencies | 安装依赖

```bash
pip install -r requirements.txt
```

### 3. Prepare third-party resources | 准备第三方资源

* **Porcupine**: Register at [Picovoice Console](https://console.picovoice.ai/), generate custom wake-word `.ppn` file, and get Access Key. Place the `.ppn` file in the wakeword directory.

* **iFlytek ASR & TTS**: Register at [讯飞开放平台](https://www.xfyun.cn/), create apps, obtain AppID, APIKey, and APISecret for both ASR & TTS. Add hotwords to config.

* **DeepSeek API**: Register at [DeepSeek Platform](https://platform.deepseek.com/), create an API key.

* **Porcupine**：在[Picovoice 控制台](https://console.picovoice.ai/)注册账号，生成唤醒词 `.ppn` 文件并获取 Access Key，`.ppn` 文件放入 wakeword 目录。

* **讯飞ASR/TTS**：在[讯飞开放平台](https://www.xfyun.cn/)注册账号，创建听写/合成应用，获取AppID、APIKey、APISecret并在config中配置热词。

* **DeepSeek API**：在 [DeepSeek 平台](https://platform.deepseek.com/) 注册账号，创建API Key。

---

### 4. Configure the project | 配置项目

Edit `config/config.yaml` with your API keys, hotwords, file paths, and custom wake-word info.

编辑 `config/config.yaml`，填写API密钥、热词、文件路径及唤醒词相关信息。

---

### 5. Run the main program | 启动主程序

```bash
python main.py
```

---

## Exception Handling & Auto-Retry | 异常捕获与自动重试

* All network and device operations are wrapped with robust exception handling and automatic retry (see `utils/retry_utils.py`).

* Errors are logged, the system gives user feedback via TTS, and the workflow gracefully degrades if any module fails.

* 所有网络/设备操作都具备异常捕获与自动重试（见 `utils/retry_utils.py`），

* 错误自动记录日志、用TTS播报反馈，流程异常时能平滑降级。

---

## Customization & Extension | 个性化与拓展

* **Hotwords**: Easily add business-specific hotwords in `config.yaml` for higher ASR accuracy.
* **Adapter expansion**: To add a new ASR/TTS/dialogue module, just add a new adapter in the relevant directory.
* **结束词**: 可以自定义对话结束词（如“下次再说”、“拜拜”等）。

---

## Sample config.yaml | 配置示例

```yaml
xunfei_asr:
  app_id: "你的ASR APPID"
  api_key: "你的ASR APIKey"
  api_secret: "你的ASR APISecret"
  hotwords: "小猪小猪,芝麻开门,嘟嘟"

deepseek:
  api_key: "你的DeepSeek APIKey"

xunfei:
  app_id: "你的TTS APPID"
  api_key: "你的TTS APIKey"
  api_secret: "你的TTS APISecret"

endwords:
  - "再见"
  - "拜拜"
  - "下次再说"
  - "回头聊"
```

---

## License | 许可协议

This project is open-sourced under the MIT License.

本项目以 MIT 许可证开源。

---

## Acknowledgements | 鸣谢

* [Porcupine (Picovoice)](https://picovoice.ai/)
* [iFlytek 讯飞开放平台](https://www.xfyun.cn/)
* [DeepSeek](https://platform.deepseek.com/)
* And all open-source contributors

---

**Issues, suggestions, or need help? Please submit via GitHub Issues or contact the maintainer.**

如需二次开发、功能建议、bug反馈，欢迎在GitHub Issue区留言！

---
