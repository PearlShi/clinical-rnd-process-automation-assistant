"""
============================================================
  base_agent.py - 多任务智能体基础框架
  临床研发流程自动化助手
============================================================
  基于 LangChain 的通用多任务AI智能体基类。
  支持三大类基础任务：
    1. 文档智能处理（会议纪要、文档对比）
    2. 邮件内容解析（任务提取）
    3. 研发任务管理（进度追踪、提醒）

  智能体可自动识别输入内容与文件类型，匹配对应执行任务。
============================================================
"""

from __future__ import annotations

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field, asdict

from app.config import get_llm_config, is_mock_mode

logger = logging.getLogger(__name__)


# ============================================================
#  数据结构定义
# ============================================================

@dataclass
class TaskInput:
    """
    任务输入数据
    """
    input_type: str               # meeting_transcript | meeting_audio | protocol | icf | email | task_list | unknown
    content: str                  # 文本内容
    file_path: Optional[Path] = None   # 原始文件路径
    metadata: Dict[str, Any] = field(default_factory=dict)  # 附加元数据

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TaskResult:
    """
    任务执行结果
    """
    success: bool                 # 是否成功
    task_type: str                # 任务类型
    output: Any = None            # 结构化输出
    error_message: str = ""       # 错误信息
    processing_time: float = 0.0  # 处理耗时（秒）
    raw_text: str = ""            # 原始处理文本
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        result = asdict(self)
        if hasattr(self.output, 'to_dict'):
            result['output'] = self.output.to_dict()
        return result

    def to_json(self, ensure_ascii: bool = False) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii, indent=2)


# ============================================================
#  模拟LLM引擎（无需真实API密钥即可演示）
# ============================================================

