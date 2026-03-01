# ============================================================
# 新浪财经 (Sina) 数据源解析器
# 接口: hq.sinajs.cn
# ============================================================

import re
from typing import Optional
from datetime import datetime

import httpx

from parsers.base import BaseParser
from models import StockQuote
from loguru import logger


class SinaParser(BaseParser):
    """
    新浪财经行情解析器
    
    接口: http://hq.sinajs.cn/list=sh600000
    返回格式: 文本拼接字符串
    
    字段顺序:
    0: 股票名称
    1: 开盘价
    2: 昨收价
    3: 当前价
    4: 最高价
    5: 最低价
    ...
    """
    
    def __init__(self):
        super().__init__(
            name="sina",
            base_url="https://hq.sinajs.cn",
            timeout=2.0
        )
    
    async def fetch(self, symbol: str) -> Optional[str]:
        """获取新浪财经行情数据"""
        symbol = self.normalize_symbol(symbol)
        
        # 新浪代码格式: sh600000 -> "sh600000"
        url = f"{self.base_url}/list={symbol}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://finance.sina.com.cn/"
                }
                response = await client.get(url, headers=headers)
                response.encoding = 'gb2312'  # 新浪返回 GB2312 编码
                response.raise_for_status()
                return response.text
                
        except httpx.TimeoutException:
            logger.warning(f"[Sina] 请求超时: {symbol}")
            return None
        except Exception as e:
            logger.error(f"[Sina] 请求失败: {symbol}, {e}")
            return None
    
    def parse(self, raw_data: str, symbol: str) -> Optional[StockQuote]:
        """解析新浪文本数据"""
        try:
            # 解析响应: var hq_str_sh600000="..."
            match = re.search(r'hq_str_\w+="(.+)"', raw_data)
            if not match:
                logger.warning(f"[Sina] 无数据: {symbol}")
                return None
            
            fields = match.group(1).split(',')
            
            if len(fields) < 32:
                logger.warning(f"[Sina] 数据不完整: {symbol}, 字段数: {len(fields)}")
                return None
            
            # 新浪字段顺序:
            # 0: 股票名称
            # 1: 开盘价
            # 2: 昨收价
            # 3: 当前价
            # 4: 最高价
            # 5: 最低价
            # 6: ...
            # 8: 买一价
            # 9: 买一量
            # 10: 卖一价
            # 11: 卖一量
            # ... 依次类推
            # 28: 主力资金净流入 (估算)
            
            # 价格
            current_price = float(fields[3]) if fields[3] else 0
            open_price = float(fields[1]) if fields[1] else 0
            prev_close = float(fields[2]) if fields[2] else 0
            high_price = float(fields[4]) if fields[4] else 0
            low_price = float(fields[5]) if fields[5] else 0
            
            # 涨跌
            change = current_price - prev_close
            change_pct = (change / prev_close * 100) if prev_close > 0 else 0
            
            # 成交量(手)
            trading_volume = float(fields[8]) if len(fields) > 8 and fields[8] else 0
            # 成交额(元)
            trading_amount = float(fields[9]) if len(fields) > 9 and fields[9] else 0
            
            # 时间戳
            now = datetime.now()
            ts = int(now.timestamp() * 1000)
            
            # 五档买卖
            bid_prices = []
            bid_volumes = []
            ask_prices = []
            ask_volumes = []
            
            # 买一档 (字段 9,10)
            if len(fields) > 10:
                bid_prices.append(float(fields[9]) if fields[9] else 0)
                bid_volumes.append(float(fields[10]) if fields[10] else 0)
            # 买二档 (字段 11,12)
            if len(fields) > 12:
                bid_prices.append(float(fields[11]) if fields[11] else 0)
                bid_volumes.append(float(fields[12]) if fields[12] else 0)
            # 买三档 (字段 13,14)
            if len(fields) > 14:
                bid_prices.append(float(fields[13]) if fields[13] else 0)
                bid_volumes.append(float(fields[14]) if fields[14] else 0)
            # 买四档 (字段 15,16)
            if len(fields) > 16:
                bid_prices.append(float(fields[15]) if fields[15] else 0)
                bid_volumes.append(float(fields[16]) if fields[16] else 0)
            # 买五档 (字段 17,18)
            if len(fields) > 18:
                bid_prices.append(float(fields[17]) if fields[17] else 0)
                bid_volumes.append(float(fields[18]) if fields[18] else 0)
            
            # 卖一档 (字段 19,20)
            if len(fields) > 20:
                ask_prices.append(float(fields[19]) if fields[19] else 0)
                ask_volumes.append(float(fields[20]) if fields[20] else 0)
            # 卖二档 (字段 21,22)
            if len(fields) > 22:
                ask_prices.append(float(fields[21]) if fields[21] else 0)
                ask_volumes.append(float(fields[22]) if fields[22] else 0)
            # 卖三档 (字段 23,24)
            if len(fields) > 24:
                ask_prices.append(float(fields[23]) if fields[23] else 0)
                ask_volumes.append(float(fields[24]) if fields[24] else 0)
            # 卖四档 (字段 25,26)
            if len(fields) > 26:
                ask_prices.append(float(fields[25]) if fields[25] else 0)
                ask_volumes.append(float(fields[26]) if fields[26] else 0)
            # 卖五档 (字段 27,28)
            if len(fields) > 28:
                ask_prices.append(float(fields[27]) if fields[27] else 0)
                ask_volumes.append(float(fields[28]) if fields[28] else 0)
            
            # 主力资金估算 (字段 28 或 37)
            if len(fields) > 37 and fields[37]:
                try:
                    main_net_inflow = float(fields[37])
                except:
                    main_net_inflow = 0
            else:
                main_net_inflow = 0
            
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
                large_net_inflow=0,
                medium_net_inflow=0,
                small_net_inflow=0,
                
                # 额外
                turnover_rate=None,
                amplitude=None,
                
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
            
        except Exception as e:
            logger.error(f"[Sina] 解析失败: {symbol}, {e}")
            return None
