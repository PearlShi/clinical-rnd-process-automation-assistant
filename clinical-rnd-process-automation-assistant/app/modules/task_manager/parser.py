"""
============================================================
  task_manager/parser.py - 任务解析工具集
  临床研发流程自动化助手
============================================================
  提供邮件预处理、任务文本标准化等辅助功能
============================================================
"""

import re
from typing import List, Tuple, Optional
from datetime import datetime


def extract_email_addresses(text: str) -> List[str]:
    """从文本中提取邮箱地址"""
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    return re.findall(pattern, text)


def extract_mentions(text: str) -> List[str]:
    """提取 @提及 的人名"""
    pattern = r'@([一-龥a-zA-Z]+)'
    return re.findall(pattern, text)


def extract_deadlines(text: str) -> List[Tuple[str, str]]:
    """
    提取文本中的截止日期
    返回: [(日期字符串, 上下文), ...]
    """
    patterns = [
        r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)',
        r'(?:下周[一二三四五六日]|下周一|下周二|下周三|下周四|下周五|下周六|下周日)',
        r'(?:本周[一二三四五六日]|本周一|本周二|本周三|本周四|本周五|本周六|本周日)',
        r'(?:明天|后天|今天|昨日|昨天)',
    ]

    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 20)
            context = text[start:end].strip()
            results.append((match.group(), context))

    return results


def normalize_task_text(text: str) -> str:
    """
    标准化任务文本格式
    - 统一任务标记
    - 标准化优先级标记
    """
    # 统一任务标记
    replacements = [
        (r'[☐□○⭕]', '[ ]'),
        (r'[☑☒✓✔✅]', '[x]'),
        (r'^- \[ \]', '- [ ]'),
        (r'^- \[x\]', '- [x]'),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text


def priority_from_text(text: str) -> str:
    """从文本推断优先级"""
    high_keywords = ['紧急', 'urgent', 'high', '重要', 'critical', 'asap', '尽快']
    low_keywords = ['低优先级', 'low', 'minor', 'nice to have', 'optional']

    text_lower = text.lower()
    if any(kw in text_lower for kw in high_keywords):
        return "高"
    if any(kw in text_lower for kw in low_keywords):
        return "低"
    return "中"
