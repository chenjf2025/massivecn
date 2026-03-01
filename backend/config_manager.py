# ============================================================
# 配置管理器 - 负责配置的加载、持久化和热更新
# 基于 YAML 文件 + 内存缓存，支持热更新无需重启服务
# ============================================================

import os
import yaml
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# -------------------- Pydantic 配置模型 --------------------

class SourceConfig(BaseModel):
    name: str
    enabled: bool = True
    priority: int = 1
    base_url: str = ""
    timeout: float = 3.0
    retry: int = 2
    parser: str = ""


class SourcesConfig(BaseModel):
    primary: List[SourceConfig] = Field(default_factory=list)
    backup: List[SourceConfig] = Field(default_factory=list)


class RoutingConfig(BaseModel):
    failover: bool = True
    request_timeout: float = 5.0
    max_retries: int = 2
    failover_delay: int = 100


class TDengineConfig(BaseModel):
    host: str = "localhost"
    port: int = 6030
    user: str = "root"
    password: str = "taosdata"
    database: str = "market_data"
    pool_size: int = 5
    timeout: int = 30


class SystemConfig(BaseModel):
    api: Dict[str, Any] = Field(default_factory=dict)
    async_task: Dict[str, Any] = Field(default_factory=dict)


class AppConfig(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    sources: SourcesConfig = Field(default_factory=SourcesConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
    tdengine: TDengineConfig = Field(default_factory=TDengineConfig)
    frontend: Dict[str, Any] = Field(default_factory=dict)
    monitoring: Dict[str, Any] = Field(default_factory=dict)


# -------------------- 配置管理器类 --------------------

class ConfigManager:
    """配置管理器 - 单例模式"""
    
    _instance: Optional['ConfigManager'] = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config_file: str = "config.yaml"):
        self._config_file = Path(config_file)
        self._config: Optional[AppConfig] = None
        self._last_modified: Optional[datetime] = None
        self._change_history: List[Dict[str, Any]] = []
        self._load_config()
    
    def _load_config(self) -> None:
        """从 YAML 文件加载配置"""
        try:
            if not self._config_file.exists():
                logger.warning(f"配置文件不存在，使用默认配置")
                self._config = AppConfig()
                self._save_config()
                return
            
            with open(self._config_file, 'r', encoding='utf-8') as f:
                raw_config = yaml.safe_load(f) or {}
            
            self._config = AppConfig(**raw_config)
            self._last_modified = datetime.now()
            logger.info(f"配置加载成功")
            
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            self._config = AppConfig()
    
    def _save_config(self) -> None:
        """保存配置到 YAML 文件"""
        try:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            config_dict = self._config.model_dump()
            with open(self._config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, allow_unicode=True, default_flow_style=False)
            self._last_modified = datetime.now()
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            raise
    
    def get_config(self) -> AppConfig:
        """获取当前配置"""
        if self._config is None:
            self._load_config()
        return self._config
    
    async def update_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """更新配置 (热更新)"""
        with self._lock:
            self._load_config()
            config_data = self._config.model_dump()
            
            for key, value in config_dict.items():
                if key in config_data and isinstance(value, dict):
                    self._deep_merge(config_data[key], value)
                else:
                    config_data[key] = value
            
            self._config = AppConfig(**config_data)
            self._save_config()
            
            self._change_history.append({
                "timestamp": datetime.now().isoformat(),
                "changes": config_dict
            })
            
            logger.info(f"配置已热更新: {list(config_dict.keys())}")
            return self._config
    
    def _deep_merge(self, base: Dict, update: Dict) -> None:
        """深度合并"""
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._deep_merge(base[k], v)
            else:
                base[k] = v
    
    def get_enabled_sources(self) -> List[SourceConfig]:
        """获取所有已启用的数据源"""
        config = self.get_config()
        primary = [s for s in config.sources.primary if s.enabled]
        backup = [s for s in config.sources.backup if s.enabled]
        primary.sort(key=lambda x: x.priority)
        backup.sort(key=lambda x: x.priority)
        return primary + backup
    
    def get_primary_sources(self) -> List[SourceConfig]:
        """获取已启用的主数据源"""
        config = self.get_config()
        return [s for s in config.sources.primary if s.enabled]
    
    def get_backup_sources(self) -> List[SourceConfig]:
        """获取已启用的备用数据源"""
        config = self.get_config()
        return [s for s in config.sources.backup if s.enabled]
    
    def get_tdengine_config(self) -> TDengineConfig:
        return self.get_config().tdengine
    
    def get_routing_config(self) -> RoutingConfig:
        return self.get_config().routing
    
    def get_change_history(self) -> List[Dict[str, Any]]:
        return self._change_history[-50:]


# 全局配置实例
config_manager = ConfigManager()
