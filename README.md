DeepSeek-Powered Smart Voice Speaker

基于树莓派/Jetson 和 DeepSeek/讯飞 API 的智能语音音箱

项目简介 | Project Introduction

本项目是一个使用 Python、树莓派 5 / Jetson Orin Nano 以及 DeepSeek / 讯飞云 API 的智能语音对话音箱系统，强调稳定、低延迟和友好的交互体验。
它支持多轮对话、热词唤醒、自定义结束词、异常分级播报，且已优化为无需单独的 TTS 缓存管理机制，直接依赖事件同步确保流畅的输入输出流程。

This project is a smart voice speaker powered by Python, Raspberry Pi 5 / Jetson Orin Nano, DeepSeek LLM, and iFlytek (Xunfei) ASR/TTS APIs. It provides robust multi-turn dialogue, hotword/stopword detection, graded error reporting, and streamlined audio event handling. The system has been optimized to remove legacy cache managers and now ensures smooth streaming playback using event synchronization.

主要功能 | Features

多轮对话：支持 DeepSeek 大模型，上下文保持自然

唤醒/结束词：Porcupine 自定义唤醒词 + DeepSeek 动态生成结束词

讯飞 ASR+TTS：中英混合识别，流式语音合成

异常分级播报：网络、录音、ASR、TTS 故障均有语音提示

参数全配置化：热词、音色、欢迎语、超时阈值等统一在配置文件里管理

冷启动秒级响应：欢迎语和常见错误音频预缓存

事件包裹的音频播放：避免播放与录音冲突，防止 ASR 误识别系统播报

兼容性强：树莓派、Jetson、小型 Linux 主机均可运行

快速开始 | Quick Start
1. 克隆仓库 | Clone the Repo
git clone https://github.com/ericick/deepseek-smart-speaker.git
cd deepseek-smart-speaker

2. 安装依赖 | Install Requirements

建议 Python 3.9+，推荐虚拟环境：

pip install -r requirements.txt

3. 配置参数 | Configure Your Keys

编辑 config/config.yaml，填入 DeepSeek / iFlytek / Porcupine API Key 及自定义参数。

4. 运行主程序 | Run the Main App
python main.py


首次启动将生成欢迎语和异常提示缓存音频。此后启动延迟极短。

目录结构 | Directory Structure
├── main.py                      # 主业务入口
├── config/
│   └── config.yaml              # 全局配置文件
├── utils/
│   ├── logger.py                # 日志管理
│   ├── timing.py                # 性能监控装饰器
│   ├── retry_utils.py           # 自动重试工具
│   └── config_loader.py         # 配置加载与校验
├── asr/xunfei_asr.py            # 讯飞 ASR 模块
├── tts/xunfei_adapter.py        # 讯飞 TTS 模块
├── dialogue/deepseek_adapter.py # DeepSeek LLM 模块
├── wakeword/porcupine_adapter.py# 本地唤醒词检测
├── endword/endword_detector.py  # 结束词检测（DeepSeek 生成）
├── audio_in/recorder.py         # 录音
├── audio_out/player.py          # 音频播放（事件包裹，避免冲突）
├── audio_out/
│   ├── welcome.mp3              # 欢迎语缓存
│   ├── error_beep.mp3           # 异常提示音
│   └── tts_cache/               # 流式生成的 TTS 音频缓存
├── logs/                        # 日志目录
└── requirements.txt             # 依赖列表

性能与异常监控 | Performance & Error Handling

API 调用耗时自动记录：ASR / TTS / LLM 皆有耗时日志

端到端统计：可扩展计时器监控整体用户体验延迟

异常分级提示：录音、ASR、TTS、网络、系统异常，均有本地缓存的语音播报

事件同步：播放期间阻塞 ASR，防止系统提示音误识别

缓存机制简化：不再依赖独立的 TTSCacheManager，缓存清理逻辑内嵌在播放和生成模块中

FAQ

Q: 支持中英混合识别吗？
A: 是的，配置 engine_type=sms16k 后，讯飞 ASR 可中英文混合识别。

Q: 唤醒/结束词能自定义吗？
A: 唤醒词通过 Porcupine 定制 .ppn 文件；结束词由 DeepSeek 在对话逻辑中生成。

Q: 系统提示音会被 ASR 识别吗？
A: 不会。音频播放被事件包裹，播放时 ASR 暂停，避免误识别。

联系与贡献 | Contact & Contribution

欢迎通过 Issue 或 PR 提交问题与建议！

If you’d like to contribute, please fork and submit pull requests.

License

MIT License.
