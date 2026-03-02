# ============================================================
# 腾讯财经 (Tencent) 数据源解析器
# 接口: qt.gtimg.cn
# ============================================================

import re
from typing import Optional
from datetime import datetime

import httpx

from parsers.base import BaseParser
from models import StockQuote
from loguru import logger


class TencentParser(BaseParser):
    """腾讯财经行情解析器"""
    
    def __init__(self):
        super().__init__(
            name="tencent",
            base_url="https://qt.gtimg.cn",
            timeout=2.0
        )
    
    async def fetch(self, symbol: str) -> Optional[str]:
        """获取腾讯财经行情数据"""
        symbol = self.normalize_symbol(symbol)
        url = f"{self.base_url}/q={symbol}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://finance.qq.com/"
                }
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except httpx.TimeoutException:
            logger.warning(f"[Tencent] 请求超时: {symbol}")
            return None
        except Exception as e:
            logger.error(f"[Tencent] 请求失败: {symbol}, {e}")
            return None
    
    def parse(self, raw_data: str, symbol: str) -> Optional[StockQuote]:
        """解析腾讯文本数据"""
        try:
            match = re.search(r'v_\w+="(.+)"', raw_data)
            if not match:
                logger.warning(f"[Tencent] 无数据: {symbol}")
                return None
            
            fields = match.group(1).split('~')
            
            if len(fields) < 35:
                logger.warning(f"[Tencent] 数据不完整: {symbol}")
                return None
            
            # 股票名称 (字段1)
            stock_name = fields[1] if fields[1] else ""
            
            # 价格字段
            current_price = float(fields[3]) if fields[3] else 0
            prev_close = float(fields[4]) if fields[4] else 0
            open_price = float(fields[5]) if fields[5] else 0
            high_price = float(fields[33]) if fields[33] else current_price
            low_price = float(fields[34]) if fields[34] else current_price
            
            # 成交量和成交额
            trading_volume = float(fields[6]) if fields[6] else 0
            trading_amount = float(fields[7]) if fields[7] else 0
            
            # 涨跌
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            # 时间戳
            now = datetime.now()
            ts = int(now.timestamp() * 1000)
            
            # 买卖档位
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []
            
            for i in [9, 11, 13, 15, 17]:
                bid_prices.append(float(fields[i]) if i < len(fields) and fields[i] else 0)
            for i in [8, 10, 12, 14, 16]:
                bid_volumes.append(float(fields[i]) if i < len(fields) and fields[i] else 0)
            
            for i in [19, 21, 23, 25, 27]:
                ask_prices.append(float(fields[i]) if i < len(fields) and fields[i] else 0)
            for i in [18, 20, 22, 24, 26]:
                ask_volumes.append(float(fields[i]) if i < len(fields) and fields[i] else 0)
            
            # 主力资金
            main_net_inflow = float(fields[28]) if len(fields) > 28 and fields[28] else 0
            large_net_inflow = float(fields[29]) if len(fields) > 29 and fields[29] else 0
            medium_net_inflow = float(fields[30]) if len(fields) > 30 and fields[30] else 0
            small_net_inflow = float(fields[31]) if len(fields) > 31 and fields[31] else 0
            
            # 换手率和振幅
            turnover_rate = float(fields[38]) / 100 if len(fields) > 38 and fields[38] else None
            amplitude = float(fields[43]) if len(fields) > 43 and fields[43] else None
            
            return StockQuote(
                ts=ts, 
                timestamp=now.isoformat(), 
                symbol=symbol, 
                stock_name=stock_name,
                data_source=self.name,
                current_price=round(current_price, 2), 
                open_price=round(open_price, 2),
                high_price=round(high_price, 2), 
                low_price=round(low_price, 2),
                close_price=round(current_price, 2), 
                prev_close=round(prev_close, 2),
                change=round(change, 2), 
                change_pct=round(change_pct, 2),
                trading_volume=trading_volume, 
                trading_amount=trading_amount,
                main_net_inflow=main_net_inflow, 
                large_net_inflow=large_net_inflow,
                medium_net_inflow=medium_net_inflow, 
                small_net_inflow=small_net_inflow,
                turnover_rate=turnover_rate, 
                amplitude=amplitude,
                bid_price1=bid_prices[0], 
                bid_volume1=bid_volumes[0],
                bid_price2=bid_prices[1], 
                bid_volume2=bid_volumes[1],
                bid_price3=bid_prices[2], 
                bid_volume3=bid_volumes[2],
                bid_price4=bid_prices[3], 
                bid_volume4=bid_volumes[3],
                bid_price5=bid_prices[4], 
                bid_volume5=bid_volumes[4],
                ask_price1=ask_prices[0], 
                ask_volume1=ask_volumes[0],
                ask_price2=ask_prices[1], 
                ask_volume2=ask_volumes[1],
                ask_price3=ask_prices[2], 
                ask_volume3=ask_volumes[2],
                ask_price4=ask_prices[3], 
                ask_volume4=ask_volumes[3],
                ask_price5=ask_prices[4], 
                ask_volume5=ask_volumes[4]
            )
        except Exception as e:
            logger.error(f"[Tencent] 解析失败: {symbol}, {e}")
            return None
