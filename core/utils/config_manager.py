# 配置管理器
# 路径: core/utils/config_manager.py
# 项目名: Word Frequency Analysis
# 作者: Sherryyue

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """
    配置管理器类，用于读取和管理YAML配置文件
    支持环境变量覆盖和多环境配置
    """
    
    def __init__(self, env: str = "default"):
        """
        初始化配置管理器
        
        Args:
            env: 环境名称 (default, development, production)
        """
        self.env = env
        self._config = {}
        self._load_config()
    
    def _load_config(self):
        """加载配置文件，支持多环境配置合并"""
        try:
            # 获取项目根目录
            current_dir = Path(__file__).parent
            project_root = current_dir.parent.parent
            config_dir = project_root / "config"
            
            # 首先加载默认配置
            default_config_path = config_dir / "default.yaml"
            if default_config_path.exists():
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            
            # 如果不是默认环境，加载对应环境配置并合并
            if self.env != "default":
                env_config_path = config_dir / f"{self.env}.yaml"
                if env_config_path.exists():
                    with open(env_config_path, 'r', encoding='utf-8') as f:
                        env_config = yaml.safe_load(f) or {}
                        self._config = self._merge_configs(self._config, env_config)
            
            # 应用环境变量覆盖
            self._apply_env_overrides()
            
        except Exception as e:
            print(f"警告: 加载配置文件失败: {e}")
            self._config = self._get_default_config()
    
    def _merge_configs(self, base_config: Dict, override_config: Dict) -> Dict:
        """
        深度合并两个配置字典
        
        Args:
            base_config: 基础配置
            override_config: 覆盖配置
        
        Returns:
            合并后的配置字典
        """
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self):
        """应用环境变量覆盖，支持嵌套键名如 DB_HOST, FILE_MAX_SIZE 等"""
        # 简单的环境变量覆盖实现
        # 可以根据需要扩展更复杂的覆盖逻辑
        pass
    
    def _get_default_config(self) -> Dict:
        """获取默认配置（当配置文件加载失败时使用）"""
        return {
            "app": {
                "name": "Word Frequency Analysis",
                "version": "1.0.0"
            },
            "database": {
                "path": "data/databases/",
                "vocabulary_db": "vocabulary.db",
                "analysis_db": "analysis.db"
            },
            "file_processing": {
                "supported_formats": [".txt", ".pdf", ".docx", ".csv"],
                "max_file_size": 50,
                "batch_size": 100
            },
            "analysis": {
                "min_word_length": 1,
                "min_frequency_threshold": 1,
                "language": "en"
            },
            "cli": {
                "page_size": 10,
                "max_display_items": 20,
                "enable_colors": True,
                "enable_progress_bar": True
            }
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值，支持点分隔的键名
        
        Args:
            key_path: 配置键路径，如 'database.path' 或 'cli.page_size'
            default: 默认值
        
        Returns:
            配置值
        """
        try:
            keys = key_path.split('.')
            value = self._config
            
            for key in keys:
                value = value[key]
            
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        获取整个配置段
        
        Args:
            section: 配置段名称
        
        Returns:
            配置段字典
        """
        return self._config.get(section, {})
    
    def update(self, key_path: str, value: Any):
        """
        更新配置值
        
        Args:
            key_path: 配置键路径
            value: 新值
        """
        keys = key_path.split('.')
        config_ref = self._config
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        # 设置最终值
        config_ref[keys[-1]] = value
    
    def get_database_path(self, db_name: str) -> str:
        """
        获取数据库文件的完整路径
        
        Args:
            db_name: 数据库名称 (vocabulary_db, analysis_db)
        
        Returns:
            数据库文件路径
        """
        db_path = self.get("database.path", "data/databases/")
        db_filename = self.get(f"database.{db_name}", f"{db_name}.db")
        
        # 确保路径存在
        Path(db_path).mkdir(parents=True, exist_ok=True)
        
        return os.path.join(db_path, db_filename)
    
    def get_export_path(self, filename: str = "") -> str:
        """
        获取导出文件路径
        
        Args:
            filename: 文件名（可选）
        
        Returns:
            导出路径
        """
        export_dir = self.get("export.output_directory", "data/exports/")
        
        # 确保路径存在
        Path(export_dir).mkdir(parents=True, exist_ok=True)
        
        if filename:
            return os.path.join(export_dir, filename)
        return export_dir
    
    def is_feature_enabled(self, feature_path: str) -> bool:
        """
        检查功能是否启用
        
        Args:
            feature_path: 功能配置路径
        
        Returns:
            功能是否启用
        """
        return bool(self.get(feature_path, False))
    
    def __str__(self) -> str:
        """返回配置的字符串表示"""
        return f"ConfigManager(env={self.env}, config_keys={list(self._config.keys())})"


# 全局配置实例
config = ConfigManager()

def get_config() -> ConfigManager:
    """获取全局配置实例"""
    return config

def reload_config(env: str = "default") -> ConfigManager:
    """重新加载配置"""
    global config
    config = ConfigManager(env)
    return config 