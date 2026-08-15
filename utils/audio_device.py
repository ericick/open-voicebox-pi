"""音频设备工具：按名称关键词查找麦克风，支持未接入时自动等待。"""
import time

import sounddevice as sd

from utils.logger import logger

DEFAULT_POLL_INTERVAL = 3.0


class DeviceUnavailable(Exception):
    """录音时麦克风不可用。"""


def find_input_device(keyword):
    """按名称关键词查找输入设备，返回设备编号；找不到返回 None。
    keyword 为整数时视为设备编号直接校验；为空时返回 None（表示未指定）。"""
    if not keyword:
        return None
    if isinstance(keyword, int):
        try:
            sd.check_input_settings(device=keyword)
            return keyword
        except Exception:
            return None
    try:
        devices = sd.query_devices()
    except Exception as e:
        logger.error(f"查询音频设备失败: {e}")
        return None
    lower_keyword = str(keyword).lower()
    for idx, dev in enumerate(devices):
        name = dev.get("name", "")
        if dev.get("max_input_channels", 0) > 0 and lower_keyword in str(name).lower():
            return idx
    return None


def refresh_audio_devices():
    """安全刷新音频设备列表（重新初始化音频引擎），让新插入的设备可见、清除幽灵条目。
    注意：必须在没有任何活动音频流、没有后台音频线程时调用——本项目的调用点都满足该条件。"""
    try:
        sd._terminate()
    except Exception:
        pass
    try:
        sd._initialize()
    except Exception:
        pass


def wait_for_input_device(keyword, poll_interval=DEFAULT_POLL_INTERVAL, refresh_every=10):
    """等待输入设备出现（每 poll_interval 秒检测一次），返回设备编号。
    等待期间每 refresh_every 轮强制刷新一次设备列表，确保启动后才插上的设备能被看到。"""
    count = 0
    while True:
        idx = find_input_device(keyword)
        if idx is not None:
            return idx
        count += 1
        if count == 1 or count % 12 == 0:
            logger.info(f"麦克风未接入（关键词: {keyword}），继续等待...")
        if count % refresh_every == 0:
            refresh_audio_devices()
        time.sleep(poll_interval)
