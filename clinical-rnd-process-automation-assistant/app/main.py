"""
============================================================
  main.py - 应用主入口
  临床研发流程自动化助手
============================================================
  基于 FastAPI 的 Web API 服务。
  提供 RESTful 接口供前端调用。
============================================================
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ---------- 日志配置 ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT_DIR / "logs" / "app.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# ============================================================
#  应用初始化
# ============================================================

def initialize_app():
    """
    初始化应用 - 注册核心智能体、加载插件配置
    """
    from app.plugins import register_core_agents, get_plugin_manager

    # 注册核心智能体
    register_core_agents()
    logger.info("核心智能体注册完成")

    # 加载插件配置
    plugin_manager = get_plugin_manager()
    plugin_manager.load_all_from_config()
    logger.info(f"插件加载完成，共 {len(plugin_manager.get_all_plugins())} 个插件")

    return True


# 启动时初始化
initialize_app()


# ============================================================
#  FastAPI 应用
# ============================================================

try:
    from fastapi import FastAPI, UploadFile, File, Form, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import HTMLResponse, JSONResponse

    app = FastAPI(
        title="临床研发流程自动化助手 API",
        description="基于AI智能体技术的临床研发工作流自动化工具",
        version="1.0.0",
    )

    # CORS 配置（允许 Streamlit 前端跨域访问）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---------- 导入核心模块 ----------
    from app.agent.base_agent import (
        TaskInput, get_orchestrator, AgentOrchestrator
    )
    from app.utils.file_utils import (
        save_uploaded_file, detect_file_type,
        guess_content_type_from_content, read_text_file
    )

    # ========================================
    #  API 路由
    # ========================================

    @app.get("/")
    def root():
        """服务健康检查"""
        return {
            "app": "临床研发流程自动化助手",
            "version": "1.0.0",
            "status": "running",
            "time": datetime.now().isoformat(),
        }

    @app.get("/agents")
    def list_agents():
        """获取所有已注册的智能体"""
        orchestrator = get_orchestrator()
        return {
            "agents": orchestrator.get_registered_agents(),
            "count": len(orchestrator.get_registered_agents()),
        }

    @app.get("/plugins")
    def list_plugins():
        """获取所有已加载的插件"""
        from app.plugins import get_plugin_manager
        pm = get_plugin_manager()
        return {
            "plugins": pm.get_plugins_summary(),
            "count": len(pm.get_all_plugins()),
        }

    # ========================================
    #  统一处理接口
    # ========================================

    @app.post("/process")
    async def process_input(
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
        input_type: Optional[str] = Form("auto"),
        mode: Optional[str] = Form(None),
        doc_type: Optional[str] = Form(None),
    ):
        """
        统一智能体处理入口 - 自动识别并路由到对应任务处理器

        Args:
            text: 输入文本（可选，与文件二选一）
            file: 上传文件（可选，与文本二选一）
            input_type: 输入类型 (auto | meeting_transcript | meeting_audio | protocol | icf | email | task_list)
            mode: 任务模式（用于 task_management: parse | query | reminder）
            doc_type: 文档类型（用于 doc_compare: protocol | icf）
        Returns:
            处理结果
        """
        orchestrator = get_orchestrator()
        content = ""
        file_path = None

        # 处理文件上传
        if file:
            saved_path = save_uploaded_file(file, sub_dir="uploads")
            file_path = saved_path

            # 尝试读取文件内容
            file_type = detect_file_type(file.filename or "")
            if file_type in ("document", "text"):
                content = read_text_file(saved_path)
            elif file_type == "audio":
                input_type = "meeting_audio"
            else:
                # 尝试作为文本读取
                try:
                    content = read_text_file(saved_path)
                except:
                    pass
        elif text:
            content = text

        if not content and not file_path:
            raise HTTPException(status_code=400, detail="请提供文本内容或上传文件")

        # 自动检测输入类型
        if input_type == "auto" or not input_type:
            if content:
                detected = guess_content_type_from_content(content)
            elif file_path:
                detected = detect_file_type(str(file_path))
            else:
                detected = "unknown"
            input_type = detected

        # 构建任务输入
        metadata = {}
        if mode:
            metadata["mode"] = mode
        if doc_type:
            metadata["doc_type"] = doc_type

        task_input = TaskInput(
            input_type=input_type,
            content=content,
            file_path=file_path,
            metadata=metadata,
        )

        # 执行处理
        result = orchestrator.process(task_input)

        return {
            "success": result.success,
            "task_type": result.task_type,
            "output": result.output,
            "error": result.error_message if not result.success else None,
            "processing_time": result.processing_time,
        }

    # ========================================
    #  会议纪要专用接口
    # ========================================

    @app.post("/meeting-minutes")
    async def create_meeting_minutes(
        text: Optional[str] = Form(None),
        file: Optional[UploadFile] = File(None),
    ):
        """生成会议纪要"""
        return await process_input(text=text, file=file, input_type="meeting_transcript")

    @app.post("/meeting-minutes/audio")
    async def create_meeting_minutes_from_audio(
        file: UploadFile = File(...),
    ):
        """从录音文件生成会议纪要"""
        return await process_input(file=file, input_type="meeting_audio")

    # ========================================
    #  文档对比专用接口
    # ========================================

    @app.post("/doc-compare")
    async def compare_documents(
        text_old: str = Form(...),
        text_new: str = Form(...),
        doc_type: str = Form("protocol"),
    ):
        """对比两个版本文本"""
        orchestrator = get_orchestrator()
        task_input = TaskInput(
            input_type=doc_type,
            content=text_new,
            metadata={
                "text_old": text_old,
                "text_new": text_new,
                "doc_type": doc_type,
            },
        )
        result = orchestrator.process(task_input)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error_message if not result.success else None,
        }

    @app.post("/doc-compare/files")
    async def compare_document_files(
        file_old: UploadFile = File(...),
        file_new: UploadFile = File(...),
        doc_type: str = Form("protocol"),
    ):
        """对比两个版本文档文件"""
        old_path = save_uploaded_file(file_old, sub_dir="compare")
        new_path = save_uploaded_file(file_new, sub_dir="compare")

        from app.modules.doc_compare import DocTextExtractor
        extractor = DocTextExtractor()

        success1, text_old, err1 = extractor.extract(old_path)
        success2, text_new, err2 = extractor.extract(new_path)

        if not success1:
            raise HTTPException(status_code=400, detail=f"无法读取旧版本文件: {err1}")
        if not success2:
            raise HTTPException(status_code=400, detail=f"无法读取新版本文件: {err2}")

        orchestrator = get_orchestrator()
        task_input = TaskInput(
            input_type=doc_type,
            content=text_new,
            metadata={
                "text_old": text_old,
                "text_new": text_new,
                "doc_type": doc_type,
            },
        )
        result = orchestrator.process(task_input)
        return {
            "success": result.success,
            "output": result.output,
            "error": result.error_message if not result.success else None,
        }

    # ========================================
    #  任务管理专用接口
    # ========================================

    @app.post("/tasks/parse")
    async def parse_tasks(
        text: str = Form(...),
        source: str = Form(""),
    ):
        """从文本中解析任务"""
        return await process_input(
            text=text, input_type="task_list",
            mode="parse",
        )

    @app.get("/tasks")
    def get_all_tasks(status: Optional[str] = None):
        """获取所有任务"""
        from app.modules.task_manager import TaskTracker
        tracker = TaskTracker()
        tasks = tracker.get_all_tasks(status)

        return {
            "tasks": [t.to_dict() for t in tasks],
            "stats": tracker.get_stats(),
            "count": len(tasks),
        }

    @app.get("/tasks/overdue")
    def get_overdue_tasks():
        """获取已过期任务"""
        from app.modules.task_manager import TaskTracker
        tracker = TaskTracker()
        tasks = tracker.get_overdue_tasks()
        return {
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
        }

    @app.get("/tasks/upcoming")
    def get_upcoming_tasks(days: int = 3):
        """获取即将到期任务"""
        from app.modules.task_manager import TaskTracker
        tracker = TaskTracker()
        tasks = tracker.get_upcoming_tasks(days)
        return {
            "tasks": [t.to_dict() for t in tasks],
            "count": len(tasks),
        }

    @app.get("/tasks/reminder")
    def get_reminder():
        """获取提醒文本"""
        from app.modules.task_manager import TaskTracker
        tracker = TaskTracker()
        return {
            "reminder_text": tracker.generate_reminder_text(),
            "stats": tracker.get_stats(),
        }

    @app.post("/tasks/{task_id}/update")
    async def update_task(task_id: str, status: str = Form(None), notes: str = Form(None)):
        """更新任务状态"""
        from app.modules.task_manager import TaskTracker
        tracker = TaskTracker()
        updates = {}
        if status:
            updates["status"] = status
        if notes:
            updates["notes"] = notes
        success = tracker.update_task(task_id, **updates)
        return {"success": success, "task_id": task_id}

    # ========================================
    #  文件上传（通用）
    # ========================================

    @app.post("/upload")
    async def upload_file(file: UploadFile = File(...)):
        """通用文件上传"""
        saved_path = save_uploaded_file(file, sub_dir="uploads")
        return {
            "success": True,
            "file_path": str(saved_path),
            "file_name": saved_path.name,
            "file_size": saved_path.stat().st_size,
        }

    @app.get("/health")
    def health_check():
        """详细健康检查"""
        return {
            "status": "healthy",
            "app": "临床研发流程自动化助手",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "meeting_minutes": True,
                "doc_compare": True,
                "task_management": True,
            },
            "plugins_loaded": len(get_plugin_manager().get_all_plugins()),
        }

except ImportError:
    # 如果 FastAPI 未安装，提供降级提示
    logger.warning("FastAPI 未安装，API 服务不可用。请安装依赖: pip install -r requirements.txt")

    # 创建一个占位 app 对象
    class PlaceholderApp:
        def __init__(self):
            self.title = "临床研发流程自动化助手 (API 模式未安装)"

        def __call__(self, *args, **kwargs):
            return {"error": "FastAPI 未安装，请运行: pip install fastapi uvicorn"}

    app = PlaceholderApp()


# ============================================================
#  直接运行入口
# ============================================================

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════╗
║     临床研发流程自动化助手 v1.0.0                ║
║   Clinical R&D Process Automation Assistant      ║
╚══════════════════════════════════════════════════╝

启动方式:
  1. Web UI (推荐): streamlit run ui/app.py
  2. API 服务:     uvicorn app.main:app --host 0.0.0.0 --port 8000
  3. 测试模式:     python -m pytest tests/

系统状态:
  - 核心智能体: 已注册 (会议纪要 / 文档对比 / 任务管理)
  - 插件架构:   就绪
  - 配置:       config/plugins.json, config/tasks.json

部署方式:
  docker-compose up

更多信息请参阅: docs/user_manual.md
""")
