# 临床研发流程自动化助手 - 用户手册

> **版本**: 1.0.0  
> **更新日期**: 2026年6月  
> **文档状态**: ✅ 已完成

---

## 📑 目录

1. [产品概述](#1-产品概述)
2. [快速部署](#2-快速部署)
3. [功能使用说明](#3-功能使用说明)
   - [3.1 会议纪要自动生成](#31-会议纪要自动生成)
   - [3.2 临床文档版本对比](#32-临床文档版本对比)
   - [3.3 任务提醒与进度追踪](#33-任务提醒与进度追踪)
4. [插件扩展方法](#4-插件扩展方法)
5. [配置文件使用规范](#5-配置文件使用规范)
6. [API 接口文档](#6-api-接口文档)
7. [常见问题](#7-常见问题)

---

## 1. 产品概述

### 1.1 产品定位

**临床研发流程自动化助手**（Clinical R&D Process Automation Assistant）是一款基于 AI 智能体技术的内部自动化应用程序，面向临床研发部门日常工作场景，旨在减少重复性人工操作，提升全流程工作效率。

### 1.2 核心功能

| 功能模块 | 说明 |
|---------|------|
| 📝 会议纪要自动生成 | 上传会议录音或文字转录，自动生成结构化会议纪要 |
| 📄 临床文档版本对比 | 比对 Protocol/ICF 文档版本差异，生成详细报告 |
| ✅ 任务提醒与进度追踪 | 解析邮件和任务清单，统一管理待办事项 |
| 🔌 可扩展插件架构 | 插件化设计，支持快速扩展新功能 |

### 1.3 技术架构

```
用户界面 (Streamlit Web UI)
        ↓
    API 服务层 (FastAPI)
        ↓
  ┌─────────────────────┐
  │  AI 智能体调度器     │
  │  ┌──────┬──────┬──┐ │
  │  │会议   │文档   │任│ │
  │  │纪要   │对比   │务│ │
  │  │智能体 │智能体 │智│ │
  │  │       │       │能│ │
  │  └──────┴──────┴──┘ │
  │  插件系统            │
  └─────────────────────┘
        ↓
  容器化部署 (Docker)
```

---

## 2. 快速部署

### 2.1 方式一：Docker 部署（推荐）

**前置条件**: 安装 Docker 和 Docker Compose

```bash
# 1. 克隆项目
git clone <repository-url>
cd clinical-rd-assistant

# 2. 启动服务（Streamlit Web UI）
docker-compose up -d web-ui

# 3. 访问应用
# 浏览器打开: http://localhost:8501

# 4. 停止服务
docker-compose down
```

### 2.2 方式二：本地 Python 运行

**前置条件**: Python 3.9+

```bash
# 1. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate      # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动 Web UI
streamlit run ui/app.py

# 4. （可选）启动 API 服务
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. 访问应用
# Web UI: http://localhost:8501
# API:    http://localhost:8000
```

### 2.3 系统要求

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU  | 2 核    | 4 核    |
| 内存 | 4 GB    | 8 GB    |
| 磁盘 | 2 GB    | 10 GB   |
| OS   | Linux/Windows/MacOS | Linux |

---

## 3. 功能使用说明

### 3.1 会议纪要自动生成

#### 功能概述

支持两种输入方式：
- **文本输入**: 粘贴会议转录文本
- **音频输入**: 上传会议录音文件（mp3/wav/m4a/ogg）

系统自动提取：
- 会议核心议题
- 关键决策
- 待执行行动项（含责任人和时间要求）
- 结构化标准会议纪要（Markdown格式）

#### 操作步骤

1. 左侧导航栏点击 **「会议纪要」**
2. 选择输入方式：
   - **文本输入**: 粘贴会议转录文本，点击「生成会议纪要」
   - **音频上传**: 上传录音文件，点击「识别并生成」
3. 查看生成的会议纪要结果（支持展开查看详情）
4. 可复制或下载 Markdown 格式结果

#### 文本示例

```
会议主题：三期临床试验中期分析讨论会
时间：2026年6月10日 10:00-11:30
参会人员：张主任、李教授、王博士、赵经理

议题一：中期分析结果汇报
王博士汇报了本次中期分析的主要结果...

行动项：
- [ ] 完成中期分析报告终稿，负责人：王博士，截止日期：6月20日
- [ ] 组建NDA申报工作组，负责人：张主任，截止日期：6月15日
```

---

### 3.2 临床文档版本对比

#### 功能概述

支持对比 **临床试验方案（Protocol）** 和 **知情同意书（ICF）** 两种文档。

支持文件格式：
- Word 文档 (.docx)
- PDF 文档 (.pdf)
- 纯文本 (.txt, .md)

检测的变更类型：
- ✅ **新增**：新版本中添加的内容（绿色标记）
- ❌ **删除**：旧版本中存在但新版本移除的内容（红色标记）
- 🔄 **修改**：内容发生变化的部分（黄色标记）

#### 操作步骤

1. 左侧导航栏点击 **「文档对比」**
2. 选择对比方式：
   - **文件上传**: 分别上传旧版本和新版本文档文件
   - **文本粘贴**: 分别粘贴两版本文本内容
3. 选择文档类型（Protocol / ICF）
4. 点击「开始对比」
5. 查看版本差异报告：
   - 变更统计概览（新增/删除/修改/总计）
   - 详细变更列表（逐条查看差异）
   - 支持下载 HTML 版本差异报告

---

### 3.3 任务提醒与进度追踪

#### 功能概述

从以下来源自动提取结构化任务：
- **工作邮件**: 解析邮件正文中的任务信息
- **任务清单**: 识别待办事项列表
- **自由文本**: 从任意文本中提取任务

自动提取信息：
- 任务内容描述
- 负责人
- 截止日期
- 优先级（高/中/低）
- 任务分类（文档/会议/审批/沟通等）

#### 操作步骤

**任务解析**:
1. 点击 **「任务管理」→「任务解析」**
2. 粘贴待解析文本（邮件或任务清单）
3. 点击「解析任务」
4. 查看自动提取的结构化任务列表

**任务看板**:
1. 在 **「任务看板」** 页签查看所有任务
2. 任务按状态分列（待处理/进行中/已完成）
3. 查看优先级和截止日期标识

**提醒通知**:
1. 在 **「提醒与通知」** 页签生成提醒日报
2. 查看已过期任务和近3日到期任务
3. 支持自定义提醒时间范围

---

## 4. 插件扩展方法

### 4.1 插件架构

系统采用插件化架构，支持通过标准接口扩展新功能。

### 4.2 创建新插件

**步骤 1**: 在 `custom_plugins/` 目录下创建 Python 文件

```python
# custom_plugins/compliance_report.py

from app.plugins.base_plugin import BasePlugin

class ComplianceReportPlugin(BasePlugin):
    # 插件元信息
    plugin_name = "合规报告生成器"
    plugin_version = "1.0.0"
    plugin_description = "自动生成合规报告"
    plugin_author = "Your Name"
    plugin_dependencies = ["python-docx"]

    def execute(self, input_data, **kwargs):
        """
        核心处理逻辑
        Args:
            input_data: 输入数据
        Returns:
            dict: 必须包含 'success' 字段
        """
        try:
            # 处理逻辑
            result = {"report": "合规报告内容..."}
            return {
                "success": True,
                "data": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
```

**步骤 2**: 注册插件

在 `config/plugins.json` 中的 `enabled_plugins` 列表中添加插件模块名：

```json
{
    "enabled_plugins": ["compliance_report"],
    "plugin_settings": {
        "合规报告生成器": {
            "output_format": "docx",
            "template_path": ""
        }
    }
}
```

### 4.3 预置插件模板

| 插件模板 | 说明 | 输入 | 输出 |
|---------|------|------|------|
| 📊 数据校验脚本 | 验证临床数据完整性和一致性 | CSV/XLSX/JSON | 校验报告 |
| 📋 合规报告模板生成 | 根据模板生成合规文件 | 数据 + 模板 | DOCX/PDF |
| 📁 批量文件处理 | 批量格式转换和标准化 | 文档文件 | 处理后文件 |

---

## 5. 配置文件使用规范

### 5.1 插件配置 (`config/plugins.json`)

```json
{
    "plugin_dirs": ["config/plugins", "custom_plugins"],
    "enabled_plugins": ["plugin_module_name"],
    "plugin_settings": {
        "插件名称": {
            "key": "value"
        }
    }
}
```

| 字段 | 说明 | 必填 |
|------|------|------|
| `plugin_dirs` | 插件扫描目录列表 | 是 |
| `enabled_plugins` | 启用的插件模块名列表 | 是 |
| `plugin_settings` | 各插件的个性化配置 | 否 |
| `plugin_examples` | 预置插件模板说明 | 否 |

### 5.2 任务规则配置 (`config/tasks.json`)

```json
{
    "task_rules": {
        "meeting_minutes": {
            "enabled": true,
            "input_types": ["text", "audio"],
            "output_formats": ["markdown", "docx"]
        }
    },
    "plugin_task_rules": {
        "data_validation": {
            "enabled": false,
            "strict_mode": false
        }
    }
}
```

| 字段 | 说明 | 可选值 |
|------|------|--------|
| `enabled` | 是否启用该任务 | true/false |
| `input_types` | 支持的输入类型 | text/audio/document |
| `output_formats` | 支持的输出格式 | markdown/docx/html |
| `auto_route` | 是否自动路由 | true/false |

### 5.3 环境变量配置

| 变量名 | 说明 | 默认值 | 可选值 |
|--------|------|--------|--------|
| `LLM_PROVIDER` | AI引擎提供商 | `mock` | mock/openai/anthropic |
| `LLM_API_KEY` | API密钥 | `` | 字符串 |
| `LLM_MODEL` | 模型名称 | `gpt-4o-mini` | 模型ID |
| `APP_DEBUG` | 调试模式 | `false` | true/false |

---

## 6. API 接口文档

启动 API 服务后（`uvicorn app.main:app`），访问 `http://localhost:8000/docs` 查看 Swagger 文档。

### 6.1 核心接口

#### 统一处理入口

```
POST /process
参数:
  - text: 输入文本 (可选)
  - file: 上传文件 (可选)
  - input_type: auto | meeting_transcript | protocol | icf | email | task_list
```

#### 会议纪要

```
POST /meeting-minutes        # 从文本生成
POST /meeting-minutes/audio  # 从录音生成
```

#### 文档对比

```
POST /doc-compare            # 文本对比
POST /doc-compare/files      # 文件对比
```

#### 任务管理

```
POST /tasks/parse            # 解析任务
GET  /tasks                  # 获取所有任务
GET  /tasks/overdue          # 获取过期任务
GET  /tasks/upcoming         # 获取即将到期任务
GET  /tasks/reminder         # 获取提醒日报
```

---

## 7. 常见问题

### Q1: 是否需要 API 密钥才能使用？

**不需要。** 系统默认使用 **模拟模式（Mock）**，无需任何 API 密钥即可演示所有核心功能。如需更高质量的处理结果，可在 `.env` 中配置 OpenAI/Anthropic API 密钥。

### Q2: 如何切换到真实的 LLM API？

设置环境变量：
```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=your-api-key-here
export LLM_MODEL=gpt-4o-mini
```

### Q3: 支持哪些文件格式？

| 功能 | 支持格式 |
|------|---------|
| 会议音频 | mp3, wav, m4a, ogg, flac |
| 文档对比 | docx, pdf, txt, md |
| 任务解析 | 纯文本 |

### Q4: 如何添加新功能？

利用插件架构扩展。参考第 4 节「插件扩展方法」创建自定义插件。

### Q5: 定位地址时没有 0.0.0.0

对于 Streamlit，使用：
```bash
streamlit run ui/app.py --server.port=8501 --server.address=0.0.0.0
```

### Q6: Docker 部署后如何查看日志？

```bash
docker-compose logs -f web-ui
docker-compose logs -f api-server
```

---

> **文档版本**: 1.0.0 | **最后更新**: 2026年6月  
> **项目**: 临床研发流程自动化助手 - AI 临床研发自动化开源演示项目
