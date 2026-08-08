#!/usr/bin/env bash
# macOS 版启动脚本（智能语音音箱）
#
# 说明：仅在本程序进程内临时关闭代理（直连 DeepSeek / 讯飞），
# 不影响系统代理、其他终端或其他程序的运行。

cd "$(dirname "$0")"

# 只对当前进程及其子进程生效，脚本退出后自动恢复
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY

source venv-mac/bin/activate
exec python main.py
