# DeepSeek-Powered Smart Voice Speaker

基于树莓派/Jetson和DeepSeek/讯飞API的智能语音音箱

---

## 项目简介 | Project Introduction

本项目是一个使用 Python、树莓派5/Jetson Orin Nano 以及 DeepSeek/讯飞云API 的智能语音对话音箱系统，专注极致语音体验、稳定多轮对话、异常友好播报与本地高效缓存，支持热词自定义、参数完全解耦、自动性能监控及缓存清理，适合个人定制或行业集成。

This project is a smart voice speaker system powered by Python, Raspberry Pi 5 / Jetson Orin Nano, DeepSeek LLM, and iFlytek (Xunfei) ASR/TTS cloud APIs. It features robust multi-turn dialogue, customized hotword detection, detailed error reporting, local audio caching, parameter decoupling, automatic performance monitoring, and cache cleaning. Ideal for personal DIY or industrial integration.

---

## 主要功能 | Features

- 多轮对话：上下文记忆，支持 DeepSeek 大模型
- 本地唤醒词检测：Porcupine 支持自定义唤醒词
- 讯飞云ASR+TTS：可中英文混合识别，自然语音合成
- 全异常分级播报：如录音故障、网络/ASR/TTS异常均有清晰语音提示
- 所有参数全配置化，热词、音色、欢迎语等随需调整
- 冷启动常用提示音、异常音预缓存，秒级响应
- TTS音频智能缓存与自动清理，防止磁盘爆满
- 详细性能日志与API耗时监控，助力产品级优化
- 兼容树莓派、Jetson、小主机等Linux硬件

---

## 快速开始 | Quick Start

### 1. 克隆仓库 | Clone the Repo

```bash
git clone https://github.com/yourname/deepseek-smart-speaker.git
cd deepseek-smart-speaker
````

### 2. 安装依赖 | Install Requirements

建议 Python 3.9+，推荐虚拟环境。

```bash
pip install -r requirements.txt
```

### 3. 配置参数 | Configure Your Keys

编辑 `config/config.yaml`，填写讯飞/DeepSeek/Picovoice 等 API Key 与自定义参数。
每项配置含注释，所有可选项均支持覆盖。

### 4. 运行主程序 | Run the Main App

```bash
python main.py
```

> 首次启动将自动生成本地欢迎语音、异常播报缓存，冷启动后体验极快。

---

## 目录结构 | Directory Structure

```
├── main.py                      # 主业务入口
├── config/
│   └── config.yaml              # 全参数解耦配置文件
├── utils/
│   ├── logger.py                # 日志分级与轮转
│   ├── timing.py                # 性能/耗时监控装饰器
│   ├── retry_utils.py           # 自动重试工具
│   ├── tts_cache_manager.py     # TTS缓存管理与异常播报
│   └── config_loader.py         # 配置加载与校验
├── asr/xunfei_asr.py            # 讯飞ASR模块
├── tts/xunfei_adapter.py        # 讯飞TTS模块
├── dialogue/deepseek_adapter.py # DeepSeek LLM模块
├── wakeword/porcupine_adapter.py# 本地唤醒词检测
├── audio_in/recorder.py         # 录音模块
├── audio_out/player.py          # 音频播放
├── endword/endword_detector.py  # 结束词检测
├── audio_out/
│   ├── welcome.mp3              # 欢迎语缓存
│   └── tts_cache/               # TTS及异常音缓存
├── logs/                        # 分级日志与性能日志
└── requirements.txt             # 依赖列表
```

---

## 性能与异常监控 | Performance & Error Handling

* **API调用耗时自动记录**：所有ASR、TTS、LLM调用均有日志标记耗时，便于随时追踪瓶颈。
* **端到端耗时可扩展**：可在主流程加计时，统计用户体验全流程时延。
* **标准化异常分级播报**：如录音、ASR、TTS、网络、系统等异常均有本地预缓存的播报音，极大提升可用性。
* **TTS缓存自动清理**：音频文件超出50条或100MB自动清理最老，磁盘永不爆满。

---

## 常见问题 | FAQ

**Q: 支持中英文双语吗？**
A: 只要config配置 engine\_type=sms16k，讯飞ASR支持中英混合识别。

**Q: 怎么自定义唤醒词？**
A: 用 Porcupine 官方定制工具生成 `.ppn`，在config里配置 `wakeword.keyword_paths`。

**Q: 缓存目录满了怎么办？**
A: 程序启动与每次TTS调用前自动清理缓存，无需人工维护。

**Q: 怎么监控API或端到端响应慢？**
A: 查看 `logs/` 下的日志文件，所有API和主链路耗时都有详细记录。

---

## 联系与贡献 | Contact & Contribution

如遇到问题、功能建议或希望贡献代码，请提Issue或PR，欢迎交流与完善！

If you have any questions, suggestions, or wish to contribute, please open an issue or pull request. Welcome!

---

## License

MIT License.

---
