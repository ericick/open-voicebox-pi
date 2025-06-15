# zh-ai-speaker

A robust, modular, open-source Chinese smart voice assistant for Raspberry Pi, featuring enhanced exception handling and auto-retry for all network and I/O modules.

一个健壮、模块化、开源的中文树莓派智能语音助手，所有网络与音频模块均强化异常捕获和自动重试机制。

---

## Features | 功能特性

* **Local wake-word detection** (Porcupine, custom keywords e.g. “小猪小猪”)

* **Cloud ASR** (iFlytek, supports hotwords, with auto-retry and error handling)

* **Flexible AI model integration** (DeepSeek API with auto-retry)

* **Cloud TTS** (iFlytek, fast and natural, with error fallback and retry)

* **Modular and extensible design**

* **全流程异常捕获与自动重试，故障自动降级**

* **本地唤醒词检测**（Porcupine，可自定义，如“小猪小猪”）

* **云端语音识别**（讯飞ASR，支持热词添加，带自动重试与错误处理）

* **灵活对话模型集成**（DeepSeek API，自动重试与降级）

* **云端语音合成**（讯飞TTS，流畅自然，异常自动兜底）

* **模块化设计，便于扩展维护**

* **全模块异常捕获、自动重试、故障降级机制**

---

## Hardware Requirements | 硬件需求

* Raspberry Pi 4/5 (推荐8G内存)
* USB microphone array (建议：ReSpeaker USB Mic Array)
* Speaker (3.5mm/USB/HDMI output)
* MicroSD card (32G及以上)
* (可选) External power supply, cooling fan

---

## Software Stack | 软件环境

* Python 3.9+
* Porcupine SDK (wake word)
* iFlytek ASR & TTS API
* DeepSeek API
* requirements.txt 所有第三方依赖

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

* **Porcupine**: Register at [Picovoice Console](https://console.picovoice.ai/), generate custom wake-word `.ppn` file, and get Access Key.

* **iFlytek ASR & TTS**: Register at [讯飞开放平台](https://www.xfyun.cn/), create apps, obtain AppID, APIKey, and APISecret for both ASR & TTS, and configure hotwords.

* **DeepSeek API**: Register at [DeepSeek Platform](https://platform.deepseek.com/), create an API key.

* **Porcupine**：在[Picovoice 控制台](https://console.picovoice.ai/)注册账号，生成唤醒词 `.ppn` 文件并获取 Access Key。

* **讯飞ASR/TTS**：在[讯飞开放平台](https://www.xfyun.cn/)注册账号，分别创建听写和合成应用，获取AppID、APIKey和APISecret，配置热词。

* **DeepSeek API**：在 [DeepSeek 平台](https://platform.deepseek.com/) 注册开发者账号，创建API Key。

---

### 4. Configure the project | 配置项目

Edit `config/config.yaml` and fill in your API keys, hotwords, file paths, and custom wake-word info.

编辑 `config/config.yaml`，填写你的API密钥、热词、文件路径和唤醒词配置。

---

### 5. Run the main program | 启动主程序

```bash
python main.py
```

---

## Project Structure | 项目结构

```
zh-ai-speaker/
├── main.py
├── config/
│   └── config.yaml
├── wakeword/
├── audio_in/
├── asr/
│   └── xunfei_asr.py
├── dialogue/
│   └── deepseek_adapter.py
├── tts/
│   └── xunfei_adapter.py
├── audio_out/
│   └── player.py
├── endword/
│   └── endword_detector.py
├── utils/
│   ├── logger.py
│   ├── config_loader.py
│   └── retry_utils.py
├── requirements.txt
├── README.md
└── ...
```

---

## Exception Handling & Auto-Retry | 异常捕获与自动重试

* All API calls (ASR, TTS, Dialogue) feature robust exception handling and auto-retry.
* Main workflow gracefully degrades, always giving feedback to the user.
* 所有API调用（ASR、TTS、对话）均内置健壮异常捕获与自动重试，主流程有故障自动降级和语音播报。

---

## Customization & Extension | 个性化与拓展

* Hotwords can be customized in config.yaml for better recognition accuracy.
* Modular adapters make it easy to add/replace ASR, TTS, or LLM modules.
* 热词可随时在config.yaml配置，模块化结构方便拓展其它ASR/TTS/大模型。

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

如需二次开发、问题反馈或定制说明，欢迎在Issue区留言或联系作者。

If you have questions, feature requests, or want to contribute, feel free to submit an issue or pull request.

---
