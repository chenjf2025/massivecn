# ============================================================
# 历史K线数据获取模块
# 使用新浪财经API获取历史K线数据
# ============================================================

import json
import re
from typing import Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

import httpx
from loguru import logger


@dataclass
class KlineData:
    """K线数据点"""
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float


class KlineFetcher:
    """历史K线数据获取器 - 使用新浪财经API"""
    
    # Sina K-line API
    # scale: 5=5分钟, 15=15分钟, 30=30分钟, 60=60分钟, 240=日线
    BASE_URL = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    
    SCALE_MAP = {
        "1min": 5,
        "5min": 5,
        "15min": 15,
        "30min": 30,
        "60min": 60,
        "1day": 240,
    }
    
    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
    
    def normalize_symbol(self, symbol: str) -> str:
        """标准化股票代码为新浪格式"""
        symbol = symbol.lower().strip()
        if not symbol.startswith(('sh', 'sz')):
            code = re.sub(r'[^0-9]', '', symbol)
            if code.startswith('6'):
                symbol = f"sh{code}"
            else:
                symbol = f"sz{code}"
        return symbol
    
    async def fetch_kline(
        self, 
        symbol: str, 
        interval: str = "1day", 
        days: int = 30
    ) -> List[KlineData]:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码 (如 sh600000, sz000001)
            interval: 周期 (1min, 5min, 15min, 30min, 60min, 1day)
            days: 获取天数
        
        Returns:
            K线数据列表
        """
        symbol = self.normalize_symbol(symbol)
        
        scale = self.SCALE_MAP.get(interval, 240)
        
        params = {
            "symbol": symbol,
            "scale": scale,
            "ma": "no"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://finance.sina.com.cn"
                }
                response = await client.get(self.BASE_URL, params=params, headers=headers)
                response.raise_for_status()
                return self._parse_response(response.text, symbol)
        except httpx.TimeoutException:
            logger.warning(f"[KlineFetcher] 请求超时: {symbol}")
            return []
        except Exception as e:
            logger.error(f"[KlineFetcher] 请求失败: {symbol}, {e}")
            return []
    
    def _parse_response(self, raw_data: str, symbol: str) -> List[KlineData]:
        """解析K线数据响应"""
        try:
            if not raw_data or raw_data == 'null':
                logger.warning(f"[KlineFetcher] 无数据: {symbol}")
                return []
            
            data = json.loads(raw_data)
            
            if not isinstance(data, list) or len(data) == 0:
                logger.warning(f"[KlineFetcher] 数据为空: {symbol}")
                return []
            
            result = []
            for item in data:
                try:
                    dt = datetime.strptime(item['day'], "%Y-%m-%d")
                except:
                    continue
                
                kline_data = KlineData(
                    timestamp=dt.isoformat(),
                    open=float(item['open']),
                    high=float(item['high']),
                    low=float(item['low']),
                    close=float(item['close']),
                    volume=float(item['volume']),
                    amount=0  # Sina API 不提供成交额
                )
                result.append(kline_data)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"[KlineFetcher] JSON解析失败: {e}, raw: {raw_data[:200]}")
            return []
        except Exception as e:
            logger.error(f"[KlineFetcher] 数据解析失败: {e}")
            return []


# 单例
kline_fetcher = KlineFetcher()
