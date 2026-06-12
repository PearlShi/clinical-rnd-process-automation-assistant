"""
============================================================
  test_agent.py - 智能体框架测试
  临床研发流程自动化助手
============================================================
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))


def test_task_input_creation():
    """测试 TaskInput 创建"""
    from app.agent.base_agent import TaskInput

    input_data = TaskInput(
        input_type="meeting_transcript",
        content="这是一段会议文本",
    )
    assert input_data.input_type == "meeting_transcript"
    assert input_data.content == "这是一段会议文本"
    assert input_data.file_path is None


def test_orchestrator_registration():
    """测试智能体注册"""
    from app.agent.base_agent import get_orchestrator, reset_orchestrator
    from app.modules.meeting_minutes import MeetingMinutesAgent
    from app.modules.doc_compare import DocCompareAgent
    from app.modules.task_manager import TaskManagerAgent

    reset_orchestrator()
    orchestrator = get_orchestrator()

    orchestrator.register_agent("meeting_minutes", MeetingMinutesAgent())
    orchestrator.register_agent("doc_compare", DocCompareAgent())
    orchestrator.register_agent("task_management", TaskManagerAgent())

    agents = orchestrator.get_registered_agents()
    assert len(agents) == 3
    assert "meeting_minutes" in agents
    assert "doc_compare" in agents
    assert "task_management" in agents


def test_task_routing_meeting():
    """测试会议纪要路由"""
    from app.agent.base_agent import TaskRouter, TaskInput

    router = TaskRouter()
    task_input = TaskInput(
        input_type="meeting_transcript",
        content="会议主题：项目进度评审\n参会人员：张三、李四\n讨论内容...",
    )
    task_type = router.route(task_input)
    assert task_type == "meeting_minutes"


def test_task_routing_protocol():
    """测试文档对比路由"""
    from app.agent.base_agent import TaskRouter, TaskInput

    router = TaskRouter()
    task_input = TaskInput(
        input_type="protocol",
        content="临床试验方案 V1.0\n入选标准\n排除标准",
    )
    task_type = router.route(task_input)
    assert task_type == "doc_compare"


def test_task_routing_email():
    """测试任务管理路由"""
    from app.agent.base_agent import TaskRouter, TaskInput

    router = TaskRouter()
    task_input = TaskInput(
        input_type="email",
        content="发件人: test@example.com\n本周待办事项",
    )
    task_type = router.route(task_input)
    assert task_type == "task_management"


def test_meeting_minutes_agent():
    """测试会议纪要智能体"""
    from app.agent.base_agent import TaskInput, get_orchestrator, reset_orchestrator
    from app.modules.meeting_minutes import MeetingMinutesAgent

    reset_orchestrator()
    orchestrator = get_orchestrator()
    orchestrator.register_agent("meeting_minutes", MeetingMinutesAgent())

    task_input = TaskInput(
        input_type="meeting_transcript",
        content="会议主题：项目进度评审\n参会人员：张三、李四\n讨论内容：项目进度正常",
    )
    result = orchestrator.process(task_input)
    assert result.success
    assert result.task_type == "meeting_minutes"
    assert result.output is not None
    assert "structured" in result.output
    assert "markdown" in result.output


def test_doc_compare_agent():
    """测试文档对比智能体"""
    from app.agent.base_agent import TaskInput, get_orchestrator, reset_orchestrator
    from app.modules.doc_compare import DocCompareAgent

    reset_orchestrator()
    orchestrator = get_orchestrator()
    orchestrator.register_agent("doc_compare", DocCompareAgent())

    text_old = "入选标准：年龄18-75岁\n排除标准：免疫治疗史"
    text_new = "入选标准：年龄18-80岁\n排除标准：免疫治疗史\n排除标准：心血管疾病史"

    task_input = TaskInput(
        input_type="protocol",
        content=text_new,
        metadata={"text_old": text_old, "text_new": text_new, "doc_type": "protocol"},
    )
    result = orchestrator.process(task_input)
    assert result.success
    assert result.task_type == "doc_compare"
    assert result.output is not None
    assert "stats" in result.output
    assert "changes" in result.output


def test_task_management_agent():
    """测试任务管理智能体"""
    from app.agent.base_agent import TaskInput, get_orchestrator, reset_orchestrator
    from app.modules.task_manager import TaskManagerAgent

    reset_orchestrator()
    orchestrator = get_orchestrator()
    orchestrator.register_agent("task_management", TaskManagerAgent())

    text = "- [ ] 完成报告，负责人：张三，截止日期：2026年6月20日\n- [x] 提交申请"
    task_input = TaskInput(
        input_type="task_list",
        content=text,
        metadata={"mode": "parse"},
    )
    result = orchestrator.process(task_input)
    assert result.success
    assert result.task_type == "task_management"
    assert result.output is not None
    assert "parsed_tasks" in result.output


def test_file_type_detection():
    """测试文件类型检测"""
    from app.utils.file_utils import detect_file_type, is_audio_file, is_document_file

    assert detect_file_type("test.mp3") == "audio"
    assert detect_file_type("test.wav") == "audio"
    assert detect_file_type("test.docx") == "document"
    assert detect_file_type("test.pdf") == "document"
    assert detect_file_type("test.txt") == "text"
    assert detect_file_type("test.md") == "text"
    assert detect_file_type("test.xyz") == "unknown"

    assert is_audio_file("test.mp3") is True
    assert is_audio_file("test.docx") is False
    assert is_document_file("test.docx") is True


def test_content_type_guessing():
    """测试内容类型猜测"""
    from app.utils.file_utils import guess_content_type_from_content

    assert guess_content_type_from_content("会议主题：讨论\n参会人：张三") == "meeting_transcript"
    assert guess_content_type_from_content("临床试验方案 V1.0") == "protocol"
    assert guess_content_type_from_content("知情同意书") == "icf"
    assert guess_content_type_from_content("发件人: test@test.com") == "email"
    assert guess_content_type_from_content("待办：完成报告\n负责人：张三") == "task_list"


def test_plugin_base():
    """测试插件基类"""
    from app.plugins import BasePlugin

    class TestPlugin(BasePlugin):
        plugin_name = "测试插件"
        plugin_version = "1.0.0"
        plugin_description = "测试用插件"

        def execute(self, input_data, **kwargs):
            return {"success": True, "data": input_data}

    plugin = TestPlugin()
    info = plugin.get_info()
    assert info["name"] == "测试插件"
    assert info["version"] == "1.0.0"
    assert info["enabled"] is True

    result = plugin.execute("test")
    assert result["success"] is True
    assert result["data"] == "test"


def test_task_tracker():
    """测试任务追踪器"""
    from app.modules.task_manager import TaskItem, TaskTracker
    import tempfile
    import json

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump({"tasks": []}, f)
        temp_path = f.name

    try:
        tracker = TaskTracker(storage_path=Path(temp_path))

        # 添加任务
        task = TaskItem(
            content="测试任务",
            responsible_person="张三",
            deadline="2026-06-20",
            priority="高",
        )
        task_id = tracker.add_task(task)
        assert task_id is not None

        # 获取任务
        fetched = tracker.get_task(task_id)
        assert fetched is not None
        assert fetched.content == "测试任务"

        # 更新任务
        tracker.update_task(task_id, status="已完成")
        updated = tracker.get_task(task_id)
        assert updated.status == "已完成"

        # 统计
        stats = tracker.get_stats()
        assert stats["total"] >= 1
        assert stats["completed"] >= 1

    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_doc_text_extractor():
    """测试文档文本提取"""
    from app.modules.doc_compare import DocTextExtractor
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("临床试验方案测试内容")
        temp_path = f.name

    try:
        success, text, error = DocTextExtractor.extract(Path(temp_path))
        assert success
        assert "临床试验方案" in text
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_all_agents_end_to_end():
    """端到端测试 - 所有智能体"""
    from app.agent.base_agent import TaskInput, get_orchestrator, reset_orchestrator
    from app.modules.meeting_minutes import MeetingMinutesAgent
    from app.modules.doc_compare import DocCompareAgent
    from app.modules.task_manager import TaskManagerAgent

    reset_orchestrator()
    orchestrator = get_orchestrator()
    orchestrator.register_agent("meeting_minutes", MeetingMinutesAgent())
    orchestrator.register_agent("doc_compare", DocCompareAgent())
    orchestrator.register_agent("task_management", TaskManagerAgent())

    # 测试会议纪要
    result1 = orchestrator.process(TaskInput(
        input_type="meeting_transcript",
        content="会议主题：进度会\n参会人员：张三、李四\n讨论内容：项目进展",
    ))
    assert result1.success

    # 测试文档对比
    result2 = orchestrator.process(TaskInput(
        input_type="protocol",
        content="新版本内容",
        metadata={
            "text_old": "旧版本内容",
            "text_new": "新版本内容",
            "doc_type": "protocol",
        },
    ))
    assert result2.success

    # 测试任务管理
    result3 = orchestrator.process(TaskInput(
        input_type="task_list",
        content="- [ ] 完成任务A\n- [x] 完成任务B",
        metadata={"mode": "parse"},
    ))
    assert result3.success


if __name__ == "__main__":
    # 手动运行测试
    test_task_input_creation()
    test_orchestrator_registration()
    test_task_routing_meeting()
    test_task_routing_protocol()
    test_task_routing_email()
    test_meeting_minutes_agent()
    test_doc_compare_agent()
    test_task_management_agent()
    test_file_type_detection()
    test_content_type_guessing()
    test_plugin_base()
    test_task_tracker()
    test_doc_text_extractor()
    test_all_agents_end_to_end()

    print("\n" + "=" * 50)
    print("✅ 所有测试通过！")
    print("=" * 50)
