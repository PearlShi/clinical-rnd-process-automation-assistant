"""
============================================================
  doc_compare/ - 临床文档版本对比模块
  临床研发流程自动化助手
============================================================
  功能说明：
  针对临床试验方案（Protocol）和知情同意书（ICF）
  两类常用临床文档，支持上传两个不同版本文件，
  自动比对全文内容，标记新增、修改、删减内容，
  并生成标准化版本差异报告。
============================================================
"""

import difflib
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.agent.base_agent import BaseAgent, TaskInput, TaskResult, MockLLMEngine
from app.config import DOC_COMPARE_CONFIG

logger = logging.getLogger(__name__)


# ============================================================
#  文档文本提取器
# ============================================================

class DocTextExtractor:
    """从各种文档格式中提取文本内容"""

    @staticmethod
    def extract(file_path: Path) -> tuple[bool, str, str]:
        """
        从文件中提取文本
        Args:
            file_path: 文件路径
        Returns:
            (是否成功, 文本内容, 错误信息)
        """
        ext = file_path.suffix.lower()

        if ext == '.txt':
            return DocTextExtractor._extract_txt(file_path)
        elif ext == '.md':
            return DocTextExtractor._extract_md(file_path)
        elif ext == '.docx':
            return DocTextExtractor._extract_docx(file_path)
        elif ext == '.pdf':
            return DocTextExtractor._extract_pdf(file_path)
        else:
            # 默认尝试纯文本
            return DocTextExtractor._extract_txt(file_path)

    @staticmethod
    def _extract_txt(file_path: Path) -> tuple[bool, str, str]:
        try:
            from app.utils.file_utils import read_text_file
            text = read_text_file(file_path)
            return True, text, ""
        except Exception as e:
            return False, "", f"读取文本文件失败: {str(e)}"

    @staticmethod
    def _extract_md(file_path: Path) -> tuple[bool, str, str]:
        try:
            from app.utils.file_utils import read_text_file
            text = read_text_file(file_path)
            return True, text, ""
        except Exception as e:
            return False, "", f"读取Markdown文件失败: {str(e)}"

    @staticmethod
    def _extract_docx(file_path: Path) -> tuple[bool, str, str]:
        try:
            from docx import Document
            doc = Document(str(file_path))
            text = '\n'.join(p.text for p in doc.paragraphs)
            return True, text, ""
        except ImportError:
            return False, "", "未安装python-docx库，无法处理Word文档"
        except Exception as e:
            return False, "", f"读取Word文档失败: {str(e)}"

    @staticmethod
    def _extract_pdf(file_path: Path) -> tuple[bool, str, str]:
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(file_path))
            text = '\n'.join(page.extract_text() for page in reader.pages)
            return True, text, ""
        except ImportError:
            return False, "", "未安装PyPDF2库，无法处理PDF文档"
        except Exception as e:
            return False, "", f"读取PDF文档失败: {str(e)}"


# ============================================================
#  文档对比引擎
# ============================================================

