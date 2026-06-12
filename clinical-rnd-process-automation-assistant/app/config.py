"""
============================================================
  config.py - 全局配置管理
  临床研发流程自动化助手
============================================================
  功能说明：
  统一管理应用的全局配置项，支持环境变量覆盖，
  为各模块提供一致的配置接口。
============================================================
"""

import os
import json
from pathlib import Path
from typing import Optional


# ---------- 路径定义 ----------
BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
SAMPLES_DIR = DATA_DIR / "samples"
LOGS_DIR = BASE_DIR / "logs"

# 确保必要目录存在
for d in [DATA_DIR, SAMPLES_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ---------- 应用基础配置 ----------
APP_NAME = "临床研发流程自动化助手"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "基于AI智能体技术的临床研发工作流自动化工具"
DEBUG = os.getenv("APP_DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("APP_SECRET_KEY", "change-me-in-production")


# ---------- LLM / AI 配置 ----------
# 默认使用模拟模式（无需真实API密钥即可演示功能）
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")  # mock | openai | anthropic
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))


# ---------- 文件上传配置 ----------
UPLOAD_DIR = BASE_DIR / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
ALLOWED_DOC_EXTENSIONS = {".docx", ".pdf", ".txt", ".md"}
ALLOWED_TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json", ".xml"}
MAX_UPLOAD_SIZE_MB = 50


# ---------- 会议纪要模块配置 ----------
MEETING_CONFIG = {
    "default_language": "zh-CN",
    "output_format": "markdown",  # markdown | docx
    "enable_speech_recognition": True,
    "speech_recognition_timeout": 300,
}


# ---------- 文档对比模块配置 ----------
DOC_COMPARE_CONFIG = {
    "highlight_add": "#e6ffe6",      # 新增内容背景色（浅绿）
    "highlight_delete": "#ffe6e6",   # 删除内容背景色（浅红）
    "highlight_modify": "#fff3cd",   # 修改内容背景色（浅黄）
    "max_diff_context_lines": 3,
}


# ---------- 任务管理模块配置 ----------
TASK_CONFIG = {
    "reminder_interval_minutes": 60,
    "default_reminder_enabled": True,
    "auto_archive_days": 30,
}


# ---------- 加载插件配置 ----------
def load_plugin_config() -> dict:
    """加载 plugins.json 插件配置文件"""
    plugin_config_path = CONFIG_DIR / "plugins.json"
    if plugin_config_path.exists():
        with open(plugin_config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"enabled_plugins": [], "plugin_settings": {}}


# ---------- 加载任务规则配置 ----------
def load_task_rules() -> dict:
    """加载 tasks.json 任务规则配置文件"""
    task_rules_path = CONFIG_DIR / "tasks.json"
    if task_rules_path.exists():
        with open(task_rules_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ---------- 快捷检查函数 ----------
def is_mock_mode() -> bool:
    """当前是否处于模拟模式（无需真实LLM API）"""
    return LLM_PROVIDER == "mock"


def get_llm_config() -> dict:
    """获取当前LLM配置字典"""
    return {
        "provider": LLM_PROVIDER,
        "api_key": LLM_API_KEY,
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
    }
