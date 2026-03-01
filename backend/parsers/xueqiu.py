# ============================================================
# 雪球财经 (XueQiu) 数据源解析器
# 接口: stock.xueqiu.com
# ============================================================

import json
import re
from typing import Optional
from datetime import datetime

import httpx

from parsers.base import BaseParser
from models import StockQuote
from loguru import logger


class XueQiuParser(BaseParser):
    """
    雪球财经行情解析器
    
    接口: https://stock.xueqiu.com/v5/stock/quote.json
    需要 Cookie 或 Referer
    """
    
    def __init__(self):
        super().__init__(
            name="xueqiu",
            base_url="https://stock.xueqiu.com",
            timeout=3.0
        )
    
    async def fetch(self, symbol: str) -> Optional[str]:
        """获取雪球行情数据"""
        symbol = self.normalize_symbol(symbol)
        
        # 提取纯数字代码
        code = re.sub(r'[^0-9]', '', symbol)
        # 雪球的代码格式: SH600000 或 SZ000001
        xueqiu_symbol = symbol.upper().replace('SH', 'SH_').replace('SZ', 'SZ_')
        
        url = f"{self.base_url}/v5/stock/quote.json"
        params = {
            "symbol": xueqiu_symbol,
            "_": int(datetime.now().timestamp() * 1000)
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Cookie": "xq_a_token=test",
                    "Referer": "https://xueqiu.com/"
                }
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                return response.text
                
        except httpx.TimeoutException:
            logger.warning(f"[XueQiu] 请求超时: {symbol}")
            return None
        except Exception as e:
            logger.error(f"[XueQiu] 请求失败: {symbol}, {e}")
            return None
    
    def parse(self, raw_data: str, symbol: str) -> Optional[StockQuote]:
        """解析雪球 JSON 数据"""
        try:
            data = json.loads(raw_data)
            
            # 雪球返回的数据在 data 数组中
            items = data.get('data', [])
            if not items:
                logger.warning(f"[XueQiu] 无数据: {symbol}")
                return None
            
            d = items[0]  # 取第一个
            
            # 价格字段
            current_price = float(d.get('current', 0) or 0)
            open_price = float(d.get('open', 0) or 0)
            high_price = float(d.get('high', 0) or 0)
            low_price = float(d.get('low', 0) or 0)
            prev_close = float(d.get('prev_close', 0) or 0)
            
            # 涨跌
            change = current_price - prev_close
            change_pct = float(d.get('change_pct', 0) or 0)
            
            # 成交量和成交额
            trading_volume = float(d.get('volume', 0) or 0)
            trading_amount = float(d.get('amount', 0) or 0)
            
            # 主力资金
            main_net_inflow = float(d.get('net_amount_main', 0) or 0)
            large_net_inflow = float(d.get('net_amount_large', 0) or 0)
            medium_net_inflow = float(d.get('net_amount_medium', 0) or 0)
            small_net_inflow = float(d.get('net_amount_small', 0) or 0)
            
            # 换手率
            turnover_rate = float(d.get('turnover_rate', 0) or 0) / 100
            
            # 振幅
            amplitude = float(d.get('amplitude', 0) or 0)
            
            # 五档数据
            bid_prices = d.get('bid1', [0, 0, 0, 0, 0])
            bid_volumes = d.get('bid1_amount', [0, 0, 0, 0, 0])
            ask_prices = d.get('ask1', [0, 0, 0, 0, 0])
            ask_volumes = d.get('ask1_amount', [0, 0, 0, 0, 0])
            
            # 时间戳
            now = datetime.now()
            ts = int(now.timestamp() * 1000)
            
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
                
                # 五档
                bid_price1=bid_prices[0] if len(bid_prices) > 0 else None,
                bid_volume1=bid_volumes[0] if len(bid_volumes) > 0 else 0,
                bid_price2=bid_prices[1] if len(bid_prices) > 1 else None,
                bid_volume2=bid_volumes[1] if len(bid_volumes) > 1 else 0,
                bid_price3=bid_prices[2] if len(bid_prices) > 2 else None,
                bid_volume3=bid_volumes[2] if len(bid_volumes) > 2 else 0,
                bid_price4=bid_prices[3] if len(bid_prices) > 3 else None,
                bid_volume4=bid_volumes[3] if len(bid_volumes) > 3 else 0,
                bid_price5=bid_prices[4] if len(bid_prices) > 4 else None,
                bid_volume5=bid_volumes[4] if len(bid_volumes) > 4 else 0,
                
                ask_price1=ask_prices[0] if len(ask_prices) > 0 else None,
                ask_volume1=ask_volumes[0] if len(ask_volumes) > 0 else 0,
                ask_price2=ask_prices[1] if len(ask_prices) > 1 else None,
                ask_volume2=ask_volumes[1] if len(ask_volumes) > 1 else 0,
                ask_price3=ask_prices[2] if len(ask_prices) > 2 else None,
                ask_volume3=ask_volumes[2] if len(ask_volumes) > 2 else 0,
                ask_price4=ask_prices[3] if len(ask_prices) > 3 else None,
                ask_volume4=ask_volumes[3] if len(ask_volumes) > 3 else 0,
                ask_price5=ask_prices[4] if len(ask_prices) > 4 else None,
                ask_volume5=ask_volumes[4] if len(ask_volumes) > 4 else 0
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"[XueQiu] JSON 解析失败: {e}")
            return None
        except Exception as e:
            logger.error(f"[XueQiu] 数据转换失败: {e}")
            return None