class DocComparator:
    """
    文档对比引擎 - 核心差异比较逻辑。
    基于 difflib 实现细粒度的文本差异检测。
    """

    def __init__(self):
        self.engine = MockLLMEngine()

    def compare(self, text_old: str, text_new: str, doc_type: str = "protocol") -> dict:
        """
        对比两个版本文档，检测所有差异
        Args:
            text_old: 旧版本文本
            text_new: 新版本文本
            doc_type: 文档类型 (protocol | icf)
        Returns:
            结构化差异报告
        """
        # 文本分块（按句子分块以提高对比精度）
        old_chunks = self._chunk_text(text_old)
        new_chunks = self._chunk_text(text_new)

        # 使用 difflib 进行差异比较
        differ = difflib.SequenceMatcher(None, old_chunks, new_chunks)
        changes = []

        for op, i1, i2, j1, j2 in differ.get_opcodes():
            if op == 'equal':
                continue

            if op == 'replace':
                for k in range(max(i2 - i1, j2 - j1)):
                    old_line = old_chunks[i1 + k] if k < i2 - i1 else ""
                    new_line = new_chunks[j1 + k] if k < j2 - j1 else ""
                    if old_line != new_line:
                        changes.append({
                            "type": "modify",
                            "content_old": old_line,
                            "content_new": new_line,
                            "line_old": i1 + k + 1,
                            "line_new": j1 + k + 1,
                        })
            elif op == 'delete':
                for k in range(i1, i2):
                    changes.append({
                        "type": "delete",
                        "content": old_chunks[k],
                        "line_old": k + 1,
                        "line_new": None,
                    })
            elif op == 'insert':
                for k in range(j1, j2):
                    changes.append({
                        "type": "add",
                        "content": new_chunks[k],
                        "line_old": None,
                        "line_new": k + 1,
                    })

        # 使用模拟引擎生成补充的语义差异分析
        semantic_result = self.engine.generate_doc_comparison(text_old, text_new, doc_type)

        # 统计信息
        stats = {
            "additions": sum(1 for c in changes if c["type"] == "add"),
            "deletions": sum(1 for c in changes if c["type"] == "delete"),
            "modifications": sum(1 for c in changes if c["type"] == "modify"),
            "total_changes": len(changes),
            "total_lines_old": len(old_chunks),
            "total_lines_new": len(new_chunks),
        }

        change_rate = (stats["total_changes"] / max(len(old_chunks), 1)) * 100

        doc_type_name = {
            "protocol": "临床试验方案（Protocol）",
            "icf": "知情同意书（ICF）",
        }.get(doc_type, "临床文档")

        return {
            "doc_type": doc_type,
            "doc_type_name": doc_type_name,
            "stats": stats,
            "change_rate": round(change_rate, 1),
            "changes": changes,
            "summary": (
                f"文档类型: {doc_type_name}\n"
                f"旧版本共 {stats['total_lines_old']} 行，新版本共 {stats['total_lines_new']} 行\n"
                f"共检测到 {stats['total_changes']} 处变更 "
                f"（新增 {stats['additions']} 处，删除 {stats['deletions']} 处，"
                f"修改 {stats['modifications']} 处）\n"
                f"变更率: {change_rate:.1f}%"
            ),
        }

    def _chunk_text(self, text: str) -> list:
        """将文本分割为合适的对比单元"""
        # 先按行分割
        lines = text.split('\n')

        chunks = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # 长句子按标点分割
            if len(line) > 200:
                sentences = re.split(r'(?<=[。！？；\n])', line)
                for s in sentences:
                    s = s.strip()
                    if s:
                        chunks.append(s)
            else:
                chunks.append(line)

        return chunks

    def generate_diff_report_html(self, result: dict) -> str:
        """
        生成HTML格式的差异报告
        使用颜色标记：绿色=新增，红色=删除，黄色=修改
        """
        colors = DOC_COMPARE_CONFIG
        html_parts = []

        html_parts.append("""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>文档版本差异报告</title>
<style>
body { font-family: 'Microsoft YaHei', sans-serif; margin: 20px; background: #f5f5f5; }
.container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
h1 { color: #333; border-bottom: 2px solid #4A90D9; padding-bottom: 10px; }
.summary { background: #f0f7ff; padding: 15px; border-radius: 6px; margin: 20px 0; white-space: pre-wrap; }
.stats { display: flex; gap: 20px; margin: 15px 0; }
.stat-box { flex: 1; text-align: center; padding: 15px; border-radius: 6px; color: white; }
.stat-add { background: #28a745; }
.stat-del { background: #dc3545; }
.stat-mod { background: #ffc107; color: #333; }
.stat-total { background: #6c757d; }
.change-item { padding: 8px 12px; margin: 4px 0; border-radius: 4px; font-family: monospace; white-space: pre-wrap; }
.change-add { background: #e6ffe6; border-left: 4px solid #28a745; }
.change-del { background: #ffe6e6; border-left: 4px solid #dc3545; text-decoration: line-through; }
.change-mod { background: #fff3cd; border-left: 4px solid #ffc107; }
.line-num { color: #999; margin-right: 10px; font-size: 0.9em; }
</style>
</head>
<body>
<div class="container">
""")

        html_parts.append(f"<h1>📄 文档版本差异报告</h1>")
        html_parts.append(f"<p><strong>文档类型:</strong> {result['doc_type_name']}</p>")
        html_parts.append(f"<p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>")

        # 统计信息
        stats = result['stats']
        html_parts.append('<div class="stats">')
        html_parts.append(f'<div class="stat-box stat-add">新增<br><strong>{stats["additions"]}</strong> 处</div>')
        html_parts.append(f'<div class="stat-box stat-del">删除<br><strong>{stats["deletions"]}</strong> 处</div>')
        html_parts.append(f'<div class="stat-box stat-mod">修改<br><strong>{stats["modifications"]}</strong> 处</div>')
        html_parts.append(f'<div class="stat-box stat-total">总计<br><strong>{stats["total_changes"]}</strong> 处</div>')
        html_parts.append('</div>')

        # 摘要
        html_parts.append(f'<div class="summary">{result["summary"]}</div>')

        # 变更列表
        html_parts.append('<h2>变更详情</h2>')
        for c in result['changes']:
            if c['type'] == 'add':
                html_parts.append(
                    f'<div class="change-item change-add">'
                    f'<span class="line-num">+{c["line_new"]}</span>'
                    f'{c["content"]}</div>'
                )
            elif c['type'] == 'delete':
                html_parts.append(
                    f'<div class="change-item change-del">'
                    f'<span class="line-num">-{c["line_old"]}</span>'
                    f'{c["content"]}</div>'
                )
            elif c['type'] == 'modify':
                html_parts.append(
                    f'<div class="change-item change-mod">'
                    f'<span class="line-num">~{c["line_old"]}→{c["line_new"]}</span>'
                    f'旧: {c["content_old"]}<br>'
                    f'新: {c["content_new"]}</div>'
                )

        html_parts.append('</div></body></html>')

        return '\n'.join(html_parts)

    def generate_diff_report_markdown(self, result: dict) -> str:
        """生成Markdown格式的差异报告"""
        md = []
        md.append("# 📄 临床文档版本差异报告\n")
        md.append(f"**文档类型**: {result['doc_type_name']}")
        md.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 统计摘要
        stats = result['stats']
        md.append("## 变更统计")
        md.append(f"- **新增**: {stats['additions']} 处")
        md.append(f"- **删除**: {stats['deletions']} 处")
        md.append(f"- **修改**: {stats['modifications']} 处")
        md.append(f"- **总变更**: {stats['total_changes']} 处")
        md.append(f"- **变更率**: {result['change_rate']}%\n")

        # 摘要
        md.append("## 变更摘要")
        md.append(result['summary'] + "\n")

        # 详细变更
        md.append("## 详细变更")
        for c in result['changes']:
            if c['type'] == 'add':
                md.append(f"> ✅ **[新增] 第{c['line_new']}行**: {c['content']}")
            elif c['type'] == 'delete':
                md.append(f"> ❌ **[删除] 第{c['line_old']}行**: ~~{c['content']}~~")
            elif c['type'] == 'modify':
                md.append(
                    f"> 🔄 **[修改] 第{c['line_old']}行→第{c['line_new']}行**:\n"
                    f"> - 旧: {c['content_old']}\n"
                    f"> - 新: {c['content_new']}"
                )

        return '\n'.join(md)


