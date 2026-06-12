"""
============================================================
  task_manager/ - 任务提醒与进度追踪模块
  临床研发流程自动化助手
============================================================
  功能说明：
  可解析工作邮件、零散任务文本清单，自动提取任务内容、
  负责人、时间节点等信息，统一整理为结构化待办列表，
  并实现任务跟进与提醒功能。
============================================================
"""

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

from app.agent.base_agent import BaseAgent, TaskInput, TaskResult, MockLLMEngine
from app.config import TASK_CONFIG

logger = logging.getLogger(__name__)


# ============================================================
#  数据结构
# ============================================================

@dataclass
class TaskItem:
    """单个任务项"""
    id: str = ""
    content: str = ""
    responsible_person: str = ""
    deadline: str = ""
    priority: str = "中"  # 高 | 中 | 低
    status: str = "待处理"  # 待处理 | 进行中 | 已完成
    category: str = ""
    source: str = ""
    created_at: str = ""
    updated_at: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class TaskList:
    """任务列表"""
    tasks: List[TaskItem] = field(default_factory=list)
    source_text: str = ""
    parsed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "tasks": [t.to_dict() for t in self.tasks],
            "total_count": len(self.tasks),
            "todo_count": sum(1 for t in self.tasks if t.status == "待处理"),
            "in_progress_count": sum(1 for t in self.tasks if t.status == "进行中"),
            "completed_count": sum(1 for t in self.tasks if t.status == "已完成"),
            "source_text": self.source_text,
            "parsed_at": self.parsed_at,
        }


# ============================================================
#  任务解析器
# ============================================================

