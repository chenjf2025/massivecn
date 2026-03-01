# ============================================================
# 解析器工厂 - 统一管理所有数据源解析器
# ============================================================

from typing import Dict, Optional, List
from loguru import logger

from parsers.base import BaseParser
from parsers.eastmoney import EastMoneyParser
from parsers.tencent import TencentParser
from parsers.xueqiu import XueQiuParser
from parsers.sina import SinaParser


class ParserFactory:
    """解析器工厂 - 注册和管理所有数据源解析器"""
    
    _parsers: Dict[str, BaseParser] = {}
    _enabled: Dict[str, bool] = {}
    
    @classmethod
    def register(cls, name: str, parser: BaseParser, enabled: bool = True) -> None:
        cls._parsers[name] = parser
        cls._enabled[name] = enabled
        logger.info(f"注册解析器: {name} (enabled={enabled})")
    
    @classmethod
    def get(cls, name: str) -> Optional[BaseParser]:
        return cls._parsers.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, BaseParser]:
        return cls._parsers.copy()
    
    @classmethod
    def get_enabled(cls) -> List[BaseParser]:
        return [
            parser for name, parser in cls._parsers.items()
            if cls._enabled.get(name, False)
        ]
    
    @classmethod
    def enable(cls, name: str) -> bool:
        if name in cls._parsers:
            cls._enabled[name] = True
            logger.info(f"启用解析器: {name}")
            return True
        return False
    
    @classmethod
    def disable(cls, name: str) -> bool:
        if name in cls._parsers:
            cls._enabled[name] = False
            logger.info(f"禁用解析器: {name}")
            return True
        return False
    
    @classmethod
    def is_enabled(cls, name: str) -> bool:
        return cls._enabled.get(name, False)
    
    @classmethod
    def initialize(cls) -> None:
        # 注册东方财富 (主源)
        cls.register("eastmoney", EastMoneyParser(), enabled=True)
        
        # 注册腾讯财经 (备源)
        cls.register("tencent", TencentParser(), enabled=True)
        
        # 注册雪球财经
        cls.register("xueqiu", XueQiuParser(), enabled=False)
        
        # 注册新浪财经
        cls.register("sina", SinaParser(), enabled=False)
        
        logger.info("解析器工厂初始化完成")


# 自动初始化
ParserFactory.initialize()
