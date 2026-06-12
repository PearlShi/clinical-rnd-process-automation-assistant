"""
============================================================
  meeting_minutes/processor.py - 会议纪要处理器
  临床研发流程自动化助手
============================================================
  提供会议转录文本预处理、音频转文字等功能
============================================================
"""

from pathlib import Path
from typing import Optional
from app.utils.file_utils import read_text_file


def load_transcript(file_path: Path) -> str:
    """
    加载会议转录文件
    支持 txt, md, docx 格式
    """
    ext = file_path.suffix.lower()
    if ext == '.docx':
        try:
            from docx import Document
            doc = Document(str(file_path))
            return '\n'.join(p.text for p in doc.paragraphs)
        except ImportError:
            pass
    # 默认以文本方式读取
    return read_text_file(file_path)


def split_by_speaker(text: str) -> list[dict]:
    """
    按发言人分割会议文本
    返回: [{"speaker": "张三", "content": "...", "timestamp": "00:05:23"}, ...]
    """
    import re
    segments = []

    # 常见的发言人标记模式
    speaker_patterns = [
        r'(?P<speaker>[^\n:：]+)[:：]\s*(?P<content>.+)',
        r'\[(?P<speaker>[^\]]+)\]\s*(?P<content>.+)',
        r'(?P<speaker>[^\n]+)说[:：]\s*(?P<content>.+)',
    ]

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        matched = False
        for pattern in speaker_patterns:
            m = re.match(pattern, line)
            if m:
                segments.append({
                    "speaker": m.group("speaker").strip(),
                    "content": m.group("content").strip(),
                })
                matched = True
                break

        if not matched:
            # 无法识别发言人，作为连续内容
            if segments:
                segments[-1]["content"] += "\n" + line
            else:
                segments.append({
                    "speaker": "未知",
                    "content": line,
                })

    return segments