class TaskParser:
    """
    任务解析器 - 从各类文本中提取结构化任务信息。
    支持邮件文本、待办清单、工作消息等多种格式。
    """

    def __init__(self):
        self.engine = MockLLMEngine()

    def parse_from_text(self, text: str, source: str = "") -> TaskList:
        """
        从文本中解析任务列表
        Args:
            text: 输入文本（邮件、待办清单等）
            source: 来源描述
        Returns:
            TaskList 对象
        """
        # 使用模拟引擎提取任务
        raw_result = self.engine.extract_tasks(text)
        tasks_raw = raw_result.get("tasks", [])

        task_list = TaskList(
            source_text=text,
            parsed_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        for i, t in enumerate(tasks_raw):
            task = TaskItem(
                id=self._generate_id(i),
                content=t.get("content", ""),
                responsible_person=t.get("responsible_person", ""),
                deadline=t.get("deadline", ""),
                priority=self._normalize_priority(t.get("priority", "中")),
                status=self._normalize_status(t.get("status", "待处理")),
                category=self._categorize_task(t.get("content", "")),
                source=source,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
            task_list.tasks.append(task)

        return task_list

    def parse_from_email(self, email_text: str) -> TaskList:
        """
        专门解析邮件内容中的任务
        """
        # 预处理邮件格式
        cleaned = self._clean_email_text(email_text)
        return self.parse_from_text(cleaned, source="邮件")

    def _generate_id(self, index: int) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"TASK-{timestamp}-{index + 1:03d}"

    def _normalize_priority(self, priority: str) -> str:
        """标准化优先级"""
        p = priority.lower()
        if p in ("高", "紧急", "urgent", "high", "critical", "highest"):
            return "高"
        elif p in ("低", "low", "lowest", "minor"):
            return "低"
        return "中"

    def _normalize_status(self, status: str) -> str:
        """标准化状态"""
        s = status.lower()
        if s in ("已完成", "done", "completed", "closed", "finish"):
            return "已完成"
        elif s in ("进行中", "in progress", "wip", "ongoing", "working"):
            return "进行中"
        return "待处理"

    def _categorize_task(self, content: str) -> str:
        """
        根据内容对任务进行分类
        分类: 文档 | 会议 | 审批 | 沟通 | 开发 | 测试 | 其他
        """
        categories = {
            "文档": ["文档", "报告", "protocol", "方案", "撰写", "编写", "更新文档"],
            "会议": ["会议", "meeting", "讨论", "评审", "汇报"],
            "审批": ["审批", "审核", "approve", "批准", "签字"],
            "沟通": ["沟通", "联系", "通知", "邮件", "协调", "确认"],
            "开发": ["开发", "编码", "coding", "实现", "implementation"],
            "测试": ["测试", "test", "验证", "validation", "qa"],
            "数据": ["数据", "data", "统计", "分析", "报告"],
        }

        content_lower = content.lower()
        max_score = 0
        best_category = "其他"

        for category, keywords in categories.items():
            score = sum(1 for kw in keywords if kw in content_lower)
            if score > max_score:
                max_score = score
                best_category = category

        return best_category

    def _clean_email_text(self, text: str) -> str:
        """清洗邮件文本，移除邮件头、签名等无关内容"""
        lines = text.split('\n')
        cleaned = []
        in_header = True
        in_signature = False

        for line in lines:
            # 跳过邮件头
            if in_header:
                header_patterns = [
                    r'^(发件人|收件人|抄送|密送|发送时间|主题|from|to|cc|bcc|subject):',
                    r'^>',
                    r'^---',
                    r'^-----',
                ]
                is_header = any(re.match(p, line, re.IGNORECASE) for p in header_patterns)
                if is_header:
                    continue
                in_header = False

            # 跳过签名
            if re.match(r'^(此致|祝好|best|regards|谢谢|--|__)', line.strip()):
                in_signature = True
            if in_signature:
                continue

            cleaned.append(line)

        return '\n'.join(cleaned)


# ============================================================
#  任务追踪器
# ============================================================

class TaskTracker:
    """
    任务追踪器 - 管理任务状态、进度和提醒通知。
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or Path("data/task_storage.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._tasks: Dict[str, TaskItem] = {}
        self._load()

    def _load(self):
        """从存储加载任务"""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for t in data.get("tasks", []):
                    item = TaskItem(**t)
                    self._tasks[item.id] = item
            except Exception as e:
                logger.error(f"加载任务存储失败: {e}")

    def _save(self):
        """保存任务到存储"""
        data = {
            "tasks": [t.to_dict() for t in self._tasks.values()],
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.storage_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_task(self, task: TaskItem) -> str:
        """添加单个任务"""
        if not task.id:
            task.id = self._generate_id()
        task.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._tasks[task.id] = task
        self._save()
        return task.id

    def add_task_list(self, task_list: TaskList) -> List[str]:
        """批量添加任务"""
        ids = []
        for task in task_list.tasks:
            ids.append(self.add_task(task))
        return ids

    def update_task(self, task_id: str, **updates) -> bool:
        """更新任务属性"""
        if task_id not in self._tasks:
            return False
        task = self._tasks[task_id]
        for key, value in updates.items():
            if hasattr(task, key):
                setattr(task, key, value)
        task.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._save()
        return True

    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save()
            return True
        return False

    def get_task(self, task_id: str) -> Optional[TaskItem]:
        """获取单个任务"""
        return self._tasks.get(task_id)

    def get_all_tasks(self, status: Optional[str] = None) -> List[TaskItem]:
        """获取所有任务，可按状态筛选"""
        tasks = list(self._tasks.values())
        if status:
            tasks = [t for t in tasks if t.status == status]
        return sorted(tasks, key=lambda t: t.created_at or "", reverse=True)

    def get_overdue_tasks(self) -> List[TaskItem]:
        """获取已过期的任务"""
        now = datetime.now()
        overdue = []
        for task in self._tasks.values():
            if task.status == "已完成":
                continue
            if task.deadline:
                try:
                    deadline = self._parse_deadline(task.deadline)
                    if deadline and deadline < now:
                        overdue.append(task)
                except:
                    continue
        return overdue

    def get_upcoming_tasks(self, days: int = 3) -> List[TaskItem]:
        """获取即将到期的任务"""
        now = datetime.now()
        end = now + timedelta(days=days)
        upcoming = []
        for task in self._tasks.values():
            if task.status == "已完成":
                continue
            if task.deadline:
                try:
                    deadline = self._parse_deadline(task.deadline)
                    if deadline and now <= deadline <= end:
                        upcoming.append(task)
                except:
                    continue
        return upcoming

    def get_tasks_by_person(self, person: str) -> List[TaskItem]:
        """按负责人筛选任务"""
        return [
            t for t in self._tasks.values()
            if t.responsible_person and person in t.responsible_person
        ]

    def get_stats(self) -> dict:
        """获取任务统计信息"""
        all_tasks = list(self._tasks.values())
        return {
            "total": len(all_tasks),
            "todo": sum(1 for t in all_tasks if t.status == "待处理"),
            "in_progress": sum(1 for t in all_tasks if t.status == "进行中"),
            "completed": sum(1 for t in all_tasks if t.status == "已完成"),
            "overdue": len(self.get_overdue_tasks()),
            "upcoming_3days": len(self.get_upcoming_tasks(3)),
        }

    def generate_reminder_text(self) -> str:
        """生成提醒文本"""
        overdue = self.get_overdue_tasks()
        upcoming = self.get_upcoming_tasks(3)
        stats = self.get_stats()

        parts = [f"📋 任务追踪日报 ({datetime.now().strftime('%Y-%m-%d')})\n"]
        parts.append(f"总览: 共 {stats['total']} 个任务 | "
                     f"待处理 {stats['todo']} | "
                     f"进行中 {stats['in_progress']} | "
                     f"已完成 {stats['completed']}")

        if overdue:
            parts.append(f"\n⚠️ 已过期任务 ({len(overdue)}个):")
            for t in overdue[:5]:
                parts.append(f"  - [{t.id}] {t.content} (负责人: {t.responsible_person or '-'})")

        if upcoming:
            parts.append(f"\n📅 近3日到期 ({len(upcoming)}个):")
            for t in upcoming[:5]:
                parts.append(f"  - [{t.id}] {t.content} (截止: {t.deadline})")

        return '\n'.join(parts)

    @staticmethod
    def _generate_id() -> str:
        return f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{id({})%1000:03d}"

    @staticmethod
    def _parse_deadline(date_str: str) -> Optional[datetime]:
        """解析截止日期字符串"""
        patterns = [
            r'(\d{4})[-/年](\d{1,2})[-/月](\d{1,2})[日]?',
            r'(\d{4})(\d{2})(\d{2})',
            r'(\d{1,2})[-/月](\d{1,2})[日]?',
        ]
        for pattern in patterns:
            m = re.search(pattern, date_str)
            if m:
                groups = m.groups()
                if len(groups) == 3:
                    return datetime(int(groups[0]), int(groups[1]), int(groups[2]))
                elif len(groups) == 2:
                    now = datetime.now()
                    return datetime(now.year, int(groups[0]), int(groups[1]))
        return None


# ============================================================
#  任务管理智能体
# ============================================================

class TaskManagerAgent(BaseAgent):
    """
    任务管理智能体 - 解析工作邮件和任务文本，
    提取结构化待办列表，支持任务跟进与提醒。
    """

    def __init__(self):
        super().__init__(
            agent_name="任务管理智能体",
            agent_description="解析工作邮件和待办文本，自动提取并整理任务清单"
        )
        self.parser = TaskParser()
        self.tracker = TaskTracker()

    def process(self, task_input: TaskInput) -> TaskResult:
        """
        处理任务管理相关输入
        支持: 邮件解析, 任务清单解析, 任务查询
        """
        try:
            start_time = datetime.now()
            metadata = task_input.metadata or {}
            mode = metadata.get("mode", "parse")

            if mode == "parse":
                # 解析任务
                source = metadata.get("source", "")
                if task_input.input_type == "email":
                    task_list = self.parser.parse_from_email(task_input.content)
                else:
                    task_list = self.parser.parse_from_text(task_input.content, source)

                # 保存到追踪器
                ids = self.tracker.add_task_list(task_list)

                elapsed = (datetime.now() - start_time).total_seconds()

                return TaskResult(
                    success=True,
                    task_type="task_management",
                    output={
                        "parsed_tasks": task_list.to_dict(),
                        "task_ids": ids,
                        "stats": {
                            "total": task_list.to_dict()["total_count"],
                            "todo": task_list.to_dict()["todo_count"],
                            "in_progress": task_list.to_dict()["in_progress_count"],
                            "completed": task_list.to_dict()["completed_count"],
                        },
                    },
                    processing_time=elapsed,
                )

            elif mode == "query":
                # 查询任务
                query_type = metadata.get("query_type", "all")
                if query_type == "overdue":
                    tasks = self.tracker.get_overdue_tasks()
                elif query_type == "upcoming":
                    days = metadata.get("days", 3)
                    tasks = self.tracker.get_upcoming_tasks(days)
                elif query_type == "person":
                    person = metadata.get("person", "")
                    tasks = self.tracker.get_tasks_by_person(person)
                else:
                    tasks = self.tracker.get_all_tasks()

                elapsed = (datetime.now() - start_time).total_seconds()

                return TaskResult(
                    success=True,
                    task_type="task_management",
                    output={
                        "tasks": [t.to_dict() for t in tasks],
                        "stats": self.tracker.get_stats(),
                        "reminder_text": self.tracker.generate_reminder_text(),
                    },
                    processing_time=elapsed,
                )

            elif mode == "reminder":
                # 生成提醒
                elapsed = (datetime.now() - start_time).total_seconds()
                return TaskResult(
                    success=True,
                    task_type="task_management",
                    output={
                        "reminder_text": self.tracker.generate_reminder_text(),
                        "stats": self.tracker.get_stats(),
                    },
                    processing_time=elapsed,
                )

            else:
                return TaskResult(
                    success=False,
                    task_type="task_management",
                    error_message=f"不支持的操作模式: {mode}",
                )

        except Exception as e:
            logger.error(f"任务管理处理失败: {str(e)}", exc_info=True)
            return TaskResult(
                success=False,
                task_type="task_management",
                error_message=f"处理任务时出错: {str(e)}",
            )