class MockLLMEngine:
    """
    模拟LLM引擎 - 在无真实API密钥时提供基于模板的智能处理。
    通过规则匹配和模板生成模拟AI处理结果，确保项目可直接演示。
    """

    @staticmethod
    def generate_meeting_minutes(text: str, language: str = "zh-CN") -> dict:
        """模拟生成会议纪要"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # 尝试提取会议主题
        title = "项目进度评审会议"
        for line in lines:
            if '主题' in line or '议题' in line or 'title' in line.lower():
                title = line.split('：')[-1].split(':')[-1].strip()
                break
            if '关于' in line and '会议' in line:
                title = line.strip()
                break

        # 提取参会人员
        participants = []
        for line in lines:
            if '参会' in line or '出席' in line or 'participants' in line.lower():
                parts = line.replace('：', ':').split(':')
                if len(parts) > 1:
                    participants = [p.strip() for p in parts[1].split('、') if p.strip()]
                break

        if not participants:
            participants = ["张三", "李四", "王五", "赵六"]

        # 提取会议时间
        meeting_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        for line in lines:
            if '时间' in line or 'time' in line.lower():
                parts = line.replace('：', ':').split(':')
                if len(parts) > 1:
                    meeting_time = parts[1].strip()
                break

        # 生成讨论议题
        raw_topics = []
        current_topic = ""
        for line in lines:
            if any(kw in line for kw in ['议题', '议程', '讨论', 'agenda', 'topic']):
                if '：' in line or ':' in line:
                    parts = line.replace('：', ':').split(':', 1)
                    topic_name = parts[1].strip()
                    if topic_name:
                        raw_topics.append(topic_name)
                        current_topic = topic_name
                elif line.strip():
                    raw_topics.append(line.strip())
                    current_topic = line.strip()

        if not raw_topics:
            raw_topics = ["项目进度回顾", "关键问题讨论", "下一步计划"]

        # 生成核心议题
        core_topics = []
        for t in raw_topics[:5]:
            core_topics.append({
                "title": t,
                "content": f"会议就【{t}】进行了深入讨论，各参会人员充分发表了意见。"
            })

        # 生成关键决策
        key_decisions = []
        decision_templates = [
            f"确定按照当前时间表推进{raw_topics[0] if raw_topics else '项目'}相关工作",
            f"成立专项工作组负责{raw_topics[1] if len(raw_topics) > 1 else '关键问题'}的解决方案制定",
            f"下次会议前完成{raw_topics[-1] if raw_topics else '项目'}风险评估报告",
            "批准了下一阶段的资源分配方案",
        ]
        for d in decision_templates[:3]:
            key_decisions.append({"content": d})

        # 生成行动项
        action_items = []
        action_templates = [
            ("完成项目风险评估报告", "张三", meeting_time.split()[0] if ' ' in meeting_time else "2026-06-20", "高"),
            ("制定详细实施方案", "李四", meeting_time.split()[0] if ' ' in meeting_time else "2026-06-25", "中"),
            ("组织跨部门协调会议", "王五", meeting_time.split()[0] if ' ' in meeting_time else "2026-06-18", "高"),
            ("更新项目进度看板", "赵六", meeting_time.split()[0] if ' ' in meeting_time else "2026-06-22", "中"),
            ("整理客户反馈意见", "张三", "", "低"),
        ]
        for content, person, deadline, priority in action_templates:
            action_items.append({
                "content": content,
                "responsible_person": person,
                "deadline": deadline,
                "priority": priority,
            })

        return {
            "title": title,
            "meeting_time": meeting_time,
            "participants": participants,
            "core_topics": core_topics,
            "key_decisions": key_decisions,
            "action_items": action_items,
            "summary": f"本次会议围绕【{title}】展开，共讨论了{len(core_topics)}个核心议题，形成{len(key_decisions)}项决策和{len(action_items)}项待办行动项。"
        }

    @staticmethod
    def generate_doc_comparison(text1: str, text2: str, doc_type: str = "protocol") -> dict:
        """模拟生成文档对比结果"""
        lines1 = [l.strip() for l in text1.split('\n') if l.strip()]
        lines2 = [l.strip() for l in text2.split('\n') if l.strip()]

        changes = []
        i, j = 0, 0

        # 模拟差异检测
        while i < len(lines1) or j < len(lines2):
            if i < len(lines1) and j < len(lines2) and lines1[i] == lines2[j]:
                i += 1
                j += 1
            elif i < len(lines1) and (j >= len(lines2) or lines1[i] not in lines2):
                changes.append({
                    "type": "delete",
                    "content": lines1[i],
                    "line_old": i + 1,
                    "line_new": None,
                })
                i += 1
            elif j < len(lines2) and (i >= len(lines1) or lines2[j] not in lines1):
                changes.append({
                    "type": "add",
                    "content": lines2[j],
                    "line_old": None,
                    "line_new": j + 1,
                })
                j += 1
            else:
                if i < len(lines1):
                    changes.append({
                        "type": "modify",
                        "content_old": lines1[i],
                        "content_new": lines2[j],
                        "line_old": i + 1,
                        "line_new": j + 1,
                    })
                i += 1
                j += 1

        stats = {
            "additions": sum(1 for c in changes if c["type"] == "add"),
            "deletions": sum(1 for c in changes if c["type"] == "delete"),
            "modifications": sum(1 for c in changes if c["type"] == "modify"),
            "total_lines_old": len(lines1),
            "total_lines_new": len(lines2),
        }

        doc_type_name = {
            "protocol": "临床试验方案（Protocol）",
            "icf": "知情同意书（ICF）",
        }.get(doc_type, f"文档（{doc_type}）")

        return {
            "doc_type": doc_type,
            "doc_type_name": doc_type_name,
            "stats": stats,
            "changes": changes[:50],  # 最多返回50处变更
            "summary": (
                f"共发现 {stats['additions']} 处新增、"
                f"{stats['deletions']} 处删除、"
                f"{stats['modifications']} 处修改，"
                f"总计 {stats['additions'] + stats['deletions'] + stats['modifications']} 处变更。"
            ),
        }

    @staticmethod
    def extract_tasks(text: str) -> dict:
        """模拟从文本中提取任务"""
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        tasks = []
        for line in lines:
            # 尝试匹配任务模式
            task_info = {"content": "", "responsible_person": "", "deadline": "", "status": "待处理", "priority": "中"}

            # 检测是否包含任务标记
            is_task = False
            for marker in ['[ ]', '[-]', 'todo:', '待办:', 'task:', '- [', '* [', '☐', '□', '○']:
                if marker in line:
                    is_task = True
                    break

            if not is_task and not any(kw in line for kw in ['负责', '完成', '跟踪', '处理', '提交', '确认', 'review']):
                continue

            task_info["content"] = line

            # 提取负责人
            for sep in ['负责人:', '负责人：', '责任人:', '责任人：', '@', 'assignee:']:
                if sep in line:
                    idx = line.find(sep) + len(sep)
                    end = line.find(' ', idx)
                    if end == -1:
                        end = len(line)
                    candidate = line[idx:end].strip()
                    if candidate and len(candidate) < 10:
                        task_info["responsible_person"] = candidate
                        break

            # 提取截止日期
            import re
            date_pattern = r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2}[日]?)'
            date_match = re.search(date_pattern, line)
            if date_match:
                task_info["deadline"] = date_match.group(1)

            # 提取优先级
            if any(kw in line for kw in ['紧急', '高优先级', 'urgent', 'high', '重要']):
                task_info["priority"] = "高"
            elif any(kw in line for kw in ['低', 'low', 'minor']):
                task_info["priority"] = "低"

            # 提取状态
            if any(kw in line for kw in ['[x]', '[√]', '[✓]', '已完成', 'done']):
                task_info["status"] = "已完成"
            elif any(kw in line for kw in ['进行中', 'in progress', 'wip']):
                task_info["status"] = "进行中"

            if task_info["content"]:
                tasks.append(task_info)

        return {
            "tasks": tasks[:20],
            "total_count": len(tasks),
            "todo_count": sum(1 for t in tasks if t["status"] == "待处理"),
            "in_progress_count": sum(1 for t in tasks if t["status"] == "进行中"),
            "completed_count": sum(1 for t in tasks if t["status"] == "已完成"),
        }


# ============================================================
#  LLM引擎工厂
# ============================================================

class LLMEngineFactory:
    """LLM引擎工厂 - 根据配置选择合适的引擎"""

    @staticmethod
    def create_engine():
        """创建LLM引擎实例"""
        config = get_llm_config()

        if config["provider"] == "mock" or is_mock_mode():
            logger.info("使用模拟LLM引擎（Mock模式）")
            return MockLLMEngine()

        if config["provider"] == "openai" and config["api_key"]:
            try:
                from langchain_openai import ChatOpenAI
                logger.info(f"使用OpenAI引擎: {config['model']}")
                return ChatOpenAI(
                    model=config["model"],
                    temperature=config["temperature"],
                    max_tokens=config["max_tokens"],
                    api_key=config["api_key"],
                )
            except ImportError:
                logger.warning("langchain-openai 未安装，回退到模拟引擎")
                return MockLLMEngine()

        logger.warning(f"不支持的LLM提供者: {config['provider']}，回退到模拟引擎")
        return MockLLMEngine()


# ============================================================
#  任务路由器
# ============================================================

class TaskRouter:
    """
    任务路由器 - 根据输入内容自动识别任务类型并路由到对应处理器。
    核心调度逻辑，实现智能体自动匹配能力。
    """

    def __init__(self):
        self._engine = LLMEngineFactory.create_engine()

    def route(self, task_input: TaskInput) -> str:
        """
        根据输入内容判断任务类型
        返回: meeting_minutes | doc_compare | task_management | unknown
        """
        input_type = task_input.input_type

        # 基于输入类型的直接路由
        type_routing = {
            "meeting_transcript": "meeting_minutes",
            "meeting_audio": "meeting_minutes",
            "protocol": "doc_compare",
            "icf": "doc_compare",
            "email": "task_management",
            "task_list": "task_management",
        }

        if input_type in type_routing:
            task_type = type_routing[input_type]
            logger.info(f"已根据输入类型 '{input_type}' 路由到 '{task_type}' 任务")
            return task_type

        # 基于内容特征的智能识别
        content = task_input.content.lower()

        # 会议纪要特征识别
        meeting_keywords = ["会议记录", "会议纪要", "会议主题", "参会人", "meeting minutes", "meeting notes"]
        meeting_score = sum(1 for kw in meeting_keywords if kw in content)

        # 文档对比特征识别
        doc_compare_keywords = ["版本", "对比", "v1.", "v2.", "version", "diff", "修订", "修改记录"]
        doc_compare_score = sum(1 for kw in doc_compare_keywords if kw in content)

        # 任务管理特征识别
        task_keywords = ["任务", "待办", "todo", "deadline", "负责人", "assignee", "截止"]
        task_score = sum(1 for kw in task_keywords if kw in content)

        scores = {
            "meeting_minutes": meeting_score,
            "doc_compare": doc_compare_score,
            "task_management": task_score,
        }

        best_match = max(scores, key=scores.get)
        best_score = scores[best_match]

        if best_score >= 2:
            logger.info(f"已根据内容特征匹配到 '{best_match}' 任务（得分: {best_score}）")
            return best_match

        logger.info(f"未识别出特定任务类型（最高得分: '{best_match}'={best_score}），返回 unknown")
        return "unknown"

    def get_engine(self):
        """获取当前LLM引擎"""
        return self._engine


# ============================================================
#  基础智能体类
# ============================================================

class BaseAgent(ABC):
    """
    所有任务智能体的基类。
    子类需要实现 process() 方法。
    """

    def __init__(self, agent_name: str, agent_description: str):
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.router = TaskRouter()
        self.engine = self.router.get_engine()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def process(self, task_input: TaskInput) -> TaskResult:
        """
        处理输入并返回结果
        子类必须实现此方法
        """
        raise NotImplementedError("子类必须实现 process 方法")

    def validate_input(self, task_input: TaskInput) -> Tuple[bool, str]:
        """验证输入是否有效"""
        if not task_input.content and not task_input.file_path:
            return False, "输入内容为空，请提供文本内容或上传文件"
        return True, ""

    def log_processing(self, task_input: TaskInput, result: TaskResult):
        """记录处理日志"""
        self.logger.info(
            f"[{self.agent_name}] 任务类型={task_input.input_type}, "
            f"结果={'成功' if result.success else '失败'}, "
            f"耗时={result.processing_time:.2f}s"
        )


# ============================================================
#  主智能体调度器
# ============================================================

class AgentOrchestrator:
    """
    智能体调度器 - 统一管理所有智能体实例。
    负责接收输入，路由到正确的智能体，收集并返回结果。
    """

    def __init__(self):
        self.router = TaskRouter()
        self._agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger(__name__)

    def register_agent(self, task_type: str, agent: BaseAgent):
        """注册智能体到调度器"""
        self._agents[task_type] = agent
        self.logger.info(f"已注册智能体: {task_type} -> {agent.agent_name}")

    def unregister_agent(self, task_type: str):
        """注销智能体"""
        if task_type in self._agents:
            del self._agents[task_type]
            self.logger.info(f"已注销智能体: {task_type}")

    def get_registered_agents(self) -> Dict[str, str]:
        """获取所有已注册的智能体信息"""
        return {
            task_type: agent.agent_name
            for task_type, agent in self._agents.items()
        }

    def process(self, task_input: TaskInput) -> TaskResult:
        """
        处理输入 - 自动路由到对应智能体。
        完整的处理流程: 输入验证 → 类型识别 → 任务路由 → 智能体处理 → 结果返回
        """
        start_time = datetime.now()

        # 步骤1: 输入验证
        if not task_input.content and task_input.file_path:
            try:
                from app.utils.file_utils import read_text_file
                task_input.content = read_text_file(task_input.file_path)
            except Exception as e:
                return TaskResult(
                    success=False,
                    task_type="unknown",
                    error_message=f"无法读取文件: {str(e)}",
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )

        if not task_input.content:
            return TaskResult(
                success=False,
                task_type="unknown",
                error_message="输入内容为空",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

        # 步骤2: 内容类型识别
        if task_input.input_type == "unknown" or not task_input.input_type:
            from app.utils.file_utils import guess_content_type_from_content
            task_input.input_type = guess_content_type_from_content(task_input.content)

        # 步骤3: 任务路由
        task_type = self.router.route(task_input)

        if task_type == "unknown":
            return TaskResult(
                success=False,
                task_type="unknown",
                error_message="无法识别输入内容类型，请明确指定任务类型",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

        # 步骤4: 路由到对应智能体
        if task_type in self._agents:
            agent = self._agents[task_type]
            result = agent.process(task_input)
            result.processing_time = (datetime.now() - start_time).total_seconds()
            return result

        return TaskResult(
            success=False,
            task_type=task_type,
            error_message=f"未找到处理 '{task_type}' 任务的智能体",
            processing_time=(datetime.now() - start_time).total_seconds(),
        )


# ============================================================
#  全局调度器实例（单例模式）
# ============================================================

_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    """获取全局调度器实例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


def reset_orchestrator():
    """重置调度器（用于测试和重新配置）"""
    global _orchestrator
    _orchestrator = None