# ============================================================
#  文档对比智能体
# ============================================================

class DocCompareAgent(BaseAgent):
    """
    文档对比智能体 - 处理临床文档版本对比任务。
    支持 Protocol 和 ICF 两种文档类型。
    """

    def __init__(self):
        super().__init__(
            agent_name="临床文档对比智能体",
            agent_description="自动比对临床试验方案和知情同意书的不同版本差异"
        )
        self.extractor = DocTextExtractor()
        self.comparator = DocComparator()

    def process(self, task_input: TaskInput) -> TaskResult:
        """
        处理文档对比任务
        需要上传两个文件或提供两段文本
        """
        try:
            start_time = datetime.now()

            # 获取两份文档内容
            metadata = task_input.metadata or {}

            # 判断对比模式
            if task_input.file_path:
                # 模式1: 文件对比 - metadata中包含旧版本文件路径
                old_file = metadata.get("old_file_path")
                new_file = metadata.get("new_file_path")

                if not old_file and task_input.file_path:
                    new_file = task_input.file_path
                    old_file = metadata.get("old_file_path") or metadata.get("compare_with")

                if not old_file or not new_file:
                    return TaskResult(
                        success=False,
                        task_type="doc_compare",
                        error_message="文档对比需要提供两个版本的文件或文本内容。 "
                                      "请上传旧版本和新版本两个文件。",
                    )

                # 提取文件文本
                success1, text_old, err1 = self.extractor.extract(Path(old_file))
                success2, text_new, err2 = self.extractor.extract(Path(new_file))

                if not success1:
                    return TaskResult(
                        success=False, task_type="doc_compare",
                        error_message=f"无法读取旧版本文件: {err1}"
                    )
                if not success2:
                    return TaskResult(
                        success=False, task_type="doc_compare",
                        error_message=f"无法读取新版本文件: {err2}"
                    )
            else:
                # 模式2: 文本对比
                # 使用元数据中的两个文本
                text_old = metadata.get("text_old", "")
                text_new = metadata.get("text_new", task_input.content)
                if not text_old:
                    return TaskResult(
                        success=False,
                        task_type="doc_compare",
                        error_message="文本对比模式需要提供旧版本和新版本两段文本。"
                    )

            doc_type = metadata.get("doc_type", task_input.input_type)
            if doc_type not in ("protocol", "icf"):
                doc_type = "protocol"

            # 执行文档对比
            result = self.comparator.compare(text_old, text_new, doc_type)
            html_report = self.comparator.generate_diff_report_html(result)
            md_report = self.comparator.generate_diff_report_markdown(result)

            elapsed = (datetime.now() - start_time).total_seconds()

            return TaskResult(
                success=True,
                task_type="doc_compare",
                output={
                    "structured": result,
                    "html_report": html_report,
                    "markdown_report": md_report,
                    "stats": result["stats"],
                    "summary": result["summary"],
                    "changes": result["changes"],
                },
                processing_time=elapsed,
            )

        except Exception as e:
            logger.error(f"文档对比处理失败: {str(e)}", exc_info=True)
            return TaskResult(
                success=False,
                task_type="doc_compare",
                error_message=f"文档对比失败: {str(e)}",
            )
