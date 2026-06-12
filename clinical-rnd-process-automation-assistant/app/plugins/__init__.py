"""
============================================================
  plugins/ - 可扩展插件架构
  临床研发流程自动化助手
============================================================
  采用插件化设计，预留扩展接口，支持后续快速新增
  自动化任务。所有任务执行规则统一通过独立配置文件
  进行管理，降低后期维护与迭代成本。
============================================================
"""

from __future__ import annotations

import os
import sys
import json
import logging
import importlib
import inspect
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type
from abc import ABC, abstractmethod

from app.config import CONFIG_DIR

logger = logging.getLogger(__name__)


# ============================================================
#  插件基类
# ============================================================

class BasePlugin(ABC):
    """
    所有插件的基类。
    新插件只需继承此类并实现 required 方法即可。
    """

    # --- 插件元信息（子类需覆盖） ---
    plugin_name: str = ""
    plugin_version: str = "1.0.0"
    plugin_description: str = ""
    plugin_author: str = ""
    plugin_dependencies: List[str] = []

    def __init__(self):
        self._enabled = True
        self._config: dict = {}

    @abstractmethod
    def execute(self, input_data: Any, **kwargs) -> dict:
        """
        插件核心执行逻辑
        Args:
            input_data: 输入数据
            **kwargs: 额外参数
        Returns:
            处理结果字典，必须包含 'success' 字段
        """
        raise NotImplementedError("子类必须实现 execute 方法")

    def initialize(self, config: dict = None):
        """插件初始化（可选覆盖）"""
        if config:
            self._config = config
        logger.info(f"插件 [{self.plugin_name}] v{self.plugin_version} 初始化完成")

    def cleanup(self):
        """插件清理（可选覆盖）"""
        logger.info(f"插件 [{self.plugin_name}] 已清理")

    def get_info(self) -> dict:
        """获取插件信息"""
        return {
            "name": self.plugin_name,
            "version": self.plugin_version,
            "description": self.plugin_description,
            "author": self.plugin_author,
            "enabled": self._enabled,
            "dependencies": self.plugin_dependencies,
            "class": self.__class__.__name__,
        }

    def set_enabled(self, enabled: bool):
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def validate_input(self, input_data: Any) -> Tuple[bool, str]:
        """
        验证输入数据（可选覆盖）
        返回: (是否有效, 错误信息)
        """
        if input_data is None:
            return False, "输入数据为空"
        return True, ""


# ============================================================
#  插件管理器
# ============================================================

