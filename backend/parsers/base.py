# ============================================================
# 数据源解析器基类
# 定义所有解析器的接口规范
# ============================================================

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

from models import StockQuote
from loguru import logger


class BaseParser(ABC):
    """
    数据源解析器基类
    
    所有具体解析器必须继承此类并实现:
    - fetch(): 获取原始数据
    - parse(): 解析原始数据为标准格式
    """
    
    def __init__(self, name: str, base_url: str, timeout: float = 3.0):
        """
        初始化解析器
        
        Args:
            name: 解析器名称 (如 eastmoney, tencent)
            base_url: 数据源基础 URL
            timeout: 请求超时时间(秒)
        """
        self.name = name
        self.base_url = base_url
        self.timeout = timeout
    
    @abstractmethod
    async def fetch(self, symbol: str) -> Optional[str]:
        """
        从数据源获取原始数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            str: 原始响应数据 (JSON/HTML/文本)
            None: 获取失败
        """
        pass
    
    @abstractmethod
    def parse(self, raw_data: str, symbol: str) -> Optional[StockQuote]:
        """
        解析原始数据为标准格式
        
        Args:
            raw_data: 原始响应数据
            symbol: 股票代码
            
        Returns:
            StockQuote: 标准行情数据
            None: 解析失败
        """
        pass
    
    async def get_quote(self, symbol: str) -> Optional[StockQuote]:
        """
        获取并解析行情数据 (组合方法)
        
        Args:
            symbol: 股票代码
            
        Returns:
            StockQuote: 标准行情数据
            None: 获取或解析失败
        """
        start_time = datetime.now()
        
        try:
            # 获取原始数据
            raw_data = await self.fetch(symbol)
            if not raw_data:
                logger.warning(f"[{self.name}] 获取数据失败: {symbol}")
                return None
            
            # 解析数据
            quote = self.parse(raw_data, symbol)
            if not quote:
                logger.warning(f"[{self.name}] 解析数据失败: {symbol}")
                return None
            
            # 记录延迟
            latency = (datetime.now() - start_time).total_seconds() * 1000
            logger.debug(f"[{self.name}] 获取成功: {symbol}, 延迟: {latency:.0f}ms")
            
            return quote
            
        except Exception as e:
            logger.error(f"[{self.name}] 获取行情异常: {symbol}, {e}")
            return None
    
    def normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码
        
        Args:
            symbol: 原始代码 (如 600000, sh600000)
            
        Returns:
            str: 标准格式代码
        """
        symbol = symbol.lower().strip()
        
        # 添加市场前缀
        if not symbol.startswith(('sh', 'sz')):
            # 根据代码判断市场
            if symbol.startswith('6'):
                symbol = 'sh' + symbol
            elif symbol.startswith(('0', '3')):
                symbol = 'sz' + symbol
        
        return symbol
