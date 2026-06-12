"""
============================================================
  ui/app.py - Streamlit 主应用
  临床研发流程自动化助手
============================================================
  整合页面导航、样式、和各功能页面。
  启动方式: streamlit run ui/app.py
============================================================
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

# ---------- 页面配置（必须在第一个 st 命令之前） ----------
st.set_page_config(
    page_title="临床研发流程自动化助手",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- 导入模块 ----------
from app.agent.base_agent import get_orchestrator, TaskInput
from app.config import APP_NAME, APP_VERSION, is_mock_mode
from app.plugins import register_core_agents


# ============================================================
#  会话状态初始化
# ============================================================

def init_session_state():
    """初始化 Streamlit 会话状态"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.agent_mode = is_mock_mode()
        st.session_state.task_results = []
        st.session_state.current_page = "首页"

        # 注册智能体（如未注册）
        try:
            register_core_agents()
        except Exception as e:
            pass

    # 确保子页面状态
    if "meeting_result" not in st.session_state:
        st.session_state.meeting_result = None
    if "compare_result" not in st.session_state:
        st.session_state.compare_result = None
    if "task_result" not in st.session_state:
        st.session_state.task_result = None
    if "extracted_tasks" not in st.session_state:
        st.session_state.extracted_tasks = None


init_session_state()


# ============================================================
#  侧边栏导航
# ============================================================

