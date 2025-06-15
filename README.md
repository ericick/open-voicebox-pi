

# zh-ai-speaker

A modular, open-source Chinese smart voice assistant for Raspberry Pi, supporting flexible AI model switching and high-quality speech interaction.

一个模块化开源的中文智能语音助手，适用于树莓派，支持灵活的AI模型切换与高质量语音交互。

---

## Features | 功能特性

* **Local wake-word detection** (Porcupine, custom keywords like “小猪小猪”)

* **Real-time ASR** (Whisper.cpp, fully offline speech-to-text)

* **Flexible AI model switching** (DeepSeek API, supports multi-LLM extension)

* **High-quality TTS** (iFlytek/讯飞 TTS API)

* **Modular design** for easy extension, privacy-friendly, DIY-friendly

* **本地唤醒词检测**（Porcupine，可自定义如“小猪小猪”）

* **实时语音识别**（Whisper.cpp，全离线语音转文本）

* **灵活AI模型切换**（DeepSeek API，支持多种大模型拓展）

* **高质量语音合成**（讯飞TTS API，效果自然流畅）

* **模块化设计**，易于拓展，注重隐私，适合DIY开发

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
* Whisper.cpp (offline ASR)
* DeepSeek/OpenAI/other LLM APIs
* iFlytek TTS API (讯飞语音合成)
* 依赖库详见 `requirements.txt`

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

* **Porcupine**: Register at [Picovoice Console](https://console.picovoice.ai/), generate your custom wake-word `.ppn` file, and get your Access Key.

* **Whisper.cpp**: [Download the desired model file (e.g., ggml-tiny.bin)](https://huggingface.co/ggerganov/whisper.cpp) and compile the whisper.cpp executable for Raspberry Pi.

* **DeepSeek API**: Register at [DeepSeek Platform](https://platform.deepseek.com/), create an API key.

* **iFlytek TTS**: Register at [讯飞开放平台](https://www.xfyun.cn/), create an app and get your AppID, APIKey, and APISecret.

* **Porcupine**：在[Picovoice 控制台](https://console.picovoice.ai/)注册账号，生成你的唤醒词 `.ppn` 文件，并获取 Access Key。

* **Whisper.cpp**：从 [Hugging Face](https://huggingface.co/ggerganov/whisper.cpp) 下载所需模型文件（如 ggml-tiny.bin），在树莓派上编译主程序。

* **DeepSeek API**：在 [DeepSeek 平台](https://platform.deepseek.com/) 注册开发者账号，创建 API Key。

* **讯飞TTS**：在[讯飞开放平台](https://www.xfyun.cn/)注册账号，创建应用获取 AppID、APIKey 和 APISecret。

---

### 4. Configure the project | 配置项目

Edit `config/config.yaml` and fill in your API keys, file paths, and custom wake-word information.

编辑 `config/config.yaml`，填写你的API密钥、文件路径和自定义唤醒词配置。

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
├── dialogue/
├── tts/
├── audio_out/
├── endword/
├── utils/
├── requirements.txt
├── README.md
└── ...
```

---

## Customization & Extension | 个性化与拓展

* Supports easy switching between different LLM and TTS modules.
* Can add custom commands, multi-turn dialogue, smart home extensions, etc.
* 欢迎自定义/添加新AI模型、TTS模块或语音指令，支持多轮对话与智能家居扩展。

---

## License | 许可协议

This project is open-sourced under the MIT License.

本项目以 MIT 许可证开源。

---

## Acknowledgements | 鸣谢

* [Porcupine (Picovoice)](https://picovoice.ai/)
* [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
* [DeepSeek](https://platform.deepseek.com/)
* [讯飞开放平台](https://www.xfyun.cn/)
* And all open-source contributors

---

如需详细二次开发、问题反馈或定制说明，欢迎在Issue区留言或联系作者。

If you have questions, feature requests, or want to contribute, feel free to submit an issue or pull request.

---
