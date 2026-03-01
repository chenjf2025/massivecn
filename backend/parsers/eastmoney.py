# ============================================================
# 东方财富 (EastMoney) 数据源解析器
# 接口: push2.eastmoney.com
# ============================================================

import json
import re
from typing import Optional
from datetime import datetime

import httpx

from parsers.base import BaseParser
from models import StockQuote
from loguru import logger


class EastMoneyParser(BaseParser):
    """
    东方财富行情解析器
    
    接口说明:
    - 推送接口: /api/qt/stock/get
    - 返回字段: 包含最新价、涨跌、成交量、五档买卖等
    
    数据格式: JSON
    """
    
    def __init__(self):
        super().__init__(
            name="eastmoney",
            base_url="https://push2.eastmoney.com",
            timeout=3.0
        )
    
    async def fetch(self, symbol: str) -> Optional[str]:
        """
        获取东方财富行情数据
        
        Args:
            symbol: 股票代码 (支持 sh600000, 600000 格式)
            
        Returns:
            str: JSON 响应
        """
        # 标准化代码
        symbol = self.normalize_symbol(symbol)
        
        # 提取纯数字代码
        code = re.sub(r'[^0-9]', '', symbol)
        market = '1' if symbol.startswith('sh') else '0'
        
        # 构建请求 URL
        url = f"{self.base_url}/api/qt/stock/get"
        params = {
            "ut": "fa5fd1943c7b386f172d6893dbfba10b",  # 固定 ut
            "invt": "2",
            "fltt": "2",
            "fields": "f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f59,f60,f116,f117,f162,f167,f168,f169,f170,f171,f173,f177",
            "secid": f"{market}.{code}",
            "_": int(datetime.now().timestamp() * 1000)
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.text
                
        except httpx.TimeoutException:
            logger.warning(f"[EastMoney] 请求超时: {symbol}")
            return None
        except Exception as e:
            logger.error(f"[EastMoney] 请求失败: {symbol}, {e}")
            return None
    
    def parse(self, raw_data: str, symbol: str) -> Optional[StockQuote]:
        """
        解析东方财富 JSON 数据
        
        Args:
            raw_data: JSON 响应
            symbol: 股票代码
            
        Returns:
            StockQuote: 标准行情数据
        """
        try:
            data = json.loads(raw_data)
            
            # 检查响应状态
            if data.get("data") is None:
                logger.warning(f"[EastMoney] 无数据: {symbol}")
                return None
            
            d = data["data"]
            
            # 获取时间戳 (毫秒)
            now = datetime.now()
            ts = int(now.timestamp() * 1000)
            
            # 价格字段
            current_price = float(d.get("f43", 0)) / 100  # 最新价 (分 -> 元)
            open_price = float(d.get("f46", 0)) / 100    # 开盘价
            high_price = float(d.get("f44", 0)) / 100     # 最高价
            low_price = float(d.get("f45", 0)) / 100     # 最低价
            prev_close = float(d.get("f58", 0)) / 100    # 昨收价
            
            # 涨跌
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            # 成交量 (手 -> 股, 注意单位)
            trading_volume = float(d.get("f50", 0))       # 成交量(手)
            trading_amount = float(d.get("f51", 0)) / 1000000  # 成交额(元 -> 万元, 再转换)
            
            # 主力资金流向 (单位: 元)
            main_net_inflow = float(d.get("f173", 0) or 0)
            large_net_inflow = float(d.get("f170", 0) or 0)
            medium_net_inflow = float(d.get("f171", 0) or 0)
            small_net_inflow = float(d.get("f173", 0) or 0) - main_net_inflow
            
            # 换手率
            turnover_rate = float(d.get("f168", 0)) / 100 if d.get("f168") else None
            
            # 振幅
            amplitude = float(d.get("f167", 0)) / 100 if d.get("f167") else None
            
            # 构建标准行情对象
            return StockQuote(
                ts=ts,
                timestamp=now.isoformat(),
                symbol=symbol,
                data_source=self.name,
                
                # 价格
                current_price=round(current_price, 2),
                open_price=round(open_price, 2),
                high_price=round(high_price, 2),
                low_price=round(low_price, 2),
                close_price=round(current_price, 2),
                prev_close=round(prev_close, 2),
                
                # 涨跌
                change=round(change, 2),
                change_pct=round(change_pct, 2),
                
                # 量额
                trading_volume=trading_volume,
                trading_amount=trading_amount,
                
                # 资金
                main_net_inflow=main_net_inflow,
                large_net_inflow=large_net_inflow,
                medium_net_inflow=medium_net_inflow,
                small_net_inflow=small_net_inflow,
                
                # 额外
                turnover_rate=turnover_rate,
                amplitude=amplitude,
                
                # 五档 (东方财富未提供详细五档, 使用主要档位)
                bid_price1=current_price - 0.01 if current_price > 0 else None,
                bid_volume1=0,
                ask_price1=current_price + 0.01 if current_price > 0 else None,
                ask_volume1=0
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"[EastMoney] JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[EastMoney] 数据转换失败: {e}")
            return None