def render_sidebar():
    """渲染侧边栏导航"""
    with st.sidebar:
        # 应用标题
        st.markdown("""
        <div style="text-align: center; padding: 10px 0;">
            <h2 style="color: #2c3e50; margin: 0;">🏥 临床研发</h2>
            <h3 style="color: #3498db; margin: 0;">流程自动化助手</h3>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # 导航菜单
        st.markdown("### 📋 功能导航")

        pages = {
            "首页": {"icon": "🏠", "desc": "系统概览"},
            "会议纪要": {"icon": "📝", "desc": "自动生成会议纪要"},
            "文档对比": {"icon": "📄", "desc": "临床文档版本对比"},
            "任务管理": {"icon": "✅", "desc": "任务解析与追踪"},
            "插件管理": {"icon": "🔌", "desc": "插件配置与管理"},
        }

        for page_name, info in pages.items():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(info["icon"])
            with col2:
                if st.button(
                    page_name,
                    key=f"nav_{page_name}",
                    use_container_width=True,
                    type="secondary" if st.session_state.current_page != page_name else "primary",
                ):
                    st.session_state.current_page = page_name
                    st.rerun()

        st.divider()

        # 系统信息
        st.markdown("### ℹ️ 系统信息")
        st.caption(f"版本: {APP_VERSION}")
        st.caption(f"AI模式: {'🟡 模拟模式' if is_mock_mode() else '🟢 LLM模式'}")
        st.caption(f"智能体: {len(get_orchestrator().get_registered_agents())} 个已注册")

        # 智能体列表
        agents = get_orchestrator().get_registered_agents()
        if agents:
            with st.expander("已注册的智能体"):
                for task_type, name in agents.items():
                    st.caption(f"• {name} ({task_type})")

        st.divider()

        # 页脚
        st.caption("© 2026 AI 临床研发自动化开源演示项目")


# ============================================================
#  页面渲染
# ============================================================

def render_home():
    """首页"""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("""
        # 🏥 临床研发流程自动化助手

        **基于AI智能体技术的临床研发工作流自动化工具**

        本工具面向企业内部办公场景设计，用于优化临床研发部门日常工作流程，
        减少人工操作成本，提升临床研发全流程的工作效率。
        """)

        # 功能卡片
        st.markdown("## 🚀 核心功能")

        cards = [
            {
                "icon": "📝",
                "title": "会议纪要自动生成",
                "desc": "上传会议录音或文字转录文本，智能提取核心议题、关键决策、行动项，结构化输出标准会议纪要。",
                "page": "会议纪要",
            },
            {
                "icon": "📄",
                "title": "临床文档版本对比",
                "desc": "针对Protocol和ICF文档，支持上传两个不同版本，自动标记新增、修改、删减内容，生成差异报告。",
                "page": "文档对比",
            },
            {
                "icon": "✅",
                "title": "任务提醒与进度追踪",
                "desc": "解析工作邮件、零散任务清单，自动提取任务信息，统一整理为结构化待办列表，实现跟进与提醒。",
                "page": "任务管理",
            },
            {
                "icon": "🔌",
                "title": "可扩展插件架构",
                "desc": "插件化设计，预留扩展接口，支持快速新增自动化任务，通过配置文件统一管理。",
                "page": "插件管理",
            },
        ]

        cols = st.columns(2)
        for i, card in enumerate(cards):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"### {card['icon']} {card['title']}")
                    st.write(card["desc"])
                    if st.button(f"进入 {card['title']}", key=f"go_{i}"):
                        st.session_state.current_page = card["page"]
                        st.rerun()

    with col2:
        st.markdown("## 📊 系统状态")

        with st.container(border=True):
            st.markdown("### 智能体运行状态")
            agents = get_orchestrator().get_registered_agents()
            for task_type, name in agents.items():
                st.markdown(f"- ✅ **{name}**")

        with st.container(border=True):
            st.markdown("### 系统信息")
            st.markdown(f"- **应用版本**: {APP_VERSION}")
            st.markdown(f"- **AI引擎**: {'模拟模式 (Mock)' if is_mock_mode() else 'LLM模式'}")
            st.markdown(f"- **状态**: 🟢 运行正常")

        with st.container(border=True):
            st.markdown("### 快速上手")
            st.markdown("""
            1. 左侧导航选择功能
            2. 上传文件或输入文本
            3. 点击处理按钮获取结果
            4. 下载或导出处理结果
            """)


def render_meeting_page():
    """会议纪要页面"""
    st.markdown("# 📝 会议纪要自动生成")

    st.info(
        "支持上传**会议录音文件**或粘贴**会议文字转录文本**，"
        "智能提取会议核心议题、关键决策、待执行行动项、相关责任人与时间要求。"
    )

    tab1, tab2 = st.tabs(["📝 文本输入", "🎤 音频上传"])

    with tab1:
        st.markdown("### 输入会议转录文本")
        meeting_text = st.text_area(
            "会议转录内容",
            placeholder="请粘贴会议转录文本...\n\n"
                       "示例格式：\n"
                       "会议主题：项目进度评审会议\n"
                       "时间：2026年6月12日 14:00\n"
                       "参会人员：张三、李四、王五\n"
                       "讨论内容：...",
            height=300,
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("📋 加载示例", use_container_width=True):
                st.session_state.meeting_example = (
                    "会议主题：三期临床试验中期分析讨论会\n"
                    "时间：2026年6月10日 10:00-11:30\n"
                    "地点：A栋3楼会议室\n"
                    "参会人员：张主任、李教授、王博士、赵经理、刘总监\n\n"
                    "议题一：中期分析结果汇报\n"
                    "王博士汇报了本次中期分析的主要结果。主要终点已达到预设的优效性界值，"
                    "安全性数据与前期观察一致，未出现新的安全信号。建议按照DMC建议继续推进研究。\n\n"
                    "议题二：数据截止日期讨论\n"
                    "经过讨论，确定将数据截止日期定为2026年6月30日。要求各研究中心在6月25日前完成数据录入。\n\n"
                    "议题三：后续研究计划\n"
                    "张主任建议提前准备NDA申报材料。李教授补充需要关注亚组分析结果。\n\n"
                    "关键决策：\n"
                    "1. 批准中期分析结果，按计划推进三期临床研究\n"
                    "2. 数据截止日期确定为2026年6月30日\n"
                    "3. 启动NDA申报准备工作\n\n"
                    "行动项：\n"
                    "- [ ] 王博士: 完成中期分析报告终稿，截止日期6月20日，高优先级\n"
                    "- [ ] 赵经理: 通知各研究中心数据截止日期，截止日期6月11日\n"
                    "- [ ] 张主任: 组建NDA申报工作组，截止日期6月15日\n"
                    "- [ ] 李教授: 完成亚组分析计划，截止日期6月25日"
                )

        with col2:
            if st.button("🚀 生成会议纪要", type="primary", use_container_width=True):
                if meeting_text or "meeting_example" in st.session_state:
                    if not meeting_text and "meeting_example" in st.session_state:
                        meeting_text = st.session_state.meeting_example
                    with st.spinner("正在生成会议纪要..."):
                        orchestrator = get_orchestrator()
                        task_input = TaskInput(
                            input_type="meeting_transcript",
                            content=meeting_text,
                        )
                        result = orchestrator.process(task_input)
                        st.session_state.meeting_result = result
                else:
                    st.warning("请先输入会议转录文本或点击「加载示例」")

    with tab2:
        st.markdown("### 上传会议录音文件")
        uploaded_audio = st.file_uploader(
            "选择录音文件 (支持 mp3, wav, m4a, ogg)",
            type=["mp3", "wav", "m4a", "ogg"],
        )

        if uploaded_audio:
            st.audio(uploaded_audio)
            if st.button("🎤 识别并生成会议纪要", type="primary"):
                with st.spinner("正在处理录音文件..."):
                    from app.utils.file_utils import save_uploaded_file
                    saved_path = save_uploaded_file(uploaded_audio, sub_dir="meeting_audio")
                    orchestrator = get_orchestrator()
                    task_input = TaskInput(
                        input_type="meeting_audio",
                        content="",
                        file_path=saved_path,
                    )
                    result = orchestrator.process(task_input)
                    st.session_state.meeting_result = result

    # 显示结果
    if st.session_state.meeting_result:
        result = st.session_state.meeting_result
        if result.success:
            output = result.output

            st.markdown("---")
            st.markdown("## ✅ 会议纪要生成完成")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("参会人员", len(output.get("participants", [])))
            with col2:
                st.metric("关键决策", len(output.get("structured", {}).get("key_decisions", [])))
            with col3:
                st.metric("行动项", len(output.get("action_items", [])))

            # 显示结构化会议纪要
            with st.expander("📋 查看结构化会议纪要", expanded=True):
                structured = output.get("structured", {})

                st.markdown(f"### {structured.get('title', '会议纪要')}")
                st.markdown(f"**会议时间**: {structured.get('meeting_time', '')}")
                st.markdown(f"**参会人员**: {'、'.join(structured.get('participants', []))}")
                st.markdown(f"**摘要**: {structured.get('summary', '')}")

                st.markdown("#### 核心议题")
                for topic in structured.get("core_topics", []):
                    with st.container(border=True):
                        st.markdown(f"**{topic['title']}**")
                        st.write(topic['content'])

                st.markdown("#### 关键决策")
                for d in structured.get("key_decisions", []):
                    st.markdown(f"- ✅ {d['content']}")

                st.markdown("#### 行动项")
                items_table = []
                for item in structured.get("action_items", []):
                    items_table.append({
                        "内容": item['content'],
                        "负责人": item.get('responsible_person', ''),
                        "截止日期": item.get('deadline', ''),
                        "优先级": item.get('priority', '中'),
                    })
                if items_table:
                    st.dataframe(items_table, use_container_width=True)

            # 显示 Markdown 版本
            with st.expander("📝 查看Markdown格式"):
                st.code(output.get("markdown", ""), language="markdown")

        else:
            st.error(f"处理失败: {result.error_message}")


def render_compare_page():
    """文档对比页面"""
    st.markdown("# 📄 临床文档版本对比")

    st.info(
        "针对**临床试验方案（Protocol）**和**知情同意书（ICF）**两类临床文档，"
        "支持上传两个不同版本的文件，自动比对全文内容，标记新增/修改/删减内容。"
    )

    tab1, tab2 = st.tabs(["📤 文件上传对比", "✏️ 文本粘贴对比"])

    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 旧版本文件")
            file_old = st.file_uploader(
                "选择旧版本文档",
                type=["docx", "pdf", "txt", "md"],
                key="file_old",
            )
        with col2:
            st.markdown("### 新版本文件")
            file_new = st.file_uploader(
                "选择新版本文档",
                type=["docx", "pdf", "txt", "md"],
                key="file_new",
            )

        doc_type_1 = st.selectbox(
            "文档类型",
            options=["protocol", "icf"],
            format_func=lambda x: {"protocol": "临床试验方案 (Protocol)", "icf": "知情同意书 (ICF)"}[x],
        )

        if st.button("🚀 开始对比", type="primary", use_container_width=True):
            if file_old and file_new:
                with st.spinner("正在对比文档..."):
                    from app.utils.file_utils import save_uploaded_file
                    old_path = save_uploaded_file(file_old, sub_dir="compare")
                    new_path = save_uploaded_file(file_new, sub_dir="compare")

                    from app.modules.doc_compare import DocTextExtractor
                    extractor = DocTextExtractor()
                    success1, text_old, err1 = extractor.extract(old_path)
                    success2, text_new, err2 = extractor.extract(new_path)

                    if success1 and success2:
                        orchestrator = get_orchestrator()
                        task_input = TaskInput(
                            input_type=doc_type_1,
                            content=text_new,
                            metadata={
                                "text_old": text_old,
                                "text_new": text_new,
                                "doc_type": doc_type_1,
                            },
                        )
                        result = orchestrator.process(task_input)
                        st.session_state.compare_result = result
                    else:
                        st.error(f"文件读取失败: {err1 or err2}")
            else:
                st.warning("请上传两个版本的文档文件")

    with tab2:
        st.markdown("### 粘贴文档文本")

        col1, col2 = st.columns(2)
        with col1:
            text_old = st.text_area(
                "旧版本文本",
                height=250,
                placeholder="在此粘贴旧版本文档的文本内容...",
                key="text_old_input",
            )
        with col2:
            text_new = st.text_area(
                "新版本文本",
                height=250,
                placeholder="在此粘贴新版本文档的文本内容...",
                key="text_new_input",
            )

        doc_type_2 = st.selectbox(
            "文档类型",
            options=["protocol", "icf"],
            format_func=lambda x: {"protocol": "临床试验方案 (Protocol)", "icf": "知情同意书 (ICF)"}[x],
            key="doc_type_2",
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("📋 加载示例", key="load_example_compare", use_container_width=True):
                st.session_state.text_old_input = (
                    "临床试验方案 V1.0\n\n"
                    "1. 入选标准\n"
                    "1.1 年龄在18-75岁之间\n"
                    "1.2 经组织学或细胞学确诊为非小细胞肺癌\n"
                    "1.3 ECOG体能评分0-1分\n"
                    "1.4 预期生存期≥12周\n\n"
                    "2. 排除标准\n"
                    "2.1 既往接受过免疫治疗\n"
                    "2.2 有活动性自身免疫性疾病\n"
                    "2.3 有间质性肺病病史"
                )
                st.session_state.text_new_input = (
                    "临床试验方案 V2.0\n\n"
                    "1. 入选标准\n"
                    "1.1 年龄在18-80岁之间（更新）\n"
                    "1.2 经组织学或细胞学确诊为非小细胞肺癌\n"
                    "1.3 ECOG体能评分0-2分（更新）\n"
                    "1.4 预期生存期≥12周\n\n"
                    "2. 排除标准\n"
                    "2.1 既往接受过免疫治疗\n"
                    "2.2 有活动性自身免疫性疾病\n"
                    "2.3 有间质性肺病病史\n"
                    "2.4 有严重心血管疾病史（新增）"
                )
        with col2:
            if st.button("🚀 开始对比", type="primary", use_container_width=True, key="compare_text_btn"):
                if text_old and text_new:
                    with st.spinner("正在对比文档..."):
                        orchestrator = get_orchestrator()
                        task_input = TaskInput(
                            input_type=doc_type_2,
                            content=text_new,
                            metadata={
                                "text_old": text_old,
                                "text_new": text_new,
                                "doc_type": doc_type_2,
                            },
                        )
                        result = orchestrator.process(task_input)
                        st.session_state.compare_result = result
                else:
                    st.warning("请粘贴两个版本的文档文本")

    # 显示对比结果
    if st.session_state.compare_result:
        result = st.session_state.compare_result
        if result.success:
            output = result.output
            stats = output.get("stats", {})

            st.markdown("---")
            st.markdown("## ✅ 版本差异报告")

            # 统计卡片
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📗 新增", stats.get("additions", 0))
            with col2:
                st.metric("📕 删除", stats.get("deletions", 0))
            with col3:
                st.metric("📙 修改", stats.get("modifications", 0))
            with col4:
                st.metric("📊 总变更", stats.get("total_changes", 0))

            st.markdown(f"**摘要**: {output.get('summary', '')}")

            # 变更详情
            with st.expander("📋 查看详细变更", expanded=True):
                changes = output.get("changes", [])
                for i, c in enumerate(changes):
                    if c["type"] == "add":
                        st.markdown(
                            f'<div style="background:#e6ffe6;padding:8px;margin:4px 0;border-radius:4px;'
                            f'border-left:4px solid #28a745;">'
                            f'✅ <strong>[新增] 第{c.get("line_new", "?")}行:</strong> {c["content"]}</div>',
                            unsafe_allow_html=True,
                        )
                    elif c["type"] == "delete":
                        st.markdown(
                            f'<div style="background:#ffe6e6;padding:8px;margin:4px 0;border-radius:4px;'
                            f'border-left:4px solid #dc3545;text-decoration:line-through;">'
                            f'❌ <strong>[删除] 第{c.get("line_old", "?")}行:</strong> {c["content"]}</div>',
                            unsafe_allow_html=True,
                        )
                    elif c["type"] == "modify":
                        st.markdown(
                            f'<div style="background:#fff3cd;padding:8px;margin:4px 0;border-radius:4px;'
                            f'border-left:4px solid #ffc107;">'
                            f'🔄 <strong>[修改] 第{c.get("line_old", "?")}→第{c.get("line_new", "?")}行:</strong><br>'
                            f'旧: {c.get("content_old", "")}<br>新: {c.get("content_new", "")}</div>',
                            unsafe_allow_html=True,
                        )

            # HTML 报告下载
            html_report = output.get("html_report", "")
            if html_report:
                st.download_button(
                    label="📥 下载HTML差异报告",
                    data=html_report,
                    file_name="版本差异报告.html",
                    mime="text/html",
                )

            md_report = output.get("markdown_report", "")
            if md_report:
                with st.expander("📝 查看Markdown报告"):
                    st.code(md_report, language="markdown")

        else:
            st.error(f"处理失败: {result.error_message}")


def render_task_page():
    """任务管理页面"""
    st.markdown("# ✅ 任务提醒与进度追踪")

    st.info(
        "解析**工作邮件**、**零散任务文本清单**，自动提取任务内容、负责人、"
        "时间节点等信息，统一整理为结构化待办列表，实现任务跟进与提醒。"
    )

    tab1, tab2, tab3 = st.tabs(["📥 任务解析", "📋 任务看板", "⏰ 提醒与通知"])

    with tab1:
        st.markdown("### 输入任务文本")

        task_text = st.text_area(
            "任务文本（邮件内容、待办清单等）",
            placeholder="请粘贴工作邮件或待办任务清单...\n\n"
                       "示例格式：\n"
                       "- [ ] 完成中期分析报告，负责人：王博士，截止日期：2026年6月20日\n"
                       "- [ ] 通知各研究中心数据截止日期，负责人：赵经理，截止日期：2026年6月11日\n"
                       "- [x] 完成数据清理工作，负责人：刘总监",
            height=200,
        )

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("📋 加载示例", key="load_task_example", use_container_width=True):
                st.session_state.task_example_text = (
                    "发件人: zhang@example.com\n"
                    "主题: 本周待办事项及下周计划\n\n"
                    "各位同事好，\n\n"
                    "以下是本周需要完成的重点工作：\n\n"
                    "1. 完成中期分析报告终稿 - 负责人：王博士 - 截止：6月20日 - 高优先级\n"
                    "2. 通知各研究中心数据截止日期 - 负责人：赵经理 - 截止：6月11日\n"
                    "3. 组建NDA申报工作组 - 负责人：张主任 - 截止：6月15日\n"
                    "4. 亚组分析计划制定 - 负责人：李教授 - 截止：6月25日\n"
                    "5. ICF版本更新审核 - 截止：6月18日，紧急\n"
                    "6. 准备下周DSMB会议材料 - 进行中\n"
                    "7. [x] 完成CRF设计定稿\n"
                    "8. [x] 提交伦理审查申请\n\n"
                    "请大家按时完成，谢谢！\n\n"
                    "张主任"
                )
        with col2:
            if st.button("🚀 解析任务", type="primary", use_container_width=True):
                if task_text or "task_example_text" in st.session_state:
                    if not task_text and "task_example_text" in st.session_state:
                        task_text = st.session_state.task_example_text
                    with st.spinner("正在解析任务..."):
                        orchestrator = get_orchestrator()
                        task_input = TaskInput(
                            input_type="email",
                            content=task_text,
                            metadata={"mode": "parse"},
                        )
                        result = orchestrator.process(task_input)
                        st.session_state.task_result = result

                        if result.success:
                            st.session_state.extracted_tasks = (
                                result.output.get("parsed_tasks", {}).get("tasks", [])
                            )
                else:
                    st.warning("请先输入任务文本或点击「加载示例」")

    with tab2:
        st.markdown("### 任务看板")

        # 获取存储的任务
        from app.modules.task_manager import TaskTracker
        tracker = TaskTracker()
        all_tasks = tracker.get_all_tasks()
        stats = tracker.get_stats()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📋 总任务", stats.get("total", 0))
        with col2:
            st.metric("⏳ 待处理", stats.get("todo", 0))
        with col3:
            st.metric("🔄 进行中", stats.get("in_progress", 0))
        with col4:
            st.metric("✅ 已完成", stats.get("completed", 0))

        if all_tasks:
            # 按状态分列看板
            statuses = ["待处理", "进行中", "已完成"]
            cols = st.columns(3)

            for idx, status in enumerate(statuses):
                with cols[idx]:
                    st.markdown(f"**{['⏳', '🔄', '✅'][idx]} {status}**")
                    st.divider()
                    tasks_in_status = [t for t in all_tasks if t.status == status]
                    for task in tasks_in_status[:10]:
                        priority_icon = {"高": "🔴", "中": "🟡", "低": "🟢"}
                        with st.container(border=True):
                            st.markdown(f"{priority_icon.get(task.priority, '')} {task.content[:50]}...")
                            if task.responsible_person:
                                st.caption(f"👤 {task.responsible_person}")
                            if task.deadline:
                                st.caption(f"📅 {task.deadline}")
        else:
            st.info("暂无任务数据，请先在「任务解析」页签中解析任务。")

        # 展示刚解析的任务
        if st.session_state.extracted_tasks:
            with st.expander("📋 最新解析的任务", expanded=True):
                st.dataframe(
                    [
                        {
                            "内容": t.get("content", "")[:60],
                            "负责人": t.get("responsible_person", ""),
                            "截止日期": t.get("deadline", ""),
                            "优先级": t.get("priority", ""),
                            "状态": t.get("status", ""),
                        }
                        for t in st.session_state.extracted_tasks
                    ],
                    use_container_width=True,
                )

    with tab3:
        st.markdown("### ⏰ 任务提醒与通知")

        if st.button("🔄 生成提醒日报", type="primary"):
            with st.spinner("正在生成提醒..."):
                orchestrator = get_orchestrator()
                task_input = TaskInput(
                    input_type="task_list",
                    content="",
                    metadata={"mode": "reminder"},
                )
                result = orchestrator.process(task_input)
                if result.success:
                    reminder_text = result.output.get("reminder_text", "")
                    st.markdown("#### 📋 任务提醒日报")
                    st.code(reminder_text)

        # 过期任务
        with st.expander("⚠️ 已过期任务"):
            overdue = tracker.get_overdue_tasks()
            if overdue:
                for t in overdue:
                    st.warning(f"🔴 [{t.id}] {t.content} - 负责人: {t.responsible_person}")
            else:
                st.success("🎉 暂无过期任务！")

        # 即将到期任务
        with st.expander("📅 近3日到期"):
            upcoming = tracker.get_upcoming_tasks(3)
            if upcoming:
                for t in upcoming:
                    st.info(f"📌 [{t.id}] {t.content} - 截止: {t.deadline}")
            else:
                st.write("近3日无即将到期任务。")

    # 显示处理结果
    if st.session_state.task_result:
        result = st.session_state.task_result
        if not result.success:
            st.error(f"处理失败: {result.error_message}")


def render_plugin_page():
    """插件管理页面"""
    st.markdown("# 🔌 可扩展插件架构")

    st.info(
        "项目采用**插件化设计**，预留扩展接口，支持后续快速新增自动化任务。"
        "所有任务执行规则统一通过独立配置文件进行管理。"
    )

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("### 📦 已注册的核心智能体")
        agents = get_orchestrator().get_registered_agents()
        for task_type, name in agents.items():
            icons = {
                "meeting_minutes": "📝",
                "doc_compare": "📄",
                "task_management": "✅",
            }
            with st.container(border=True):
                st.markdown(f"**{icons.get(task_type, '🤖')} {name}**")
                st.caption(f"任务类型: `{task_type}`")

        st.markdown("### 🔌 插件架构说明")
        st.markdown("""
        **插件实现步骤**:

        1. 在 `custom_plugins/` 目录下创建 Python 文件
        2. 继承 `BasePlugin` 基类
        3. 实现 `execute()` 方法
        4. 在 `config/plugins.json` 中启用

        **插件示例**:
        ```python
        from app.plugins.base_plugin import BasePlugin

        class ComplianceReportPlugin(BasePlugin):
            plugin_name = "合规报告生成器"
            plugin_description = "自动生成合规报告"
            plugin_version = "1.0.0"

            def execute(self, input_data, **kwargs):
                # 处理逻辑
                return {"success": True, "data": "..."}
        ```
        """)

    with col2:
        st.markdown("### ⚙️ 插件配置")

        with st.container(border=True):
            st.markdown("**配置文件**")
            st.markdown("`config/plugins.json`")
            st.markdown("`config/tasks.json`")

        with st.container(border=True):
            st.markdown("**当前状态**")
            st.markdown(f"- 核心智能体: {len(agents)} 个已注册")
            st.markdown(f"- 插件目录: `custom_plugins/`")
            st.markdown(f"- 运行模式: {'🟡 模拟模式' if is_mock_mode() else '🟢 LLM模式'}")

        with st.container(border=True):
            st.markdown("**预置插件模板**")
            st.markdown("1. 📊 数据校验脚本")
            st.markdown("2. 📋 合规报告模板生成")
            st.markdown("3. 📁 批量文件处理")
            st.markdown("4. 🧪 自定义自动化任务")

        with st.container(border=True):
            st.markdown("**扩展建议**")
            st.markdown("""
            - 对接数据库实现数据持久化
            - 集成邮件发送功能
            - 添加日历同步接口
            - 接入真实LLM API提升处理质量
            """)


# ============================================================
#  主渲染逻辑
# ============================================================

def main():
    """主渲染入口"""
    render_sidebar()

    # 页面路由
    pages = {
        "首页": render_home,
        "会议纪要": render_meeting_page,
        "文档对比": render_compare_page,
        "任务管理": render_task_page,
        "插件管理": render_plugin_page,
    }

    current_page = st.session_state.current_page
    page_renderer = pages.get(current_page, render_home)

    with st.container():
        page_renderer()


if __name__ == "__main__":
    main()