class PluginManager:
    """
    插件管理器 - 负责插件的注册、发现、加载和生命周期管理。
    支持自动扫描插件目录和通过配置文件动态加载。
    """

    def __init__(self, plugin_dirs: List[Path] = None):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_dirs = plugin_dirs or []
        self._config: dict = {}

    def discover_plugins(self, directory: Path) -> List[str]:
        """
        在指定目录中自动发现插件
        Args:
            directory: 插件目录路径
        Returns:
            发现的插件模块名称列表
        """
        discovered = []
        if not directory.exists():
            logger.warning(f"插件目录不存在: {directory}")
            return discovered

        for file in directory.glob("*.py"):
            if file.name.startswith('_'):
                continue
            module_name = file.stem
            discovered.append(module_name)
            logger.info(f"发现候选插件模块: {module_name} ({file})")

        return discovered

    def load_plugin(self, module_name: str, directory: Path = None) -> Optional[BasePlugin]:
        """
        加载并实例化单个插件
        Args:
            module_name: 插件模块名称
            directory: 模块所在目录
        Returns:
            插件实例，失败返回 None
        """
        try:
            # 动态导入模块
            if directory:
                sys.path.insert(0, str(directory.parent))

            module = importlib.import_module(module_name)

            # 查找模块中所有 BasePlugin 的子类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and issubclass(obj, BasePlugin)
                        and obj is not BasePlugin):
                    plugin_class = obj
                    break

            if plugin_class is None:
                logger.warning(f"模块 {module_name} 中未找到 BasePlugin 子类")
                return None

            # 实例化插件
            plugin_instance = plugin_class()

            # 应用配置
            plugin_config = self._config.get(plugin_instance.plugin_name, {})
            plugin_instance.initialize(plugin_config)

            self._plugins[plugin_instance.plugin_name] = plugin_instance
            logger.info(f"成功加载插件: {plugin_instance.plugin_name} "
                        f"v{plugin_instance.plugin_version}")

            return plugin_instance

        except Exception as e:
            logger.error(f"加载插件 {module_name} 失败: {str(e)}", exc_info=True)
            return None

    def load_all_from_config(self, config_file: Optional[Path] = None):
        """
        根据配置文件加载所有插件
        Args:
            config_file: 插件配置文件路径（默认使用 config/plugins.json）
        """
        if config_file is None:
            config_file = CONFIG_DIR / "plugins.json"

        if not config_file.exists():
            logger.info(f"插件配置文件不存在，使用默认配置: {config_file}")
            self._create_default_config(config_file)
            return

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logger.error(f"读取插件配置文件失败: {e}")
            return

        self._config = config.get("plugin_settings", {})

        # 加载启用列表中的插件
        for plugin_name in config.get("enabled_plugins", []):
            self.load_plugin(plugin_name)

        # 扫描插件目录
        for plugin_dir in config.get("plugin_dirs", []):
            dir_path = Path(plugin_dir)
            if dir_path.exists():
                discovered = self.discover_plugins(dir_path)
                for module in discovered:
                    if module not in self._plugins:
                        self.load_plugin(module, dir_path)

    def register_plugin(self, plugin: BasePlugin) -> bool:
        """手动注册一个插件实例"""
        if not isinstance(plugin, BasePlugin):
            logger.error(f"注册插件失败：对象不是 BasePlugin 实例")
            return False

        name = plugin.plugin_name
        if not name:
            logger.error("注册插件失败：插件名称不能为空")
            return False

        self._plugins[name] = plugin
        logger.info(f"已注册插件: {name}")
        return True

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """按名称获取插件"""
        return self._plugins.get(name)

    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已加载的插件"""
        return dict(self._plugins)

    def get_enabled_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已启用的插件"""
        return {
            name: plugin
            for name, plugin in self._plugins.items()
            if plugin.is_enabled()
        }

    def unload_plugin(self, name: str) -> bool:
        """卸载指定插件"""
        if name in self._plugins:
            self._plugins[name].cleanup()
            del self._plugins[name]
            logger.info(f"已卸载插件: {name}")
            return True
        return False

    def reload_all_plugins(self):
        """重新加载所有插件"""
        for name in list(self._plugins.keys()):
            self.unload_plugin(name)
        self.load_all_from_config()

    def execute_plugin(self, name: str, input_data: Any, **kwargs) -> dict:
        """
        执行指定插件
        Args:
            name: 插件名称
            input_data: 输入数据
            **kwargs: 额外参数
        Returns:
            执行结果
        """
        plugin = self.get_plugin(name)
        if not plugin:
            return {"success": False, "error": f"插件 '{name}' 未找到"}

        if not plugin.is_enabled():
            return {"success": False, "error": f"插件 '{name}' 未启用"}

        # 输入验证
        valid, error = plugin.validate_input(input_data)
        if not valid:
            return {"success": False, "error": error}

        return plugin.execute(input_data, **kwargs)

    def get_plugins_summary(self) -> List[dict]:
        """获取所有插件的摘要信息"""
        return [
            plugin.get_info()
            for plugin in self._plugins.values()
        ]

    def _create_default_config(self, config_file: Path):
        """创建默认插件配置文件"""
        default_config = {
            "plugin_dirs": [
                str(CONFIG_DIR / "plugins"),
                str(Path.cwd() / "custom_plugins"),
            ],
            "enabled_plugins": [],
            "plugin_settings": {},
            "description": "插件配置文件 - 在此添加需要启用的插件和配置",
        }
        config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        logger.info(f"已创建默认插件配置文件: {config_file}")


# ============================================================
#  全局插件管理器实例
# ============================================================

_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器实例"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def register_core_agents():
    """
    注册核心智能体到调度器。
    在应用启动时调用。
    """
    from app.agent.base_agent import get_orchestrator
    from app.modules.meeting_minutes import MeetingMinutesAgent
    from app.modules.doc_compare import DocCompareAgent
    from app.modules.task_manager import TaskManagerAgent

    orchestrator = get_orchestrator()

    orchestrator.register_agent("meeting_minutes", MeetingMinutesAgent())
    orchestrator.register_agent("doc_compare", DocCompareAgent())
    orchestrator.register_agent("task_management", TaskManagerAgent())

    logger.info("所有核心智能体已注册完成")
