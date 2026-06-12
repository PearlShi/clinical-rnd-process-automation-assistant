# 🏥 临床研发流程自动化助手

> **Clinical R&D Process Automation Assistant**  
> 基于 AI 智能体技术的临床研发工作流自动化工具

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-green)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📋 项目简介

本工具面向企业内部办公场景设计，核心定位为**内部自动化应用程序**，用于优化临床研发部门日常工作流程。项目结合 AI 智能体技术落地业务场景，覆盖从需求设计、架构开发到部署上线的端到端解决方案。

### 核心功能

| 功能模块 | 说明 |
|---------|------|
| 📝 **会议纪要自动生成** | 上传会议录音或转录文本，结构化输出标准会议纪要 |
| 📄 **临床文档版本对比** | 针对 Protocol/ICF 文档，自动比对版本差异并生成报告 |
| ✅ **任务提醒与进度追踪** | 解析邮件和任务清单，统一管理待办事项并自动提醒 |
| 🔌 **可扩展插件架构** | 插件化设计，支持快速扩展新功能，配置文件统一管理 |

---

## 🚀 快速开始

### 方式一：Docker 部署（推荐）

```bash
# 启动服务
docker-compose -f docker/docker-compose.yml up -d web-ui

# 访问
# http://localhost:8501
```

### 方式二：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 Web UI
streamlit run ui/app.py

# 3. 访问
# http://localhost:8501
```

---

## 🧩 系统架构

```
┌─────────────────────────────────────────────┐
│          用户界面 (Streamlit Web UI)          │
├─────────────────────────────────────────────┤
│              API 服务层 (FastAPI)              │
├─────────────────────────────────────────────┤
│         多任务AI智能体调度器                   │
│  ┌──────────┬──────────────┬───────────────┐ │
│  │会议纪要   │ 文档对比     │ 任务管理       │ │
│  │智能体     │ 智能体       │ 智能体         │ │
│  └──────────┴──────────────┴───────────────┘ │
│  ┌─────────────────────────────────────────┐ │
│  │          插件系统 (Plugin System)        │ │
│  └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│            Docker 容器化部署                  │
└─────────────────────────────────────────────┘
```

---

## 📂 项目结构

```
clinical-rd-assistant/
├── app/                          # 核心应用代码
│   ├── agent/                    # AI 智能体框架
│   │   ├── base_agent.py         # 基础智能体与调度器
│   │   └── router.py             # 任务路由
│   ├── modules/                  # 功能模块
│   │   ├── meeting_minutes/      # 会议纪要
│   │   ├── doc_compare/          # 文档对比
│   │   └── task_manager/         # 任务管理
│   ├── plugins/                  # 插件架构
│   │   ├── __init__.py           # 插件管理器
│   │   └── base_plugin.py        # 插件基类
│   ├── utils/                    # 工具函数
│   ├── config.py                 # 全局配置
│   └── main.py                   # 应用入口
├── ui/                           # 用户界面
│   └── app.py                    # Streamlit 主程序
├── config/                       # 配置文件
│   ├── plugins.json              # 插件配置
│   └── tasks.json                # 任务规则配置
├── custom_plugins/               # 自定义插件目录
├── docker/                       # Docker 部署配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/                         # 文档
│   └── user_manual.md            # 用户手册
├── data/                         # 数据目录
├── tests/                        # 测试
├── requirements.txt              # Python 依赖
└── README.md                     # 本文件
```

---

## 🛠 技术栈

| 层次 | 技术 | 用途 |
|------|------|------|
| 前端 | **Streamlit** | Web 用户界面 |
| 后端 | **FastAPI** | RESTful API 服务 |
| AI 框架 | **LangChain** | 多任务智能体基础框架 |
| 文档处理 | **python-docx / PyPDF2** | 文档读写和格式转换 |
| 语音处理 | **SpeechRecognition / pydub** | 会议录音转文字 |
| 容器化 | **Docker / docker-compose** | 一键部署和环境管理 |
| 配置管理 | **JSON 配置文件** | 任务规则和插件管理 |

---

## ⚙️ 配置说明

### 环境变量

```bash
# AI 引擎配置（默认使用 Mock 模式，无需 API 密钥）
LLM_PROVIDER=mock        # mock | openai | anthropic
LLM_API_KEY=             # 真实 API 密钥
LLM_MODEL=gpt-4o-mini    # 模型名称
APP_DEBUG=false          # 调试模式
```

### AI 模式说明

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| 🟡 **Mock**（默认） | 无需 API 密钥，基于模板和规则处理 | 功能演示、开发测试 |
| 🟢 **OpenAI** | 接入 GPT 模型，质量更高 | 生产环境使用 |
| 🟢 **Anthropic** | 接入 Claude 模型 | 生产环境使用 |

---

## 🔌 插件开发

详见 [用户手册 - 插件扩展方法](docs/user_manual.md#4-插件扩展方法)

```python
from app.plugins.base_plugin import BasePlugin

class MyPlugin(BasePlugin):
    plugin_name = "我的插件"
    plugin_description = "插件功能说明"
    plugin_version = "1.0.0"

    def execute(self, input_data, **kwargs):
        # 实现处理逻辑
        return {"success": True, "data": result}
```

---

## 📊 应用截图

### 首页概览
> 系统首页展示核心功能卡片、智能体状态和快速上手指引

### 会议纪要页面
> 支持文本输入和音频上传两种模式，一键生成结构化会议纪要

### 文档对比页面
> 可视化展示版本差异，支持下载 HTML 报告

### 任务管理页面
> 任务解析、看板管理、提醒通知一站式管理

---

## 🧪 测试

```bash
# 运行测试
python -m pytest tests/

# 带覆盖率报告
python -m pytest tests/ --cov=app
```

---

## 📚 文档

- [完整用户手册](docs/user_manual.md) - 部署、使用、扩展、配置全说明
- [软件计划书](软件计划书：Clinical%20R&D%20Process%20Automation%20Assistant.txt) - 项目原始需求文档

---

## 👨‍💻 开发团队

AI 临床研发自动化开源演示项目

---

## 📄 许可证

本项目为 AI 临床研发自动化开源演示项目，仅供个人学习、技术演示使用。
