# TDengine 数据库操作模块 - REST API 方式

import asyncio
import aiohttp
from datetime import datetime
from typing import List, Optional, Dict, Any
from loguru import logger
from config_manager import config_manager
from models import StockQuote, HistoryDataPoint


class TDenginePool:
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = False
        self._config = config_manager.get_tdengine_config()
        self._base_url = None
        self._session = None
    
    async def initialize(self):
        if self._initialized:
            return
        try:
            host = self._config.host
            port = self._config.port
            self._base_url = f"http://{host}:{port}"
            logger.info(f"连接 TDengine REST: {self._base_url}")
            await self._execute_sql("SELECT server_version()")
            await self._setup_database()
            self._session = aiohttp.ClientSession()
            self._initialized = True
            logger.info("TDengine 连接成功")
        except Exception as e:
            logger.error(f"TDengine 连接失败: {e}")
    
    async def _execute_sql(self, sql):
        if not self._session:
            return None
        url = f"{self._base_url}/rest/sql/{self._config.database}"
        try:
            async with self._session.post(url, data=sql.encode('utf-8')) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if result.get('status') == 'success':
                        return result.get('data', [])
        except Exception as e:
            logger.error(f"SQL 执行异常: {e}")
        return None
    
    async def _setup_database(self):
        db_name = self._config.database
        await self._execute_sql(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        sql = f"""
        CREATE STABLE IF NOT EXISTS {db_name}.stock_quotes (
            ts TIMESTAMP, current_price FLOAT, open_price FLOAT, high_price FLOAT,
            low_price FLOAT, close_price FLOAT, prev_close FLOAT, change FLOAT,
            change_pct FLOAT, trading_volume BIGINT, trading_amount BIGINT,
            main_net_inflow BIGINT, large_net_inflow BIGINT, medium_net_inflow BIGINT,
            small_net_inflow BIGINT, turnover_rate FLOAT, amplitude FLOAT,
            bid_price1 FLOAT, bid_volume1 BIGINT, ask_price1 FLOAT, ask_volume1 BIGINT
        ) TAGS (symbol BINARY(20), data_source BINARY(20))
        """
        await self._execute_sql(sql)
        logger.info(f"表创建成功: {db_name}.stock_quotes")
    
    async def close_all(self):
        if self._session:
            await self._session.close()
        self._initialized = False
        logger.info("TDengine 连接已关闭")
    
    async def insert_quote(self, quote):
        return await self.batch_insert([quote]) > 0
    
    async def batch_insert(self, quotes):
        if not quotes or not self._session:
            return 0
        db_name = self._config.database
        try:
            sql_parts = []
            for quote in quotes:
                ts = datetime.fromtimestamp(quote.ts / 1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                sql = f"('{ts}', '{quote.symbol}', '{quote.data_source}', {quote.current_price}, {quote.open_price}, {quote.high_price}, {quote.low_price}, {quote.close_price}, {quote.prev_close}, {quote.change}, {quote.change_pct}, {int(quote.trading_volume)}, {int(quote.trading_amount)}, {int(quote.main_net_inflow)}, {int(quote.large_net_inflow)}, {int(quote.medium_net_inflow)}, {int(quote.small_net_inflow)}, {quote.turnover_rate or 'NULL'}, {quote.amplitude or 'NULL'}, {quote.bid_price1 or 'NULL'}, {int(quote.bid_volume1 or 0)}, {quote.ask_price1 or 'NULL'}, {int(quote.ask_volume1 or 0)})"
                sql_parts.append(sql)
            full_sql = f"INSERT INTO {db_name}.stock_quotes (ts, symbol, data_source, current_price, open_price, high_price, low_price, close_price, prev_close, change, change_pct, trading_volume, trading_amount, main_net_inflow, large_net_inflow, medium_net_inflow, small_net_inflow, turnover_rate, amplitude, bid_price1, bid_volume1, ask_price1, ask_volume1) VALUES {','.join(sql_parts)}"
            result = await self._execute_sql(full_sql)
            if result is not None:
                return len(quotes)
        except Exception as e:
            logger.error(f"批量插入失败: {e}")
        return 0
    
    async def query_history(self, symbol, start_time=None, end_time=None, interval="1m", aggregation=None):
        db_name = self._config.database
        try:
            where_clauses = [f"symbol = '{symbol}'"]
            if start_time:
                where_clauses.append(f"ts >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'")
            if end_time:
                where_clauses.append(f"ts <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'")
            where_sql = " AND ".join(where_clauses)
            if aggregation:
                sql = f"SELECT _wstart as ts, first(open_price), max(high_price), min(low_price), last(close_price), sum(trading_volume), sum(trading_amount), avg(main_net_inflow) FROM {db_name}.stock_quotes WHERE {where_sql} INTERVAL ({aggregation}m) ORDER BY ts"
            else:
                sql = f"SELECT ts, open_price, high_price, low_price, close_price, trading_volume, trading_amount, main_net_inflow FROM {db_name}.stock_quotes WHERE {where_sql} ORDER BY ts"
            result = await self._execute_sql(sql)
            if not result:
                return []
            data = []
            for row in result:
                ts_val = row[0]
                ts_dt = datetime.strptime(ts_val, '%Y-%m-%d %H:%M:%S.%f') if isinstance(ts_val, str) else ts_val
                volume = float(row[5])
                amount = float(row[6])
                vwap = amount / volume if volume > 0 else 0
                data.append(HistoryDataPoint(
                    ts=int(ts_dt.timestamp() * 1000), timestamp=ts_dt.isoformat(),
                    open=float(row[1]), high=float(row[2]), low=float(row[3]), close=float(row[4]),
                    volume=volume, amount=amount, vwap=round(vwap, 2), main_net_inflow=float(row[7]) if row[7] else 0
                ))
            return data
        except Exception as e:
            logger.error(f"历史查询失败: {e}")
            return []
    
    async def get_today_stats(self):
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            sql = f"SELECT COUNT(*) FROM {self._config.database}.stock_quotes WHERE ts >= '{today}'"
            result = await self._execute_sql(sql)
            count = result[0][0] if result and result[0] else 0
            return {"today_ingested": count, "avg_latency_ms": 0}
        except:
            return {"today_ingested": 0, "avg_latency_ms": 0}


tdengine_pool = TDenginePool()
