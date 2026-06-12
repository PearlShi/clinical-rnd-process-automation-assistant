"""
============================================================
  doc_compare/comparator.py - 文档对比工具集
  临床研发流程自动化助手
============================================================
  提供文档对比的辅助功能和工具函数
============================================================
"""

import re
from pathlib import Path
from typing import Optional, List, Tuple


# 临床文档常用章节标题（用于智能分段）
PROTOCOL_SECTIONS = [
    "试验标题", "研究目的", "试验设计", "入选标准", "排除标准",
    "受试者退出", "治疗方案", "疗效评估", "安全性评估", "统计分析",
    "数据管理", "伦理审查", "知情同意", "参考文献", "附录",
]

ICF_SECTIONS = [
    "研究背景", "研究目的", "研究程序", "风险与不适", "潜在受益",
    "替代方案", "保密性", "自愿参加", "退出研究", "联系人信息",
    "受试者声明", "研究者声明", "签名页",
]


def detect_doc_type(text: str) -> str:
    """
    根据文本内容自动检测文档类型
    返回: protocol | icf | unknown
    """
    text_lower = text.lower()
    protocol_score = sum(
        1 for kw in ["临床试验", "protocol", "研究方案", "入选标准", "排除标准",
                     "试验设计", "方案编号", "申办者", "监查员"]
        if kw in text_lower
    )
    icf_score = sum(
        1 for kw in ["知情同意", "informed consent", "受试者须知", "同意书",
                     "自愿参加", "签名", "confidentiality", "隐私"]
        if kw in text_lower
    )

    if protocol_score > icf_score and protocol_score >= 2:
        return "protocol"
    elif icf_score >= 2:
        return "icf"
    return "unknown"


def section_aware_chunk(text: str, doc_type: str = "protocol") -> dict:
    """
    按章节将文档分段
    Args:
        text: 文档全文
        doc_type: 文档类型
    Returns:
        {section_title: content, ...}
    """
    sections = PROTOCOL_SECTIONS if doc_type == "protocol" else ICF_SECTIONS
    result = {}
    current_section = "前言"
    current_content = []

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue

        # 检测是否为章节标题
        matched = False
        for section in sections:
            if section in line and len(line) < 50:
                if current_content:
                    result[current_section] = '\n'.join(current_content)
                current_section = section
                current_content = []
                matched = True
                break

        if not matched:
            current_content.append(line)

    # 保存最后一节
    if current_content:
        result[current_section] = '\n'.join(current_content)

    return result
